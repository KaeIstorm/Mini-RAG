### **Project Documentation: Mini RAG Application**

This document provides a comprehensive, formal, and technical overview of the Mini RAG application, detailing its architecture, components, setup, and usage.

-----

### **1. Executive Summary**

The Mini RAG application is a full-stack, end-to-end system designed for real-time, document-based question-answering. It leverages a modern Retrieval-Augmented Generation (RAG) pipeline to ingest documents, generate vector embeddings, and provide context-aware answers with verifiable citations. The system is architecturally separated into a front-end hosted on Vercel and a backend hosted on Render, ensuring modularity and a clear division of responsibilities.

-----

### **2. System Architecture**

The application operates on a client-server model, utilizing a three-tiered architecture.

  - **Tier 1: Frontend (Next.js)**: The user interface is developed with Next.js, and is hosted on **Vercel**. It is responsible for user interactions, including document uploads and question submissions, and for displaying the final answers and citations.

  - **Tier 2: Backend (FastAPI)**: The API layer is built with FastAPI and is hosted on **Render**. It orchestrates the entire RAG pipeline, handling data ingestion, retrieval, and LLM-based generation.

  - **Tier 3: Vector Database (Pinecone)**: An external vector store that serves as the system's knowledge base. It stores vector embeddings of document chunks, enabling efficient semantic search operations.

The data flow is a two-phase process: ingestion and querying. During ingestion, documents are processed, chunked, and vectorized before being stored in Pinecone. During querying, the system retrieves relevant document chunks from Pinecone, uses them as context for a large language model, and returns a final, cited answer.

-----

### **3. Technical Components**

#### **3.1 Backend Components**

  * `Config.py`: A centralized configuration file for managing all environment variables, including API keys for Google, Pinecone, and Cohere.
  * `utilities.py`: Contains helper functions for token counting, unique document ID generation, and document formatting for LLM context.
  * `indexing.py`: A dedicated script for the document ingestion and indexing process. It loads documents, splits them into chunks using a `RecursiveCharacterTextSplitter`, and upserts the corresponding vector embeddings into the Pinecone index.
  * `rag.py`: The core of the RAG pipeline. It initializes a **Maximal Marginal Relevance (MMR)** retriever with a **Cohere Re-ranker** to improve document relevance. The RAG chain is constructed using LangChain's expression language, concurrently handling answer generation and source extraction for citations.
  * `app.py`: The FastAPI application server. It exposes `/ingest` and `/query` endpoints for file processing and question answering. It also pre-initializes the RAG chain upon startup to minimize latency for subsequent queries.

#### **3.2 Frontend Components**

  * `HomePage.js`: The primary React component that manages application state, handles API interactions with the backend, and dynamically renders the user interface. It is configured to send requests to the live backend URL hosted on Render.

-----

### **4. Deployment and Setup**

#### **4.1 Prerequisites**

  - Python 3.8+
  - Node.js and npm
  - API keys for Google, Pinecone, and Cohere.

#### **4.2 Local Setup**

**Backend:**

1.  Navigate to the project's root directory.
2.  Create a Python virtual environment and activate it.
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Install dependencies from `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file and add your API keys.
    ```
    GOOGLE_API_KEY="your_google_api_key_here"
    PINECONE_API_KEY="your_pinecone_api_key_here"
    PINECONE_INDEX_NAME="your-pinecone-index-name"
    COHERE_API_KEY="your_cohere_api_key_here"
    ```
5.  Run the `indexing.py` script once to create and populate your Pinecone index.
    ```bash
    python api/indexing.py
    ```
6.  Start the FastAPI server.
    ```bash
    uvicorn api.app:app --reload
    ```
    The API will be available at `http://localhost:8000`.

**Frontend:**

1.  Navigate to the `frontend` directory.
    ```bash
    cd frontend
    ```
2.  Install Node.js dependencies.
    ```bash
    npm install
    ```
3.  Create a `.env.local` file and set the backend API URL to the local address.
    ```
    NEXT_PUBLIC_API_URL="http://localhost:8000"
    ```
4.  Start the Next.js development server.
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:3000`.

#### **4.3 Deployment**

For deployment to a live environment, the project is configured for Vercel (frontend) and Render (backend). The API keys should be set as environment variables on the respective hosting platforms.

-----

### **5. Usage Instructions**

1.  **Ingestion:** Use the provided interface to either paste text or upload a `.txt` or `.pdf` file. This action triggers the `/ingest` endpoint on the backend, updating the Pinecone index.
2.  **Querying:** Enter a question into the text field in the "Ask a Question" section and submit the query.
3.  **Output:** The front-end will display the generated answer and a list of sources, such as page numbers, formatted as citations.

-----

### **6. Limitations and Future Work**

  - **File Support**: Current support is limited to `.txt` and `.pdf` files. Future work could extend this to include `.docx`, `.md`, and other common document formats.
  - **Conversation History**: The application is stateless and does not maintain conversation history. Implementing a session-based chat history would improve the user experience by allowing for follow-up questions and more coherent conversations.
  - **Evaluation**: The current evaluation is a manual, "gold set" based approach. Future work could include the implementation of an automated evaluation framework to systematically measure the RAG pipeline's performance.

-----