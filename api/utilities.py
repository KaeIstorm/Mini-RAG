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
    """
    Formats documents for the LLM. For PDFs, it includes a page number citation.
    For other documents, it includes the content without a citation.
    """
    formatted_output = []
    for i, doc in enumerate(docs):
        # Check if the document has a 'page' key in its metadata, indicating it's a PDF chunk
        if "page" in doc.metadata:
            formatted_output.append(f"Source: Page {doc.metadata['page']}\nContent: {doc.page_content}")
        else:
            # For other document types, just provide the content without a source ID
            formatted_output.append(f"Content: {doc.page_content}")
            
    return "\n\n".join(formatted_output)