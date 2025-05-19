from ollama import Client
from .aws_error_service import AWSErrorService
from typing import Optional

class ChatService:
    def __init__(self):
        self.ollama = Client(host='http://localhost:11434')
        self.error_service = AWSErrorService()
        self.aws_services = ["IAM", "EC2", "S3", "Lambda", "RDS", "Aurora", "EKS", "DynamoDB"]
    
    async def get_response(self, user_input: str) -> str:
        # Detect AWS service
        service = self._detect_aws_service(user_input)
        
        if service:
            # Get RAG context
            results = self.error_service.search_errors(user_input, service)
            context = "\n".join([
                f"🔧 {res['service']} Error:\n{res['message']}\nSolution: {res['fixes']}"
                for res in self._format_rag_results(results)
            ])
            
            # Generate with Ollama
            prompt = f"""
            You are an AWS {service} expert. Use this context:
            {context}
            
            Question: {user_input}
            """
            response = self.ollama.chat(
                model='aws-expert',  # We'll create this
                messages=[{'role': 'user', 'content': prompt}]
            )
            return response['message']['content']
        else:
            # General chat fallback
            return await self._general_chat(user_input)

    def _detect_aws_service(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for service in self.aws_services:
            if service.lower() in text_lower:
                return service
        return None

    def _format_rag_results(self, results):
        formatted = []
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            formatted.append({
                "service": meta["service"],
                "message": doc.split("Message:")[1].split("Fixes:")[0].strip(),
                "fixes": doc.split("Fixes:")[1].strip()
            })
        return formatted