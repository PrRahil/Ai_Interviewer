import os
import hashlib
import streamlit as st
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

# Use a temp directory for Streamlit Cloud
CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "chroma_db")

def get_openai_api_key():
    """Get OpenAI API key from environment or Streamlit secrets"""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")

def get_vectorstore():
    """Initialize and return the vector store"""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    api_key = get_openai_api_key()
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

class VectorStore:
    def __init__(self):
        self.vectorstore = get_vectorstore()
    
    def _generate_doc_id(self, job_description, interview_level):
        """Generate a unique document ID based on job description and level"""
        content = f"{job_description.strip().lower()}_{interview_level}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def add_document(self, job_description, qa_content, interview_level):
        """Add a document to the vector store"""
        try:
            # Generate unique document ID
            doc_id = self._generate_doc_id(job_description, interview_level)
            
            # Create metadata
            metadata = {
                "interview_level": interview_level,
                "job_description": job_description[:500],  # Truncate for metadata
                "doc_id": doc_id
            }
            
            # Create document
            doc = Document(
                page_content=qa_content,
                metadata=metadata
            )
            
            # Add to vector store with unique ID
            self.vectorstore.add_documents([doc], ids=[doc_id])
            
            return True
        except Exception as e:
            print(f"Error adding document to vector store: {e}")
            return False
    
    def search_similar(self, job_description, interview_level, k=1, similarity_threshold=0.8):
        """Search for similar documents in the vector store"""
        try:
            # First try to find exact match using document ID
            doc_id = self._generate_doc_id(job_description, interview_level)
            
            # Perform similarity search with filter
            results = self.vectorstore.similarity_search_with_score(
                job_description, 
                k=k,
                filter={"interview_level": interview_level}
            )
            
            if results and len(results) > 0:
                doc, score = results[0]
                # Check if it's a good match (lower scores mean higher similarity)
                if score < (1 - similarity_threshold):
                    return doc.page_content
            
            return None
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return None
    
    def delete_document(self, job_description, interview_level):
        """Delete a document from the vector store"""
        try:
            doc_id = self._generate_doc_id(job_description, interview_level)
            self.vectorstore.delete([doc_id])
            return True
        except Exception as e:
            print(f"Error deleting document from vector store: {e}")
            return False
    
    def get_all_documents(self):
        """Get all documents from the vector store"""
        try:
            # This is a simple implementation - in practice you might want pagination
            results = self.vectorstore.similarity_search("", k=100)  # Get up to 100 docs
            return results
        except Exception as e:
            print(f"Error getting all documents from vector store: {e}")
            return []
