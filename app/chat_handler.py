import ollama
from typing import Optional
from models.models import ChatMessage, MessageType
from datetime import datetime

def is_iam_related(question: str) -> bool:
    """Check if question is IAM-related"""
    iam_keywords = {
        'iam', 'policy', 'role', 'permission', 
        'aws security', 'principal', 'resource',
        'action', 'effect', 'trust policy', 'security'
    }
    return any(keyword in question.lower() for keyword in iam_keywords)

def get_llm_response(question: str) -> Optional[str]:
    if not is_iam_related(question):
        return ("I'm sorry, I can only assist with AWS IAM questions. "
                "Would you like help with IAM?")
    
    response = ollama.chat(
        model='iam-expert',
        messages=[{'role': 'user', 'content': question}]
    )
    return response['message']['content']



def process_message(user_message: str) -> str:
    """
    Process user message and return appropriate bot response
    """
    # Simple keyword-based responses (you can replace this with LLM later)
    user_message_lower = user_message.lower()
    
    if any(word in user_message_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm your AWS IAM assistant. How can I help you with your IAM policies or roles today?"
    
    elif "permission" in user_message_lower:
        return "I can help analyze permissions. Please describe the specific permissions you need or upload your IAM policy document."
    
    elif "error" in user_message_lower or "issue" in user_message_lower:
        return "Let's troubleshoot your IAM issue. Can you describe the error you're seeing or upload the policy that's causing problems?"
    
    elif "create role" in user_message_lower:
        return "To create an IAM role, I'll need to know: 1) Which AWS service will use this role, 2) What permissions it needs, and 3) Any trust relationships. Would you like to proceed step by step?"
    
    elif "policy" in user_message_lower:
        return "I can help analyze or create IAM policies. You can describe your requirements or upload an existing policy document for review."
    
    else:
        return "I'm here to help with AWS IAM. You can ask me about roles, policies, permissions, or upload documents for analysis. Could you clarify your question?"
        # return get_llm_response(user_message) or "I couldn't process your request. Please try again."