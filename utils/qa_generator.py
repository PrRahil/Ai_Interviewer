import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from utils.vector_store import get_vectorstore, job_exists, add_job_to_vectorstore


def generate_or_retrieve_qa(job_role: str):
    vectorstore = get_vectorstore()
    existing = job_exists(vectorstore, job_role)
    if existing:
        return existing, True

    prompt_template = PromptTemplate(
        input_variables=["role"],
        template="""
You are an expert tech recruiter.

Generate 5 technical interview questions and ideal answers for the role of: {role}

Format:
Q1: ...
A1: ...
Q2: ...
A2: ...
"""
    )

    llm = ChatOpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7, model="gpt-3.5-turbo")

    chain = LLMChain(llm=llm, prompt=prompt_template)
    result = chain.run(role=job_role)

    add_job_to_vectorstore(job_role, result)
    return result, False
