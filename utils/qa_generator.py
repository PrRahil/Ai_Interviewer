import os
import hashlib
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnableSequence
from .vector_store import VectorStore

# Load environment variables
load_dotenv()

def generate_title_from_query(query: str) -> str:
    """
    Generate a concise, suitable title for the chat history from the user's query/JD.
    Uses the LLM to summarize the query into a short title (max 8 words).
    """
    try:
        prompt_template = PromptTemplate(
            input_variables=["query"],
            template="""Given the following job description or query, generate a short, clear title (max 8 words) that best represents the role or topic. Do not use generic words like 'Job Description'.

Examples:
Input: 'We are looking for a Frontend Developer with experience in React and TypeScript...'
Title: 'Frontend Developer (React, TypeScript)'

Input: 'Seeking a Data Analyst to work on business intelligence and dashboarding...'
Title: 'Data Analyst - BI & Dashboarding'

Input: 'Cloud Architect with AWS and DevOps experience...'
Title: 'Cloud Architect - AWS DevOps'

Input: '{query}'
Title:"""
        )
        
        llm = ChatOpenAI(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.3,
            model="gpt-3.5-turbo"
        )
        
        chain = LLMChain(llm=llm, prompt=prompt_template)
        title = chain.run(query=query).strip()
        
        # Post-process to ensure title is not too long
        if len(title.split()) > 8:
            title = " ".join(title.split()[:8])
            
        return title if title else "Interview Questions"
        
    except Exception as e:
        print(f"Error generating title: {e}")
        # Fallback: extract key words from query
        words = query.split()[:3]
        return " ".join(words) if words else "Interview Questions"

def create_unique_key(job_role: str, interview_level: str) -> str:
    """Create a unique key for job role and level combination"""
    # Clean and normalize the input
    normalized_role = job_role.strip().lower()
    normalized_level = interview_level.strip().lower()
    
    # Create a hash to ensure uniqueness while keeping it readable
    combined = f"{normalized_role}_{normalized_level}"
    hash_suffix = hashlib.md5(combined.encode()).hexdigest()[:8]
    
    return f"{normalized_role}_{normalized_level}_{hash_suffix}"

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
        # Initialize vector store
        vector_store = VectorStore()
        
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
            openai_api_key=os.getenv("OPENAI_API_KEY")
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

def save_to_history(job_role, qa_content, interview_level="entry", title=None):
    """Save generated Q&A to history file with proper formatting"""
    history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qa_history.json")
    
    entry = {
        "job_role": job_role,
        "title": title if title else job_role[:50] + "..." if len(job_role) > 50 else job_role,
        "content": qa_content,
        "interview_level": interview_level,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        history = []
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            try:
                with open(history_file, "r", encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
        
        history.append(entry)
        
        with open(history_file, "w", encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error saving to history: {e}")
