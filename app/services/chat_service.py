from typing import Optional, List
from ollama import AsyncClient
from app.services.aws_error_service import AWSErrorService
import re
from enum import Enum
from app.services.approved_aws_services import APPROVED_SERVICES, is_service_approved, get_approved_services_list, get_unapproved_service

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
        unapproved_service = get_unapproved_service(user_input)
        APPROVAL_LINK = "https://your-company.com/aws-service-approval"
        # print("=====>>>>>>>>>>", unapproved_service)

        if unapproved_service and not is_service_approved(unapproved_service):
            return {
                "response": (
                    f"I'm sorry, but {unapproved_service} is not currently an approved AWS service in SYF.\n"
                    "To get access, please request a CDA (Cloud Deployment Approval) by visiting:  "
                    f"{APPROVAL_LINK}"
                ),
                "services": get_approved_services_list(),
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP,
                "service": unapproved_service,
            }

        # Check for greetings
        if is_first_interaction and self._is_greeting(user_input):
            return {
                "response": "Hello! I'm your AWS support assistant.",
                "new_state": ConversationState.INITIAL_GREETING,
                "response_type": "normal"
            }
        
        # Check for AWS service mentions
        detected_service = self._detect_service(user_input)

        # Handle first technical interaction
        if is_first_interaction and not self._is_greeting(user_input):
            if detected_service:
                if is_service_approved(detected_service):
                    print("Inside Line 56")
                    return {
                        "response": (
                            f"Thanks for asking about {detected_service} service. To help you better:\n"
                            "1. What specific issue are you facing?\n"
                            "2. Any error messages or codes?\n"
                            "3. Screenshots or code snippets would be helpful!"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": detected_service,
                        "response_type": "service_response"
                    }
                else:
                    return {
                        "response": f"I specialize in AWS IAM and related services, but not {detected_service}.",
                        "services": get_approved_services_list(),
                        "response_type": "approved_services",
                        "new_state": ConversationState.AWS_HELP
                    }
            elif self._is_aws_related(user_input):
                return {
                    "response": "Which AWS service are you having trouble with?",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
            
        # State machine logic
        if conversation_state == ConversationState.INITIAL_GREETING:
            if detected_service:
                if is_service_approved(detected_service):
                    print("Inside Line 87;;;;chat_service.py")
                    return {
                        "response": (
                            f"Thanks for asking about {detected_service} service. To help you better:\n"
                            "1. What specific issue are you facing?\n"
                            "2. Any error messages or codes?\n"
                            "3. Screenshots or code snippets would be helpful!"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": detected_service,
                        "response_type": "service_response"
                    }
                else:
                    return {
                        "response": f"I don't support {detected_service}.",
                        "services": get_approved_services_list(),
                        "response_type": "approved_services",
                        "new_state": ConversationState.AWS_HELP
                    }
            elif self._is_aws_related(user_input):
                return {
                    "response": "Which AWS service are you having trouble with?",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
            elif any(term in user_input for term in ['aws', 'amazon', 'help', 'debug']):
                return {
                    "response": "Which AWS service do you need help with?",
                    "services": get_approved_services_list(),
                    "response_type": "approved_services",
                    "new_state": ConversationState.AWS_HELP
                }
        
        elif conversation_state == ConversationState.AWS_HELP:
            if detected_service:
                if is_service_approved(detected_service):
                    print("Inside Line 124")
                    return {
                        "response": (
                            f"Thanks for asking about {detected_service} service. To help you better:\n"
                            "1. What specific issue are you facing?\n"
                            "2. Any error messages or codes?\n"
                            "3. Screenshots or code snippets would be helpful!"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": detected_service,
                        "response_type": "service_response"
                    }
                else:
                    return {
                        "response": f"I don't support {detected_service}.",
                        "services": get_approved_services_list(),
                        "response_type": "approved_services"
                    }
            return {
                "response": "Please specify an AWS service from the below list.",
                "services": get_approved_services_list(),
                "response_type": "approved_services"
            }
        
        elif conversation_state == ConversationState.SERVICE_SPECIFIC:
            if current_service:
                # Check if user provided error details or attachments
                if self._contains_error_details(user_input):
                    return await self._handle_service_query(current_service, user_input)
                else:
                    return {
                        "response": (
                            f"To better assist with your {current_service} issue:\n"
                            "1. Please describe the exact problem\n"
                            "2. Share any error messages\n"
                            "3. Attach screenshots if possible"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": current_service,
                        "response_type": "service_response"
                    }
            # Default fallback
            return {
                "response": "How can I help you with AWS services today?",
                "response_type": "normal"
            }
        
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
    
    def _contains_error_details(self, text: str) -> bool:
        """Check if message contains potential error details"""
        error_indicators = ['error', 'issue', 'problem', 'not working', 'failed']
        return any(indicator in text.lower() for indicator in error_indicators)

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
        try:
            # Get RAG context - ensure service is uppercase
            service = service.upper()
            results = self.rag.search_errors(query, service)

            # Validate we have results
            if not results or not results.get('metadatas') or not results['metadatas'][0]:
                return {
                    "response": (
                        f"Couldn't find specific error details for {service}. Common issues:\n"
                        "1. Check AWS service health status\n"
                        "2. Verify your IAM permissions\n"
                        "3. Ensure resource names follow naming rules\n\n"
                        "Please share the exact error message for more specific help."
                    ),
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": service
                }
            
            # Extract the first error's metadata
            first_error_metadata = results['metadatas'][0][0] if results['metadatas'][0] else {}
            error_code = first_error_metadata.get('error_code', 'ConfigurationError')
            remediation_steps = first_error_metadata.get('remediation_steps', [])
            doc_link = first_error_metadata.get('doc_link', '')

            response_lines = [
                f"🔴 **Error Detected**: {error_code}",
                f"📝 **Description**: Failed to create bucket due to naming rules violation",
                "🛠️ **Recommended Fixes**:"
            ]

            # Add remediation steps
            response_lines.extend([f"- {step}" for step in remediation_steps])

            # Add documentation link
            if doc_link:
                response_lines.append(f"📖 **AWS Documentation**: {doc_link}")

            return {
                "response": "\n".join(response_lines),
                "new_state": ConversationState.SERVICE_SPECIFIC,
                "service": service,
                "response_type": "rich_error"
            }
        
        except Exception as e:
            print(f"Error handling service query: {str(e)}")
            return {
                "response": (
                    f"I encountered an issue processing your S3 bucket creation error. Common solutions:\n"
                    "1. Bucket names must be lowercase and can't contain underscores\n"
                    "2. Names must be 3-63 characters long\n"
                    "3. Must start/end with letter/number\n"
                    "4. Try a different name (abcd-123789 instead of abcd_123789)"
                ),
                "new_state": ConversationState.SERVICE_SPECIFIC,
                "service": service
            }