from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_db"

def get_vectorstore():
    """Get or create the vector store for storing and retrieving job Q&A data"""
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

def job_exists(vectorstore, job_role):
    """
    Check if Q&A for a job role already exists in the vector store
    
    Args:
        vectorstore: The vector store instance
        job_role: The job role to search for
        
    Returns:
        The Q&A content if found, None otherwise
    """
    docs = vectorstore.similarity_search(f"job role: {job_role}", k=2)
    
    for doc in docs:
        if 'job_role' in doc.metadata and doc.metadata['job_role'].lower() == job_role.lower():
            return doc.page_content
        
        if job_role.lower() in doc.page_content.lower():
            return doc.page_content
    
    return None

def add_job_to_vectorstore(job_role, qa_data):
    """
    Add job Q&A data to the vector store
    
    Args:
        job_role: The job role for the Q&A
        qa_data: The Q&A content
    """
    vectorstore = get_vectorstore()
    
    metadata = {
        "job_id": str(uuid.uuid4()),
        "job_role": job_role,
        "timestamp": os.environ.get("CURRENT_TIMESTAMP", ""),
        "source": "ai-generated"
    }
    
    vectorstore.add_texts([qa_data], metadatas=[metadata])
    vectorstore.persist()
    
    return True
