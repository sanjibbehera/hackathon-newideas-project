from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import os
from typing import List
from datetime import datetime
from models.models import ChatMessage
from app.chat_handler import process_message
from app.iam_analyzer import analyze_iam_policy
from ollama import Client
import re
from enum import Enum
from typing import Optional, Set
from .routes import aws_errors
from .services.approved_aws_services import is_service_approved, APPROVED_SERVICES
from .services.chat_service import ChatService

app = FastAPI()
app.include_router(aws_errors.router)

class ConversationState(str, Enum):
    NORMAL = "normal"
    AWS_HELP = "aws_help"
    SERVICE_SPECIFIC = "service_specific"
    INITIAL_GREETING = "initial_greeting"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APPROVAL_LINK = "https://your-company.com/aws-service-approval"

# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def init_rag():
    try:
        from app.services.aws_error_service import AWSErrorService
        AWSErrorService()
        print("✅ RAG database initialized successfully")
    except Exception as e:
        print(f"⚠️ RAG initialization failed: {e}")

APPROVED_SERVICES = APPROVED_SERVICES

# Initialize Ollama client
ollama_client = Client(host='http://localhost:11434')

# Allowed file types
ALLOWED_EXTENSIONS = {'.doc', '.docx', '.pdf', '.png', '.jpg', '.jpeg', '.txt'}

# List of approved services (could also load from a file)
APPROVAL_LINK = "https://your-company.com/aws-service-approval"

# Add this helper function
def is_iam_related(message: str) -> bool:
    """Check if message is AWS IAM related"""
    iam_keywords = [
        'iam', 'permission', 'policy', 'role', 'access', 
        'credentials', 'authentication', 'authorization'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in iam_keywords)

def contains_unapproved_service(message: str) -> Optional[str]:
    """
    Check if message mentions unapproved AWS services by comparing against
    the approved services list.
    Returns the first unapproved service found, or None if all are approved.
    """

    # First check for exact matches (case insensitive)
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9-]*\b', message)
    for word in words:
        if len(word) > 2:  # Ignore short words
            if word.upper() in [s.upper() for s in APPROVED_SERVICES.keys()]:
                return None
            if word.upper() in ["AWS", "AMAZON"]:
                continue
            # Check for service patterns like "AWS Redshift"
            if (f"aws {word}".upper() in [f"aws {s}".upper() for s in APPROVED_SERVICES.keys()] or
                f"amazon {word}".upper() in [f"amazon {s}".upper() for s in APPROVED_SERVICES.keys()]):
                return None
            
    # Then do the more complex pattern matching
    aws_service_pattern = r'\b(?:Amazon\s+|AWS\s+)?([A-Z][A-Za-z0-9-]+)\b'
    matches = re.finditer(aws_service_pattern, message, re.IGNORECASE)
    
    for match in matches:
        service = match.group(1)  # Get just the service name part
        if not is_service_approved(service):
            return f"AWS {service}" if service.upper() != service else service
    
    # Common false positives to exclude
    false_positives = {
        'amazon', 'aws', 'cloud', 'web', 'api', 'http', 'https', 
        'server', 'service', 'account', 'user', 'access'
    }
    
    # Find all potential AWS service mentions in the message
    potential_services = re.finditer(aws_service_pattern, message, re.IGNORECASE | re.VERBOSE)
    
    for match in potential_services:  # Changed from 'matches' to 'potential_services'
        service = match.group()
        normalized = re.sub(r'^(Amazon|AWS)\s+', '', service, flags=re.IGNORECASE)
        normalized = normalized.strip().lower()
        
        # Skip false positives
        if normalized in false_positives:
            continue
            
        # Check for AWS prefix pattern even if not matched
        if not re.match(r'^(Amazon|AWS)\s+', service, re.IGNORECASE):
            # For non-prefixed names, only check if it's a known acronym
            if len(normalized) > 5 and normalized not in [s.lower() for s in APPROVED_SERVICES.keys()]:
                continue
                
        # Check all possible variations against approved services
        normalized_variations = {
            normalized,
            normalized.replace(' ', ''),
            normalized.replace('-', ''),
            normalized.replace(' ', '').replace('-', '')
        }
        
        # If none of the variations match approved services
        if not any(is_service_approved(variation) for variation in normalized_variations):
            return service
            
    return None

def get_ollama_response(message: str) -> str:
    """Get response from Ollama with IAM context"""
    try:
        response = ollama_client.chat(
            model='aws-iam-assistant',
            messages=[{'role': 'user', 'content': message}],
            options={'temperature': 0.3}  # More deterministic responses
        )
        return response['message']['content']
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return "I'm having trouble accessing my AWS IAM knowledge. Please try again later."

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Chatbot is ready"}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.json()
        message = body.get('message', '')
        current_state = body.get('current_state', ConversationState.NORMAL)
        current_service = body.get('current_service', None)
        is_first_interaction = body.get('is_first_interaction', True)  # Get the flag

        if not message:
            return JSONResponse(
                content={"response": "Please provide a message"},
                status_code=400
            )

        # Initialize chat service
        chat_service = ChatService()
        
        # Process the message
        result = await chat_service.process_message(
            user_input=message,
            conversation_state=current_state,
            current_service=current_service,
            is_first_interaction=is_first_interaction  # Pass to service
        )

        response = {
            "response": result["response"],
            "timestamp": datetime.now().isoformat(),
            "new_state": result.get("new_state", current_state),
            "service": result.get("service", current_service),
            "response_type": result.get("response_type", "normal"),
            "approval_link": APPROVAL_LINK if result.get("response_type") == "approved_services" else None
        }

        if "services" in result:
            response["services"] = result["services"]

        return response

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return JSONResponse(
            content={"response": "An error occurred while processing your request"},
            status_code=500
        )

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Save the file temporarily
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{datetime.now().timestamp()}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Analyze IAM policy if it's a text-based file
    if file_ext in {'.txt', '.doc', '.docx', '.pdf'}:
        analysis_result = analyze_iam_policy(file_path)
        return {"filename": file.filename, "analysis": analysis_result}
    
    return {"filename": file.filename, "message": "File uploaded successfully"}

@app.get("/api/approved-services")
async def get_approved_services():
    from .services.approved_aws_services import get_approved_services_list
    return {"services": get_approved_services_list()}