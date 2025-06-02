import os
import json
from datetime import datetime
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from utils.vector_store import get_vectorstore, job_exists, add_job_to_vectorstore


def generate_or_retrieve_qa(job_role: str, interview_level="entry"):
    """
    Generate or retrieve Q&A for a job role with specified interview level.
    
    Args:
        job_role: The job role to generate questions for
        interview_level: Level of interview difficulty (entry, mid, senior)
        
    Returns:
        Tuple of (qa_content, is_existing)
    """
    vectorstore = get_vectorstore()
    existing = job_exists(vectorstore, job_role)
    if existing:
        return existing, True

    interview_level_info = {
        "entry": {
            "description": "Entry-level (0-2 years of experience, SDE-1)",
            "difficulty": "Focus on fundamentals, basic implementation, and understanding of core concepts. Include straightforward coding questions.",
            "depth": "Questions should test fundamental knowledge and basic problem-solving abilities."
        },
        "mid": {
            "description": "Mid-level (3-5 years of experience, SDE-2)",
            "difficulty": "Include questions on system design, optimization, and deeper technical knowledge. Questions should explore trade-offs and best practices.",
            "depth": "Questions should test both breadth and depth of knowledge, practical experience, and ability to make technical decisions."
        },
        "senior": {
            "description": "Senior-level (5+ years of experience, SDE-3 or higher)",
            "difficulty": "Focus on complex system design, architecture decisions, and leadership aspects. Include questions about scaling, performance, and technical strategy.",
            "depth": "Questions should test advanced knowledge, experience with complex systems, technical leadership, and strategic thinking."
        }
    }
    
    level_info = interview_level_info.get(interview_level, interview_level_info["entry"])
    
    prompt_template = PromptTemplate(
        input_variables=["role", "level_description", "difficulty", "depth"],
        template="""
You are a senior technical interviewer with 15+ years of experience in the tech industry.

Generate 5 in-depth technical interview questions and detailed model answers for a {role} position at {level_description} level.
{difficulty}

Focus on industry best practices, real-world scenarios, and practical knowledge.

Questions should:
- Test both theoretical understanding and practical application
- Include a mix of fundamental concepts and advanced topics
- Cover relevant frameworks, tools, and technologies specific to the role
- Include at least one problem-solving or coding question
- Include at least one system design or architecture question (appropriate for the level)

Answers should:
- Be comprehensive and technically precise
- Include examples where appropriate
- Highlight best practices and common pitfalls
- Demonstrate deep domain knowledge

{depth}

Make the content highly technical and reflective of current industry standards as of 2025.

Format your response in rich markdown, including:
- Properly formatted headings for each question
- Code blocks with appropriate syntax highlighting
- Bullet points for key concepts
- Bold text for important terms
- Tables where appropriate
- Indented paragraphs for clarity
"""
    )

    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.5,  
        model="gpt-3.5-turbo"  
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.run(
        role=job_role, 
        level_description=level_info["description"],
        difficulty=level_info["difficulty"],
        depth=level_info["depth"]
    )
    
    add_job_to_vectorstore(job_role, result)
    
    save_to_history(job_role, result, interview_level)
    
    return result, False


def save_to_history(job_role, qa_content, interview_level="entry"):
    """Save generated Q&A to history file with proper indentation"""
    history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "qa_history.json")
    
    entry = {
        "job_role": job_role,
        "content": qa_content,
        "interview_level": interview_level,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        history = []
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                history = []
        
        history.append(entry)
        
        with open(history_file, "w") as f:
            json.dump(history, f, indent=2)
            
    except Exception as e:
        print(f"Error saving to history: {e}")
