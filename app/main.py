from fastapi import FastAPI, Request, UploadFile, File, HTTPException
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
from typing import Optional, Set

app = FastAPI()

# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def load_approved_services(file_path: str = "db/approved_aws_services.txt") -> Set[str]:
    """Load approved AWS services from file and return all valid service names"""
    approved_services = set()
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Extract all service name variants (split by semicolon)
                variants = [v.strip() for v in line.split(';') if v.strip()]
                approved_services.update(variants)
                
    except FileNotFoundError:
        print(f"Warning: Approved services file {file_path} not found. Using default set.")
        approved_services = {"ec2", "s3", "lambda", "iam"}  # Fallback
    
    return approved_services

# Initialize Ollama client
ollama_client = Client(host='http://localhost:11434')

# Allowed file types
ALLOWED_EXTENSIONS = {'.doc', '.docx', '.pdf', '.png', '.jpg', '.jpeg', '.txt'}

# List of approved services (could also load from a file)
APPROVED_SERVICES = load_approved_services()
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
    the loaded APPROVED_SERVICES set.
    Returns the first unapproved service found, or None if all are approved.
    """
    # Enhanced AWS service pattern
    aws_service_pattern = r'''
        \b(?:Amazon\s+|AWS\s+)?  # Optional prefix
        (?:                       # Service names:
            [A-Za-z][\w-]*        # Start with letter
            (?:\s+[A-Za-z][\w-]*)* # Additional words
            |                     # OR
            [A-Z]{2,}             # All-caps acronyms
        )\b
    '''
    
    # Common false positives to exclude
    false_positives = {
        'amazon', 'aws', 'cloud', 'web', 'api', 'http', 'https', 
        'server', 'service', 'account', 'user', 'access'
    }
    
    # Get lowercase versions of all approved services for comparison
    approved_lower = {s.lower() for s in APPROVED_SERVICES}
    
    matches = re.finditer(aws_service_pattern, message, re.IGNORECASE | re.VERBOSE)
    
    for match in matches:
        service = match.group()
        normalized = re.sub(r'^(Amazon|AWS)\s+', '', service, flags=re.IGNORECASE)
        normalized = normalized.strip().lower()
        
        # Skip false positives
        if normalized in false_positives:
            continue
            
        # Check for AWS prefix pattern even if not matched
        if not re.match(r'^(Amazon|AWS)\s+', service, re.IGNORECASE):
            # For non-prefixed names, only check if it's a known acronym
            if len(normalized) > 5 and normalized not in approved_lower:
                continue
                
        # Check all possible variations against approved services
        normalized_variations = {
            normalized,
            normalized.replace(' ', ''),
            normalized.replace('-', ''),
            normalized.replace(' ', '').replace('-', '')
        }
        
        # If none of the variations match approved services
        if not any(variation in approved_lower for variation in normalized_variations):
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
async def chat_endpoint(request: Request, message: str):
    # Check for unapproved services first
    unapproved_service = contains_unapproved_service(message)
    if unapproved_service:
        return {
            "response": (
                f"The AWS service '{unapproved_service}' is not currently approved for use. "
                f"Please request approval by visiting {APPROVAL_LINK} "
                "before using this service."
            ),
            "timestamp": datetime.now().isoformat()
        }
    
    # Check if this is an IAM-related question
    if is_iam_related(message):
        # Get technical response from Ollama
        bot_response = get_ollama_response(message)
    else:
        # Handle non-IAM questions (pleasantries, etc.)
        if any(greeting in message.lower() for greeting in ['hi', 'hello', 'hey']):
            bot_response = "Hello! I'm your AWS IAM assistant. How can I help you with IAM policies, roles, or permissions today?"
        elif 'thank' in message.lower():
            bot_response = "You're welcome! Is there anything else you'd like to know about AWS IAM?"
        else:
            bot_response = "I specialize in AWS IAM questions. Could you tell me more about your IAM-related needs?"
    
    return {
        "response": bot_response,
        "timestamp": datetime.now().isoformat()
    }

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