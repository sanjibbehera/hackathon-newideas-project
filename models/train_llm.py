import sqlite3
from pathlib import Path
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index.storage.storage_context import StorageContext
from llama_index.vector_stores import SQLiteVectorStore

# Initialize SQLite vector store
vector_store = SQLiteVectorStore(db_path="db/iam_knowledge.db")
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Load documents
documents = SimpleDirectoryReader("data").load_data()

# Create and persist index
index = VectorStoreIndex.from_documents(
    documents, 
    storage_context=storage_context
)
index.storage_context.persist()