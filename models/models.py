from typing import Optional
from pydantic import BaseModel
from enum import Enum

class MessageType(str, Enum):
    USER = "user"
    BOT = "bot"

class ChatMessage(BaseModel):
    content: str
    type: MessageType
    timestamp: str
    attachments: Optional[list[str]] = None

class IAMPolicyAnalysis(BaseModel):
    issues: list[str]
    recommendations: list[str]
    severity: str  # low, medium, high