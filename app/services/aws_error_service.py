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
        filters = {"service": service_filter} if service_filter else None
        return self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )