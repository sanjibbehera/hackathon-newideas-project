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

app = FastAPI()

# Configure static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Allowed file types
ALLOWED_EXTENSIONS = {'.doc', '.docx', '.pdf', '.png', '.jpg', '.jpeg', '.txt'}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(request: Request, message: str):
    # Process user message and get bot response
    bot_response = process_message(message)
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