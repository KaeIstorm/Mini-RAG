from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, Optional
import tiktoken
import tempfile
import os

# Import your RAG and Indexing functions from their respective files
from api.rag import getRetriever, ragChain
from api.indexing import loadAndChunk, vectorUpsert
from api.config import Config

# Import helpers from your helpers.py file
from api.utilities import getDocID, tokenCount

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- Initialize the FastAPI app ---
app = FastAPI(
    title="Mini RAG Application",
    description="A simple API for document-based question answering using a RAG pipeline.",
    version="1.0.0"
)

# Global variables to hold the RAG components
retriever = None
rag_chain = None

# --- Startup Event ---
# This runs once when the API starts. It's crucial for performance.
@app.on_event("startup")
async def startup_event():
    global retriever, rag_chain
    try:
        # NOTE: This part assumes you have already run 'indexing.py' once
        # to populate your Pinecone index.
        # This startup event only initializes the query-time components.
        
        # 1. Initialize the retriever (connects to your populated Pinecone index)
        retriever = getRetriever()
        
        # 2. Initialize the full RAG chain
        rag_chain = ragChain(retriever)
        
        print("API startup complete. RAG pipeline is ready!")

    except Exception as e:
        print(f"Failed to initialize RAG pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Server startup failed: {e}")


# --- API Endpoints ---

@app.post("/ingest")
async def ingest_document(
    text_content: str = None,
    file: UploadFile = File(None)
):
    try:
        from langchain_core.documents import Document

        docs = []

        # Case 1: Plain text ingestion
        if text_content:
            docs.append(Document(page_content=text_content, metadata={"source": "user_input"}))

        # Case 2: File ingestion
        if file:
            contents = await file.read()
            if file.filename.endswith(".pdf"):
                from langchain_community.document_loaders import PyPDFLoader
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(contents)
                    tmp.flush()
                    loader = PyPDFLoader(tmp.name)
                    docs.extend(loader.load())
            elif file.filename.endswith(".txt"):
                docs.append(Document(page_content=contents.decode("utf-8"), metadata={"source": file.filename}))
            # Add docx loader if needed later

        # Then chunk + upsert (same as before)
        # ...

        return {"message": "Document ingestion successful."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {e}")



# Pydantic model for the query request
class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def run_query(request: QueryRequest):
    """
    Queries the RAG pipeline with a user's question.
    """
    if not rag_chain:
        raise HTTPException(status_code=503, detail="RAG service is not ready.")

    try:
        # Invoke the pre-initialized RAG chain with the user's question
        response = rag_chain.invoke(request.question)
        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during query processing: {e}")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)