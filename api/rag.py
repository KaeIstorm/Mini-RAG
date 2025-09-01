import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.retrievers.document_compressors import CohereRerank
from langchain.retrievers import ContextualCompressionRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore

from api.config import Config
from api.utilities import formatDocsWithIDs

def getRetriever():
    """Creates a Retriever composed of MMR Retrieval and Cohere Reranking"""
    
    embeddings=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorStore = PineconeVectorStore.from_existing_index(
        index_name=Config.PINECONE_INDEX_NAME,
        embedding=embeddings
    )
    print("Vector store connection established.")

    retriever=vectorStore.as_retriever(
        search_type="mmr",
        search_kwargs={"fetch_k":50, "k":10}
    )

    compressor=CohereRerank(
        model="rerank-english-v3.0",
        cohere_api_key=Config.COHERE_API_KEY,
        top_n=3
    )

    finalRetriever=ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=retriever
    )

    print("Retriever and ReRanker setup and combined successfully")
    return finalRetriever

def ragChain(finalRetriever):
    """Put together the final RAG chain"""

    template="""
        You are a helpful assistant for question-answering tasks.
        Use the following pieces of retrieved context to answer the question.
        If you don't know the answer, just say that you don't know, and be graceful about it.
        Generate a concise answer and provide inline citations from the documents.
        The citations should be formatted as [Source ID].

        Context:
        {context}

        Question: {question}

        Answer:"""

    prompt = ChatPromptTemplate.from_template(template)
    llm=ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.2)
    print("LLM Initialized")

    rag=(
        {"context": finalRetriever | RunnableLambda(formatDocsWithIDs), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    print("Chain built successfully")
    return rag

if __name__=="__main__":
    print("Starting RAG Query pipeline")
    retriever=getRetriever()
    rag=ragChain(retriever)