from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Any
import tiktoken
import os
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document

# Import your RAG and Indexing functions from their respective files
from api.rag import getRetriever, ragChain
from api.indexing import loadAndChunk, vectorUpsert
from api.config import Config

# Import helpers from your helpers.py file
from api.utilities import getDocID, tokenCount

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
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingests a new document file (e.g., PDF, TXT), chunks it, and upserts to the vector store.
    """
    try:
        # Save the uploaded file temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Now call your updated load and chunk function
        chunks = loadAndChunk(file_path)
        vectorUpsert(chunks)

        # Remove the temporary file
        os.remove(file_path)

        return {"message": f"Document '{file.filename}' ingested successfully."}
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict later to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)