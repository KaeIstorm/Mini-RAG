import tiktoken
import hashlib
from langchain_core.documents import Document

def tokenCount(text):
    tokenizer=tiktoken.get_encoding("cl100k_base")
    return len(tokenizer.encode(text))

def getDocID(doc: Document) -> str:
    """Generates a unique, stable ID for a document chunk."""
    content_hash = hashlib.sha256(doc.page_content.encode('utf-8')).hexdigest()
    # Combine with metadata to make it more unique
    metadata_string = str(doc.metadata)
    metadata_hash = hashlib.sha256(metadata_string.encode('utf-8')).hexdigest()
    return f"{content_hash}-{metadata_hash}"

def formatDocsWithIDs(docs):
    return "\n\n".join([f"Source ID: {i+1}\nContent: {doc.page_content}" for i, doc in enumerate(docs)])
