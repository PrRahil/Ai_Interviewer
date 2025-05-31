import streamlit as st
from utils.qa_generator import generate_or_retrieve_qa

st.set_page_config(page_title="AI Interview Q&A Generator", layout="centered")

st.title("🎯 AI Interview Q&A Generator (RAG-powered)")
st.write("Enter a job role and get smart interview questions and answers.")

job_role = st.text_input("💼 Job Role", placeholder="e.g., Frontend Developer, Data Analyst")

if st.button("Generate / Retrieve"):
    if job_role.strip():
        with st.spinner("Fetching from DB or generating..."):
            result, from_cache = generate_or_retrieve_qa(job_role)
            if from_cache:
                st.info("✅ Retrieved from previous saved sessions (Vector DB).")
            else:
                st.success("✅ Generated fresh via OpenAI API and stored.")

            st.code(result)

            if st.download_button("💾 Save to file", data=result, file_name=f"{job_role}_QnA.txt"):
                st.toast("Saved for offline use!")
    else:
        st.warning("Please enter a job role.")
