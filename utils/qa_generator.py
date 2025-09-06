import os
import hashlib
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from .simple_vector_store import SimpleVectorStore

def get_openai_api_key():
    """Get OpenAI API key from environment or Streamlit secrets"""
    # Try to get from Streamlit secrets first (for cloud deployment)
    try:
        return st.secrets["OPENAI_API_KEY"]
    except:
        # Fallback to environment variable (for local development)
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("OPENAI_API_KEY")

def generate_or_retrieve_qa(job_description, interview_level="entry"):
    """
    Generate or retrieve Q&A for interview preparation
    
    Args:
        job_description (str): Job description or role
        interview_level (str): entry, mid, or senior
    
    Returns:
        tuple: (qa_content, from_cache, title)
    """
    try:
        # Get API key
        api_key = get_openai_api_key()
        if not api_key:
            raise Exception("OpenAI API key not found. Please set OPENAI_API_KEY in secrets.")
        
        # Initialize simple vector store
        vector_store = SimpleVectorStore()
        
        # Create a title from job description
        title = job_description[:50].strip() + ("..." if len(job_description) > 50 else "")
        
        # Try to retrieve from vector store first
        cached_result = vector_store.search_similar(job_description, interview_level)
        
        if cached_result:
            return cached_result, True, title
        
        # Generate new Q&A using LangChain
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            openai_api_key=api_key
        )
        
        prompt_template = PromptTemplate(
            input_variables=["job_description", "interview_level"],
            template="""
            Create comprehensive interview questions and answers for the following job:
            
            Job Description: {job_description}
            Interview Level: {interview_level}
            
            Generate 8-10 relevant questions with detailed answers covering:
            1. Technical skills and knowledge
            2. Problem-solving scenarios
            3. Behavioral questions
            4. Role-specific challenges
            
            Format the response in markdown with clear sections:
            
            ## Technical Questions
            
            **Q1: [Technical Question]**
            A: [Detailed Answer]
            
            ## Problem-Solving Questions
            
            **Q2: [Problem-Solving Question]**
            A: [Detailed Answer]
            
            ## Behavioral Questions
            
            **Q3: [Behavioral Question]**
            A: [Detailed Answer]
            
            Continue this format for all questions.
            """
        )
        
        # Use the new RunnableSequence approach
        chain = prompt_template | llm
        result = chain.invoke({
            "job_description": job_description,
            "interview_level": interview_level
        })
        
        qa_content = result.content
        
        # Store in vector database for future use
        vector_store.add_document(job_description, qa_content, interview_level)
        
        return qa_content, False, title
        
    except Exception as e:
        raise Exception(f"Error generating Q&A: {str(e)}")
