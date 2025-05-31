# utils/vector_store.py

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "chroma_db"

def get_vectorstore():
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

def job_exists(vectorstore, job_role):
    docs = vectorstore.similarity_search(job_role, k=1)
    if docs and job_role.lower() in docs[0].page_content.lower():
        return docs[0].page_content
    return None

def add_job_to_vectorstore(job_role, qa_data):
    vectorstore = get_vectorstore()
    metadata = {"job_id": str(uuid.uuid4())}
    vectorstore.add_texts([qa_data], metadatas=[metadata])
    vectorstore.persist()
