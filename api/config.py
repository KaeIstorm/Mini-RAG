import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
    PINECONE_API_KEY=os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME=os.getenv("PINECONE_INDEX_NAME")
    COHERE_API_KEY=os.getenv("COHERE_API_KEY")
    DOC_PATH="docs/sampletext.txt"