### **Project Documentation: Mini RAG Application**

This document provides a comprehensive, formal, and technical overview of the Mini RAG application, detailing its architecture, components, setup, and usage.

-----

### **1. Executive Summary**

The Mini RAG application is a full-stack, end-to-end system designed for real-time, document-based question-answering. It leverages a modern Retrieval-Augmented Generation (RAG) pipeline to ingest documents, generate vector embeddings, and provide context-aware answers with verifiable citations. The system is architecturally separated into a front-end hosted on Vercel and a backend hosted on Render, ensuring modularity and a clear division of responsibilities.

-----

### **2. System Architecture**

The application operates on a client-server model, utilizing a three-tiered architecture.

  * **Tier 1: Frontend (Next.js)**: The user interface is developed with Next.js, and is hosted on **Vercel**. It is responsible for user interactions, including document uploads and question submissions, and for displaying the final answers and citations.

  * **Tier 2: Backend (FastAPI)**: The API layer is built with FastAPI and is hosted on **Render**. It orchestrates the entire RAG pipeline, handling data ingestion, retrieval, and LLM-based generation.

  * **Tier 3: Vector Database (Pinecone)**: An external vector store that serves as the system's knowledge base. It stores vector embeddings of document chunks, enabling efficient semantic search operations.

The data flow is a two-phase process: ingestion and querying. During ingestion, documents are processed, chunked, and vectorized before being stored in Pinecone. During querying, the system retrieves relevant document chunks from Pinecone, uses them as context for a large language model, and returns a final, cited answer.

-----

### **3. RAG Pipeline Details**

#### **3.1 Architecture Diagram**

The following diagram illustrates the high-level architecture and data flow of the Mini RAG system:

#### **3.2 Providers and Models**

| Component | Provider/Library | Model/Service Used |
| :--- | :--- | :--- |
| **Embeddings** | Pinecone | `multilingual-e5-large` |
| **LLM** | Google Generative AI | `gemini-2.5-pro` |
| **Vector Store** | Pinecone | Managed Vector Database |
| **Re-ranking** | Cohere | `rerank-english-v3.0` |

#### **3.3 Chunking Parameters**

The document chunking process is configured with the following parameters to balance chunk size and context preservation:

  * **Chunk Size**: 1000 tokens
  * **Chunk Overlap**: 200 tokens
  * **Separator Priority**: `["\n\n", "\n", " ", ""]`

This configuration ensures that each chunk is large enough to contain meaningful context while the overlap helps maintain continuity across chunks, preventing critical information from being split.

#### **3.4 Retriever and Re-ranker Settings**

The retrieval process is optimized for both relevance and diversity:

  * **Base Retriever**: Uses **Maximal Marginal Relevance (MMR)** to fetch an initial set of diverse, relevant documents. It is configured with `search_kwargs={"fetch_k": 50, "k": 10}`. This means it retrieves the **top 50** most similar documents from the vector store and then selects the **top 10** among them that are most diverse.
  * **Contextual Re-ranker**: The `CohereRerank` model is then applied to the top 10 documents to re-rank them based on their semantic relevance to the query. The final context provided to the LLM consists of the `top_n=3` most relevant documents after re-ranking.

-----

### **4. Technical Components**

#### **4.1 Backend Components**

  * `Config.py`: A centralized configuration file for managing all environment variables, including API keys for Pinecone and Cohere.
  * `utilities.py`: Contains helper functions for token counting, unique document ID generation, and document formatting for LLM context.
  * `indexing.py`: A dedicated script for the document ingestion and indexing process. **It now uses the `Unstructured` library to handle a wide range of file types beyond just text and PDFs.** It creates a temporary file on the server before processing, ensuring compatibility with hosted environments like Render. It loads documents, splits them into chunks using a `RecursiveCharacterTextSplitter`, and upserts the corresponding vector embeddings into the Pinecone index using Pinecone's integrated embedding service.
  * `rag.py`: The core of the RAG pipeline. **It has been updated to use Pinecone's integrated embedding model (`multilingual-e5-large`) for both ingestion and querying, which resolves API quota issues.** It initializes a **Maximal Marginal Relevance (MMR)** retriever with a **Cohere Re-ranker** to improve document relevance. The RAG chain is constructed using LangChain's expression language.
  * `app.py`: The FastAPI application server. It exposes `/ingest` and `/query` endpoints for file processing and question answering. It also pre-initializes the RAG chain upon startup to minimize latency for subsequent queries.

#### **4.2 Frontend Components**

  * `HomePage.js`: The primary React component that manages application state, handles API interactions with the backend, and dynamically renders the user interface. It is configured to send requests to the live backend URL hosted on Render.

-----

### **5. Deployment and Setup**

#### **5.1 Prerequisites**

  * Python 3.8+
  * Node.js and npm
  * API keys for Google, Pinecone, and Cohere.
  * **Ensure that your Pinecone index is configured with a dimension of 1024 to match the `multilingual-e5-large` embedding model.**

#### **5.2 Local Setup**

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
    ```dotenv
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
    ```dotenv
    NEXT_PUBLIC_API_URL="http://localhost:8000"
    ```
4.  Start the Next.js development server.
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:3000`.

#### **5.3 Deployment**

For deployment to a live environment, the project is configured for Vercel (frontend) and Render (backend). The API keys should be set as environment variables on the respective hosting platforms.

-----

### **6. Usage Instructions**

1.  **Ingestion:** Use the provided interface to either paste text or upload a document. **The system now supports a wide range of file types, including DOCX, PPTX, and more, thanks to the `Unstructured` library.** This action triggers the `/ingest` endpoint on the backend, updating the Pinecone index.
2.  **Querying:** Enter a question into the text field in the "Ask a Question" section and submit the query.
3.  **Output:** The front-end will display the generated answer and a list of sources, such as page numbers, formatted as citations.

-----

### **7. Performance evaluation using Golden Set**

The RAG's current knowledge base consists of knowledge, documentation, and code about its own functioning, which we use to derive the following golden set comprising of pairs of five question-answers to evaluate the RAG's performance.

**1. Question:** How do the `fetch_k` and `k` parameters of the base retriever work together, and what is the final number of documents that the `gemini-2.5-pro` model receives as context after the re-ranking step?

**Expected Answer:** The base retriever first retrieves **50** documents from the vector store using `fetch_k`. It then selects the **top 10** most diverse documents from that set using the `k` parameter. The `CohereRerank` model then processes these 10 documents, and the final context provided to the `gemini-2.5-pro` model consists of the **top 3** most relevant documents after re-ranking.


**2. Question:** Describe the two distinct methods of document ingestion mentioned in the documentation, including how one of them has been specifically updated to handle in-memory processing for deployment on Render.

**Expected Answer:** The documentation describes two methods for document ingestion: **pasting text** or **uploading a file**. The `indexing.py` script has been specifically updated to handle in-memory processing for file uploads by creating a temporary file on the server. This temporary file is written to, processed by the `UnstructuredFileLoader`, and then deleted from the server, ensuring compatibility with the hosted Render environment.


**3. Question:** The documentation states the application is stateless and doesn't maintain conversation history. How does the `app.py` startup process address a similar issue, but for the RAG pipeline components themselves?

**Expected Answer:** The `app.py` startup process addresses the issue of RAG pipeline state by **pre-initializing** the retriever and the full RAG chain upon application startup. This is done to minimize the latency for subsequent queries by ensuring the core RAG components are ready and don't need to be recreated for each request.


**4. Question:** If a new developer is setting up the project locally and incorrectly configures their Pinecone index dimension, what is the exact numerical mismatch they will see in the error, and what is the required dimension for the specified embedding model?

**Expected Answer:** The developer will receive an error indicating a dimension mismatch between **1024** and **768**. The error will specifically state "Vector dimension 1024 does not match the dimension of the index 768." The required dimension for the `multilingual-e5-large` embedding model is **1024**.


**5. Question:** Which two backend components are directly responsible for the ingestion process, and what is the role of the `utilities.py` file within this process?

**Expected Answer:** The two backend components directly responsible for the ingestion process are **`app.py`** and **`indexing.py`**. `app.py` receives the uploaded file and calls the `loadAndChunk` and `vectorUpsert` functions from `indexing.py`. The `utilities.py` file supports this process by providing helper functions for token counting (`tokenCount`) and generating a unique document ID for each chunk (`getDocID`).

For the above questions, the RAG provides the following answers:

**Answer 1:** Based on the provided documentation, the base retriever uses Maximal Marginal Relevance (MMR) to first fetch the **top 50** most similar documents from the vector store, as specified by `fetch_k=50`. From this initial set, it then selects the **top 10** most diverse documents, as configured by `k=10`. After this initial retrieval, a `CohereRerank` model re-ranks these 10 documents for semantic relevance to the query. The `gemini-2.5-pro` model then receives the **top 3** most relevant documents as its final context.

**Answer 2:** Based on the documentation, the two methods for document ingestion are: 1. **Pasting Text**: A user can paste text directly into the application's interface. The frontend then converts this text into a temporary file (`Blob`) before sending it to the backend for processing [p.6]. 2. **Uploading a Document**: A user can upload a file directly. The system supports a wide range of file types, including DOCX and PPTX, by using the `Unstructured` library [p.6]. The ingestion process was specifically updated for deployment on Render. The backend `indexing.py` script now creates a temporary file on the server upon receiving the data. This step ensures compatibility with hosted environments like Render, which may have specific filesystem requirements [p.4].

**Answer 3:** While the application is stateless regarding conversation history, the `app.py` server addresses a similar performance concern for the RAG pipeline itself. It uses a startup event to pre-initialize the RAG chain and its components when the server first starts [p.2], [app.py]. This is done to minimize latency for all subsequent queries by ensuring the RAG pipeline is ready to use without needing to be reloaded for each individual request [p.2].

**Answer 4:** Based on the provided documents, the required dimension for the Pinecone index is **1024**. This is to match the `multilingual-e5-large` embedding model used for both ingestion and querying. The context does not specify the exact numerical mismatch a developer would see in an error message if the index were configured incorrectly.

**Answer 5:** Based on the provided documents, the two backend components directly responsible for the ingestion process are `app.py` and `indexing.py`. * **`app.py`**: This is the FastAPI application server that exposes the `/ingest` endpoint, which receives the file or text from the user to begin the process. * **`indexing.py`**: This script is dedicated to the document ingestion and indexing process. It uses the `Unstructured` library to handle various file types, splits the documents into chunks, and upserts their vector embeddings into the Pinecone index. The **`utilities.py`** file supports this process by providing helper functions, such as `getDocID`, which generates a unique and stable ID for each document chunk before it is indexed.

We can make the following statements about the Precision and Recall of the RAG based on the above answers:

* **Precision:** The system's answers are consistently accurate and directly relevant to the questions asked. There's no extraneous or irrelevant information included. For example, in Answer 1, the model correctly identifies all three key numerical parameters (`50`, `10`, and `3`) and explains their roles in the RAG pipeline.

* **Recall:** The system effectively retrieves all necessary information to provide a complete answer. For example, in Answer 5, it not only identifies the two main components (`app.py`, `indexing.py`) but also correctly explains the role of the helper file, `utilities.py`, demonstrating a comprehensive recall of the relevant sections.

-----

### **7. Limitations and Future Work**

  * **File Support**: The application now supports a wide variety of file types.
  * **Conversation History**: The application is stateless and does not maintain conversation history. Implementing a session-based chat history would improve the user experience by allowing for follow-up questions and more coherent conversations.
  * **Evaluation**: The current evaluation is a manual, "gold set" based approach. Future work could include the implementation of an automated evaluation framework to systematically measure the RAG pipeline's performance.

-----