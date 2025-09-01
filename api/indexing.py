#import libraries
import os
from pinecone import Pinecone
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

#import modules
from api.config import Config
from api.utilities import getDocID, tokenCount

#loading and chunking the document
def loadAndChunk(path:str):
    """Loads the provided text and chunks it."""
    
    #document loading
    loader=TextLoader(path)
    documents=loader.load()
    print("Documents loaded successfully!")

    #document chunking
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200, 
        length_function=tokenCount,
        separators=["\n\n", "\n", " ", ""]
    )
    print("Documents chunked successfully!")
    
    return splitter.split_documents(documents)

#create vector embedings and store them in a vector DB
def vectorUpsert(chunks: list):
    """Translates the document chunks into vector embeddings and upserts them to a vector DB (Pinecone in this case)"""
    from langchain_pinecone import PineconeVectorStore

    #vector embeddings
    embeddings=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    print("Documnents embedded successfully")

    #preparing docs for upserting
    docsWithIDs=[]
    for doc in chunks:
        docID=getDocID(doc)
        doc.metadata["document_id"]=docID
        docsWithIDs.append(doc)

    pc = Pinecone(api_key=Config.PINECONE_API_KEY)

    if Config.PINECONE_INDEX_NAME in [index['name'] for index in pc.list_indexes()]:
        print("Index already exists. Performing upsert...")
        # Initialize an existing PineconeVectorStore instance
        vectorStore = PineconeVectorStore.from_existing_index(
            index_name=Config.PINECONE_INDEX_NAME,
            embedding=embeddings
        )
        # Use the add_documents method to upsert
        vectorStore.add_documents(documents=docsWithIDs, ids=[doc.metadata["document_id"] for doc in docsWithIDs])
    else:
        print("Index does not exist. Creating and populating for the first time...")
        # This line is for initial population only
        PineconeVectorStore.from_documents(
            documents=docsWithIDs,
            embedding=embeddings,
            index_name=Config.PINECONE_INDEX_NAME
        )
        print("Embedding and storage completed")

if __name__=="__main__":
    print("Starting Document Indexing")
    chunks=loadAndChunk(Config.DOC_PATH)
    vectorUpsert(chunks)
    print("Indexing complete")