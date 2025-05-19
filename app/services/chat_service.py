from typing import Optional, List
from ollama import AsyncClient
from app.services.aws_error_service import AWSErrorService
import re

class ChatService:
    APPROVED_SERVICES = {
        "IAM": "Identity and Access Management",
        "EC2": "Elastic Compute Cloud",
        "S3": "Simple Storage Service",
        "Lambda": "AWS Lambda",
        "RDS": "Relational Database Service",
        "Aurora": "Aurora Database",
        "EKS": "Elastic Kubernetes Service",
        "DynamoDB": "DynamoDB"
    }

    def __init__(self):
        self.ollama = AsyncClient()
        self.rag = AWSErrorService()

    async def process_message(self, user_input: str, conversation: List[dict]) -> str:
        # Check conversation history for existing service context
        current_service = self._get_context_service(conversation)
        
        if self._is_greeting(user_input):
            return self._get_greeting_response(current_service)
            
        # Detect service from input if not already in context
        if not current_service:
            detected_service = self._detect_service(user_input)
            if detected_service:
                if detected_service in self.APPROVED_SERVICES:
                    return await self._handle_service_query(detected_service, user_input)
                else:
                    return self._get_unapproved_service_response(detected_service)
            else:
                return self._get_service_prompt()
        
        # Handle approved service query
        return await self._handle_service_query(current_service, user_input)

    def _get_context_service(self, conversation: List[dict]) -> Optional[str]:
        """Check if service was already established in conversation"""
        for msg in reversed(conversation):
            if msg['role'] == 'assistant' and 'specializing in AWS' in msg['content']:
                match = re.search(r'AWS (\w+)', msg['content'])
                if match:
                    return match.group(1)
        return None

    def _is_greeting(self, text: str) -> bool:
        greetings = ["hi", "hello", "hey", "greetings"]
        return any(greet in text.lower() for greet in greetings)

    def _get_greeting_response(self, current_service: Optional[str]) -> str:
        if current_service:
            return f"Hello again! You're currently discussing {current_service} issues. What's your question?"
        return (
            "Hello! I'm your AWS support assistant specializing in these services:\n"
            + "\n".join([f"- {k} ({v})" for k, v in self.APPROVED_SERVICES.items()]) + 
            "\n\nWhich service are you having trouble with?"
        )

    def _detect_service(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for service in self.APPROVED_SERVICES:
            if service.lower() in text_lower:
                return service
        return None

    def _get_service_prompt(self) -> str:
        return (
            "To best assist you, please specify which AWS service you need help with.\n"
            "Examples:\n"
            "\"IAM: I'm getting AccessDenied errors\"\n"
            "\"EC2: Can't launch instances\"\n\n"
            f"I specialize in: {', '.join(self.APPROVED_SERVICES)}"
        )

    def _get_unapproved_service_response(self, service: str) -> str:
        return (
            f"I specialize only in these AWS services: {', '.join(self.APPROVED_SERVICES)}\n"
            f"I can't assist with {service} issues. Would you like help with one of "
            "the approved services instead?"
        )

    async def _handle_service_query(self, service: str, query: str) -> str:
        # Get RAG context
        results = self.rag.search_errors(query, service)
        context = self._format_rag_results(results)
        
        # Generate LLM response
        response = await self.ollama.chat(
            model='aws-expert',
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an AWS {service} expert. "
                        "Provide concise, technical answers with code examples when needed. "
                        f"Current service context: {service}"
                    )
                },
                {"role": "user", "content": query}
            ],
            options={'temperature': 0.3}
        )
        return response['message']['content']