from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import tiktoken

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
        # We need to re-import the necessary libraries as they are not global to this file
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_core.documents import Document
        from langchain_pinecone import PineconeVectorStore
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        # Placeholder for the chunking and upsert logic for new content
        # 1. Create a temporary document from the incoming text
        temp_doc = [Document(page_content=request.text_content, metadata={"source": "user_input"})]

        # 2. Chunk the new content using your helpers
        tokenizer = tiktoken.get_encoding("cl100k_base")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200, 
            length_function=tokenCount,
            separators=["\n\n", "\n", " ", ""]
        )
        new_chunks = splitter.split_documents(temp_doc)

        # 3. Prepare for upsert with unique IDs
        docs_with_ids = [doc for doc in new_chunks]
        for doc in new_chunks:
            doc_id = getDocID(doc)
            doc.metadata["document_id"] = doc_id

        # 4. Upsert into the vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = PineconeVectorStore.from_existing_index(
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=embeddings
        )
        vector_store.add_documents(documents=new_chunks)

        print("Received new text for ingestion. Upsert process completed successfully.")
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