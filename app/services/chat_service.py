from typing import Optional, List
from ollama import AsyncClient
from app.services.aws_error_service import AWSErrorService
import re
from enum import Enum
from app.services.approved_aws_services import APPROVED_SERVICES, is_service_approved, get_approved_services_list

class ConversationState(str, Enum):
    NORMAL = "normal"
    AWS_HELP = "aws_help"
    SERVICE_SPECIFIC = "service_specific"
    INITIAL_GREETING = "initial_greeting"

class ChatService:    

    def __init__(self):
        self.ollama = AsyncClient()
        self.rag = AWSErrorService()
        self.approved_services = APPROVED_SERVICES

    async def process_message(self, user_input: str, conversation_state: str, current_service: str = None, is_first_interaction: bool = True) -> dict:     
        # Normalize input
        user_input = user_input.strip().lower()

        # Check for greetings
        if self._is_greeting(user_input):
            return {
                "response": "Hello! How can I assist you with AWS services today?" if is_first_interaction 
                       else "How can I help you with AWS services?",
                "new_state": ConversationState.NORMAL,
                "response_type": "normal"
            }
        
        # Check for AWS service mentions
        detected_service = self._detect_service(user_input)
        APPROVAL_LINK = "https://your-company.com/aws-service-approval"

        # Special handling for first technical interaction
        if is_first_interaction and self._is_aws_related(user_input):
            if detected_service:
                if is_service_approved(detected_service):
                    return await self._handle_service_query(detected_service, user_input)
                return {
                    "response": f"I specialize in AWS IAM and related services, but not {detected_service}. Here are the services I support:",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
            return {
                "response": "Which AWS service do you need help with?",
                "services": get_approved_services_list(),
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP
            }
            
        # State machine logic
        if conversation_state == ConversationState.NORMAL:
            if detected_service:
                if is_service_approved(detected_service):
                    return await self._handle_service_query(detected_service, user_input)
                return {
                    "response": f"I don't support {detected_service}.",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
            elif any(term in user_input for term in ['aws', 'amazon', 'help']):
                return {
                    "response": "Which AWS service do you need help with?",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
        
        elif conversation_state == ConversationState.AWS_HELP:
            if detected_service:
                if is_service_approved(detected_service):
                    return await self._handle_service_query(detected_service, user_input)
                return {
                    "response": f"I don't support {detected_service}.",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services"
                }
            return {
                "response": "Please specify an AWS service from the list.",
                "services": get_approved_services_list(),
                "response_type": "approved_services"
            }
        
        elif conversation_state == ConversationState.SERVICE_SPECIFIC and current_service:
            return await self._handle_service_query(current_service, user_input)
        
        if detected_service and not is_service_approved(detected_service):
            return {
                "response": (
                    f"I'm sorry, but {detected_service} is not currently an approved service.\n"
                    "To get access, please request a CDA (Cloud Deployment Approval) by visiting:\n"
                    f"{APPROVAL_LINK}\n\n"
                    "Here are the services I can currently help with:"
                ),
                "services": get_approved_services_list(),
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP
            }
        
        # Default fallback
        return {
            "response": "How can I help you with AWS services today?",
            "response_type": "normal"
        }

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
            + "\n".join(get_approved_services_list()) + 
            "\n\nWhich service are you having trouble with?"
        )

    def _detect_service(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for service in self.approved_services:
            if service.lower() in text_lower:
                return service
        return None

    def _get_service_prompt(self) -> str:
        return (
            "To best assist you, please specify which AWS service you need help with.\n"
            "Examples:\n"
            "\"IAM: I'm getting AccessDenied errors\"\n"
            "\"EC2: Can't launch instances\"\n\n"
            f"I specialize in: {', '.join(self.approved_services)}"
        )
    
    # Add these helper methods:
    def _is_aws_related(self, text: str) -> bool:
        aws_terms = ['aws', 'amazon web services', 'cloud', 'iam', 'ec2', 's3'] + list(self.approved_services.keys())
        return any(term.lower() in text.lower() for term in aws_terms)

    async def _handle_service_query(self, service: str, query: str) -> dict:
        # Get RAG context
        results = self.rag.search_errors(query, service)
        context = self._format_rag_results(results)

        # Check if this is the first message about this service
        is_first_service_message = not bool(context)

        if is_first_service_message:
            return {
                "response": (
                    f"Thanks for asking about {service}. "
                    "To help you better, could you please:\n"
                    "1. Describe your issue in more detail\n"
                    "2. Share any error messages you're seeing\n"
                    "3. Provide screenshots or code snippets if possible\n\n"
                    "The more details you provide, the better I can assist you!"
                ),
                "new_state": ConversationState.SERVICE_SPECIFIC,
                "service": service,
                "response_type": "service_response",
                "is_approved_service": True
            }
        
        # Generate LLM response
        response = await self.ollama.chat(
            model='aws-expert',
            messages=[{
                "role": "system",
                "content": f"You are an AWS {service} expert. Provide technical help."
            }, {
                "role": "user", 
                "content": query
            }]
        )
        
        return {
            "response": response['message']['content'],
            "new_state": ConversationState.SERVICE_SPECIFIC,
            "service": service,
            "response_type": "service_response",
            "is_approved_service": True
        }