from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

# Import your RAG and Indexing functions from their respective files
from api.rag import getRetriever, ragChain
from api.indexing import ingest_text_and_upsert
from api.config import Config

# --- Initialize the FastAPI app ---
app = FastAPI(
    title="Mini RAG Application",
    description="A simple API for document-based question answering using a RAG pipeline.",
    version="1.0.0"
)

# --- CORS Middleware ---
# This allows your Next.js frontend to communicate with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, but you should restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold the RAG components
# These will be initialized once when the application starts
rag_chain = None
retriever = None

# --- Startup Event ---
# This runs once when the API starts. It's crucial for performance.
@app.on_event("startup")
async def startup_event():
    global rag_chain, retriever
    try:
        # NOTE: This part assumes you have already run 'indexing.py' at least once
        # to populate your Pinecone index.
        # This startup event only initializes the query-time components.
        
        # 1. Initialize the retriever (connects to your populated Pinecone index)
        retriever = getRetriever()
        
        # 2. Initialize the full RAG chain
        rag_chain = ragChain(retriever)
        
        print("API startup complete. RAG pipeline is ready!")

    except Exception as e:
        print(f"Failed to initialize RAG pipeline: {e}")
        # In a production environment, you might log this error
        # and raise a critical exception to prevent the app from starting.
        raise HTTPException(status_code=500, detail=f"Server startup failed: {e}")

# --- API Endpoints ---

# Pydantic model for the ingestion request
class IngestRequest(BaseModel):
    text_content: str

@app.post("/ingest")
async def ingest_document(request: IngestRequest):
    """
    Ingests new text content, chunks it, and upserts it to the vector store.
    This is for real-time updates from the frontend.
    """
    try:
        print("Received new text for ingestion. Starting upsert process...")
        # Call the reusable function from indexing.py
        ingest_text_and_upsert(request.text_content)
        print("Upsert process completed successfully.")
        return {"message": "Document ingestion successful."}
    except Exception as e:
        print(f"Ingestion failed: {e}")
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
        return {"answer": response, "sources": []} # Return sources in the response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during query processing: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"}