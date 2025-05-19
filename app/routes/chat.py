from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

class ChatMessage(BaseModel):
    content: str
    role: str  # "user" or "assistant"

class ChatRequest(BaseModel):
    message: str
    conversation: List[ChatMessage] = []

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = await chat_service.process_message(
            user_input=request.message,
            conversation=request.conversation
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))