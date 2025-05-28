import json
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict

class AWSErrorService:
    def __init__(self):
        self.db_path = Path("./data/aws_rag_db")
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        self.collection = self.client.get_or_create_collection(
            name="aws_errors",
            embedding_function=self.embed_fn
        )
        self._initialize_db()

    def _load_all_errors(self) -> List[Dict]:
        errors = []
        error_files = Path("./data/aws_errors").glob("*.json")
        
        for file in error_files:
            try:
                with open(file) as f:
                    data = json.load(f)
                    service = file.stem.replace("_errors", "").upper()
                    # Handle both "Errors" and "IAMErrors" top-level keys
                    error_list = data.get("Errors", data.get(f"{service}Errors", []))
                    for error in error_list:
                        error["service"] = service
                        errors.append(error)
            except json.JSONDecodeError as e:
                print(f"⚠️ Skipping {file.name} due to JSON error: {e}")
                continue
            except Exception as e:
                print(f"⚠️ Error processing {file.name}: {e}")
                continue
                
        return errors

    def _initialize_db(self):
        if self.collection.count() == 0:
            errors = self._load_all_errors()
            
            documents = []
            metadatas = []
            ids = []
            
            for idx, error in enumerate(errors):
                content = f"""
                [Service: {error['service']}]
                Error: {error['error_code']}
                Message: {error['error_message']}
                Fixes: {'; '.join(error.get('remediation_steps', []))}
                """
                documents.append(content)
                metadatas.append({
                    "service": error["service"],
                    "severity": error.get("severity", "Medium"),
                    "doc_link": error.get("aws_doc_link", "")
                })
                ids.append(f"{error['service']}_{idx}")

            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def search_errors(self, query: str, service_filter: str = None, n_results: int = 5):

        try:
            # Normalize inputs
            query_lower = query.lower().strip()
            
            # Special handling for AccessDenied errors
            if 'accessdenied' in query_lower or 'not authorized' in query_lower:
                # Try to find specific AccessDenied patterns
                denied_errors = []
                for error in self._load_all_errors():
                    if error['error_code'].lower() == 'accessdenied':
                        if not service_filter or error['service'] == service_filter.upper():
                            denied_errors.append(error)
                
                if denied_errors:
                    return self._format_error_response(denied_errors[:n_results])
                
            service_filter = service_filter.upper() if service_filter else None

            # Load all errors for pattern matching
            all_errors = self._load_all_errors()
            matched_errors = []
        
            # First try exact error code match
            for error in all_errors:
                # Check service filter if provided
                if service_filter and error['service'] != service_filter:
                    continue

                # Check if error code matches
                if error['error_code'].lower() in query:
                    # return self._format_error_response([error])
                    matched_errors.append(error)
                
                # Check error patterns if no direct match
                patterns = error.get('patterns', [])
                if any(pattern.lower() in query for pattern in patterns):
                    matched_errors.append(error)
            
            # If we found matches in JSON files, return them
            if matched_errors:
                return self._format_error_response(matched_errors[:n_results])

            # Fallback to semantic search in ChromaDB
            chroma_results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"service": service_filter} if service_filter else None
            )

            # Ensure we always return a properly formatted response
            if not chroma_results['documents']:
                return {'documents': [], 'metadatas': [], 'ids': []}
                
            return chroma_results
        
        except Exception as e:
            print(f"Error in search_errors: {str(e)}")
            return {'documents': [], 'metadatas': [], 'ids': []}
        
    
    def _format_error_response(self, errors: List[Dict]) -> Dict:
        """Convert error objects to ChromaDB-compatible format"""
        documents = []
        metadatas = []
        ids = []
        
        for error in errors:
            doc = f"""
            [Service: {error['service']}]
            Error: {error['error_code']}
            Message: {error['error_message']}
            Fixes: {'; '.join(error.get('remediation_steps', []))}
            """
            documents.append(doc)
            metadatas.append({
                "service": error["service"],
                "severity": error.get("severity", "Medium"),
                "doc_link": error.get("aws_doc_link", ""),
                "error_code": error["error_code"],
                "remediation_steps": error.get("remediation_steps", [])
            })
            ids.append(f"{error['service']}_{error['error_code']}")
        
        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "ids": [ids]
        }