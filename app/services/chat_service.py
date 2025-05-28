from typing import Optional, List
from ollama import AsyncClient
from app.services.aws_error_service import AWSErrorService
import re, os
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

        # Check for multiple services first
        detected_services = self._detect_multiple_services(user_input)
        if len(detected_services) > 1:
            multiple_services_response = self._handle_multiple_services(detected_services, user_input)
            if multiple_services_response:
                return multiple_services_response

        if unapproved_service and not is_service_approved(unapproved_service):
            return {
                "response": (
                    f"I'm sorry, but {unapproved_service} is not currently an approved AWS service in SYF.\n"
                    "To get access, please request a CDA (Cloud Deployment Approval) by visiting:  "
                    f"{APPROVAL_LINK}\n\n"
                    "Here are the services I can currently help with:"
                ),
                "services": get_approved_services_list(),
                "unapproved_services": [unapproved_service],  # Add this line
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP,
                "service": unapproved_service,
            }

        # Check for greetings
        if is_first_interaction and self._is_greeting(user_input):
            if detected_services:
                # User greeted and mentioned services in first message
                if len(detected_services) == 1:
                    service = detected_services[0]
                    if is_service_approved(service):
                        return {
                            "response": (
                                f"Hello! Thanks for asking about {service}. "
                                "To help you better:\n"
                                "1. What specific issue are you facing?\n"
                                "2. Any error messages?\n"
                                "3. Screenshots would be helpful!"
                            ),
                            "new_state": ConversationState.SERVICE_SPECIFIC,
                            "service": service,
                            "response_type": "service_response"
                        }
            else:
                # Simple greeting
                return {
                    "response": "Hello! I'm your AWS support assistant.",
                    "new_state": ConversationState.INITIAL_GREETING,
                    "response_type": "normal"
                }
        
        # Check for AWS service mentions
        detected_service = self._detect_service(user_input)

        # Check IAM context
        is_iam_question, related_service = self._detect_iam_context(user_input)
        if is_iam_question:
            if related_service:
                if len(related_service) == 1:
                    return {
                        "response": (
                            f"I see you're having IAM issues with {related_service[0]}. To help you better:\n"
                            "1. Please share the exact error message or logs\n"
                            "2. Describe what you were trying to do\n"
                            "3. Include any relevant policy documents or screenshots"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": related_service[0],
                        "response_type": "service_response"
                    }
                else:
                    return {
                        "response": (
                            "I see you're having IAM issues with multiple services. To help you better:\n"
                            "1. Please share the exact error messages or logs for each service\n"
                            "2. Specify which service(s) you need help with first\n"
                            "3. Include any relevant policy documents or screenshots\n\n"
                            f"Mentioned services: {', '.join(related_service)}"
                        ),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": "IAM",
                        "response_type": "service_response"
                    }
            else:
                return {
                    "response": (
                        "I see you're having IAM issues. To help you better:\n"
                        "1. Please share the exact error message or logs\n"
                        "2. Describe what you were trying to do\n"
                        "3. Include any relevant policy documents or screenshots\n"
                        "4. Specify if this is for a particular AWS service\n\n"
                    ),
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": "IAM",
                    "response_type": "service_response"
                }
            
        
        # Check for similar services
        similar_service_mapping = {
            'clouddeploy': 'CodeDeploy',
            'cloudsearch': 'OpenSearch',
            'cassandra': 'KeySpaces',
        }

        for similar_term, approved_term in similar_service_mapping.items():
            if similar_term in user_input.lower() and approved_term in self.approved_services:
                return {
                    "response": f"I noticed you mentioned '{similar_term}'. Did you mean '{approved_term}'? (yes/no)",
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": approved_term,
                    "needs_confirmation": True,
                    "response_type": "service_confirmation"
                }

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
                    # Try to detect service from ARN if not already specified
                    if not current_service:
                        arn_service = self._detect_service_from_arn(user_input)
                        if arn_service:
                            current_service = arn_service
                    # If we have a service context, try to get solution
                    if current_service:
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
    
    def _detect_service_from_arn(self, text: str) -> Optional[str]:
        """Extract AWS service from ARN if present in text"""
        arn_pattern = re.compile(r'arn:aws:([a-z0-9-]+):[a-z0-9-]*:[0-9]*:.+')
        match = arn_pattern.search(text.lower())
        if match:
            service = match.group(1)
            # Map some service abbreviations to full names
            service_map = {
                'sts': 'IAM',
                'rds': 'RDS',
                'ec2': 'EC2',
                's3': 'S3',
                'lambda': 'Lambda',
                'iam': 'IAM',
                'dynamodb': 'DynamoDB',
                'redshift': 'Redshift'
            }
            return service_map.get(service, service.upper())
        return None
    
    def _contains_error_details(self, text: str) -> bool:
        """Check if message contains potential error details"""
        error_indicators = [
            'accessdenied', 
            'not authorized',
            'is not authorized to perform',
            'permission denied',
            'unauthorized',
            r'user\s.*\sis\snot\sauthorized',  # More robust regex
            'issue',
            r'arn:aws:',  # More general ARN detection
            'error',
            'failed',
            'cannot',
            r'\bdenied\b',  # Word boundary for standalone 'denied'
            r'rds:\w+',  # Detect RDS API calls
            r'ec2:\w+',  # Detect EC2 API calls
            r's3:\w+',  # Detect S3 API calls
            r'dynamodb:\w+',  # Detect DynamoDB API calls
            r'aurora:\w+',  # Detect Aurora API calls
            r's3:\w+',  # Detect S3 API calls
            r'bucket\s?policy',  # Detect bucket policy mentions
            r'service\s?control\s?policy|scp',  # Detect SCP mentions
            r'access\s?denied',  # More flexible matching
        ]
        text_lower = text.lower()
        return any(re.search(indicator, text_lower) for indicator in error_indicators)

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
        potential_matches = []

        # First pass - exact matches
        for service in self.approved_services:
            if service.lower() in text_lower:
                potential_matches.append(service)
        
        if len(potential_matches) == 1:
            return potential_matches[0]
        
        # Handle similar service names (like CloudDeploy vs CodeDeploy)
        similar_services = {
            'clouddeploy': 'CodeDeploy',
            'cloudsearch': 'OpenSearch',
            'cassandra': 'KeySpaces',
            # Add other similar service mappings as needed
        }

        for term, service in similar_services.items():
            if term in text_lower and service in self.approved_services:
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
    
    # Add these new methods to ChatService class
    def _detect_multiple_services(self, text: str) -> List[str]:
        """Detect multiple AWS services mentioned in text"""
        detected_services = []
        text_lower = text.lower()
        
        for service in self.approved_services:
            if service.lower() in text_lower:
                detected_services.append(service)
        
        return detected_services
    
    def _handle_multiple_services(self, services: List[str], user_input: str) -> dict:
        """Handle case where user mentions multiple services"""
        iam_mentioned = any(s.upper() == "IAM" for s in services)
        other_services = [s for s in services if s.upper() != "IAM"]
        
        if iam_mentioned and other_services:
            # User mentioned IAM and other services
            services_info = []

            # Check if it's specifically about IAM permissions/roles for these services
            iam_keywords = ['permission', 'policy', 'role', 'access', 'issue', 'issues']
            is_iam_for_services = any(kw in user_input.lower() for kw in iam_keywords)

            if is_iam_for_services:
                return {
                    "response": (
                        f"I see you're having IAM permission issues with {', '.join(other_services)}. "
                        "To help you better:\n"
                        "1. Please share the exact IAM error message or logs\n"
                        "2. Describe what IAM permissions you were trying to set up\n"
                        "3. Include any relevant policy documents or screenshots\n"
                        f"4. Specify if this is for {other_services[0]} or all mentioned services\n{os.linesep}"
                    ),
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": "IAM",
                    "response_type": "service_response"
                }
            else:
                # Original handling for non-IAM-specific cases
                services_info = []                
                for service in other_services:
                    services_info.append({
                        "message": (
                            f"For {service}, could you please provide:\n"
                            "1. The specific issue you're facing\n"
                            "2. Any error messages\n"
                            "3. Relevant details or screenshots"
                        ),
                        "services": None
                    })
                
                services_info.append({
                    "message": "For IAM, please describe your issue:",
                    "services": None
                })
            
                return {
                    "response": f"I see you have mentioned both IAM and other AWS services {other_services[0]}. Let me help you with each one separately:",
                    "services_info": services_info,
                    "response_type": "multiple_services",
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "all_services": services  # Include all services for reference
                }
        elif len(services) > 1:
            # Multiple non-IAM services mentioned
            return {
                "response": "I see you have mentioned multiple AWS services. Please tell me which AWS service, you'd like to focus on first:",
                "services": [f"{s} - {self.approved_services[s]}" for s in services],
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP
            }
        else:
            # Fallback to single service handling
            return None
        
    async def _handle_similar_service(self, user_input: str, similar_service: str, approved_service: str) -> dict:
        if "yes" in user_input.lower() or approved_service.lower() in user_input.lower():
            return {
                "response": (
                    f"Thanks for confirming you meant {approved_service}. To help you better:\n"
                    "1. What specific issue are you facing?\n"
                    "2. Any error messages or codes?\n"
                    "3. Screenshots or code snippets would be helpful!"
                ),
                "new_state": ConversationState.SERVICE_SPECIFIC,
                "service": approved_service,
                "response_type": "service_response"
            }
        else:
            return {
                "response": (
                    f"I'm sorry, but {similar_service} is not currently an approved AWS service.\n"
                    "To get access, please request a CDA (Cloud Deployment Approval).\n\n"
                    "Here are the services I can currently help with:"
                ),
                "services": get_approved_services_list(),
                "response_type": "approved_services",
                "new_state": ConversationState.AWS_HELP
            }
        
    def _detect_iam_context(self, text: str) -> tuple:
        """Returns (is_iam_question, related_service)"""
        text_lower = text.lower()
        iam_terms = ['iam', 'permission', 'policy', 'role', 'access', 'auth', 'authorize']

        if not any(term in text_lower for term in iam_terms) or not self._contains_error_details(text_lower):
            return (False, None)
        
        # Try to extract service from ARN if present
        arn_service = self._detect_service_from_arn(text_lower)
        if arn_service:
            return (True, [arn_service])
        
        # Find all mentioned services (except IAM itself)
        mentioned_services = []
        for service in self.approved_services:
            if service.lower() != 'iam' and service.lower() in text_lower:
                mentioned_services.append(service)
    
        return (True, mentioned_services if mentioned_services else None)
    
    # Add these helper methods:
    def _is_aws_related(self, text: str) -> bool:
        aws_terms = ['aws', 'amazon web services', 'amazon', 'cloud', 'iam', 'ec2', 's3'] + list(self.approved_services.keys())
        return any(term.lower() in text.lower() for term in aws_terms)

    async def _handle_service_query(self, service: str, query: str) -> dict:
        try:
            # Enhanced error detection
            if self._contains_error_details(query):
                # Try to extract service from ARN if not specified
                if not service or service.upper() == 'IAM':
                    arn_service = self._detect_service_from_arn(query)
                    if arn_service:
                        service = arn_service
                
                # Get RAG context for IAM errors
                results = self.rag.search_errors(query, service or 'IAM')
                
                if results and results.get('metadatas') and results['metadatas'][0]:
                    # Process IAM permission error results
                    first_error = results['metadatas'][0][0]
                    error_code = first_error.get('error_code', 'AccessDenied')
                    remediation = first_error.get('remediation_steps', [])
                    doc_link = first_error.get('doc_link', '')
                    
                    response_lines = [
                        f"🔴 **Identified Error**: {error_code}",
                        f"🛠️ **Recommended Solution**:"
                    ]

                    # Add service-specific remediation if available
                    if service and service.upper() != 'IAM':
                        response_lines.append(f"- Verify IAM permissions for {service}")
                        response_lines.append(f"- Check {service} resource policies")
                    
                    # Add general remediation steps
                    response_lines.extend([
                        "- Check IAM policies attached to your role/user",
                        "- Verify resource ARNs in your policy match exactly",
                        "- Ensure the service has necessary trust relationships",
                        f"📖 **AWS Documentation**: {doc_link or 'https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html'}"
                    ])

                    return {
                        "response": "\n".join(response_lines),
                        "new_state": ConversationState.SERVICE_SPECIFIC,
                        "service": service if service else 'IAM',
                        "response_type": "rich_error"
                    }
            
            # Get RAG context - ensure service is uppercase
            service = service.upper()
            results = self.rag.search_errors(query, service)

            # Validate we have results
            if results or results.get('metadatas') or results['metadatas'][0]:
                first_error = results['metadatas'][0][0]
                error_code = first_error.get('error_code', 'AccessDenied')
                remediation = first_error.get('remediation_steps', [])
                doc_link = first_error.get('doc_link', '')

                response_lines = [
                    f"🔴 **Identified Error**: {error_code}",
                    f"🛠️ **Recommended Solution**:"
                ]

                # Add remediation steps
                if remediation:
                    response_lines.extend([f"- {step}" for step in remediation])
                else:
                    response_lines.append("- Check IAM permissions for the service")
                    response_lines.append("- Verify resource ARNs in your policy")
                
                if doc_link:
                    response_lines.append(f"📖 **AWS Documentation**: {doc_link}")
                
                return {
                    "response": "\n".join(response_lines),
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": service,
                    "response_type": "rich_error"
                }
            
            # Fallback for generic AccessDenied errors
            if 'accessdenied' in query.lower() or 'not authorized' in query.lower():
                return {
                    "response": (
                        "🔴 **Identified Error**: AccessDenied\n"
                        "🛠️ **Recommended Solution**:\n"
                        "- Verify the IAM permissions attached to your role/user\n"
                        "- Check if the resource ARN in your policy matches exactly\n"
                        "- Ensure the service has the necessary trust relationship\n"
                        "📖 **AWS Documentation**: https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html"
                    ),
                    "new_state": ConversationState.SERVICE_SPECIFIC,
                    "service": service if service else "IAM",
                    "response_type": "rich_error"
                }
            
            # Generic fallback
            return {
                "response": (
                    f"Couldn't find specific error details for {service}. Common solutions:\n"
                    "1. Check IAM permissions for the service\n"
                    "2. Verify resource ARNs in your policy\n"
                    "3. Check AWS service health status\n\n"
                    "Please share more details if you need specific help."
                ),
                "new_state": ConversationState.SERVICE_SPECIFIC,
                "service": service
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