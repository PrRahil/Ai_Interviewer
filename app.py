import streamlit as st
from utils.qa_generator import generate_or_retrieve_qa
import json 
import os
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="AI Interview Q&A Generator", layout="centered")


HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa_history.json')


def load_history_from_file():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.sidebar.error(f"Error loading history file: {str(e)}")
    return []


def save_history_to_file(history):
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except Exception as e:
        st.sidebar.error(f"Error saving history file: {str(e)}")

if "history" not in st.session_state:
    
    file_history = load_history_from_file()
    if file_history:
        st.session_state.history = file_history
    else:
        st.session_state.history = []
        
        try:
            get_history_js = """
            var stored = localStorage.getItem('qa_history');
            if (stored) {
                return stored;
            }
            return '';
            """
            stored_history = streamlit_js_eval(js_expressions=get_history_js, key='get_history', wait_for_result=True)
            
            if stored_history and stored_history != '':
                st.session_state.history = json.loads(stored_history)
                save_history_to_file(st.session_state.history)
        except Exception as e:
            st.sidebar.error(f"Could not load history: {str(e)}")
            st.session_state.history = []


def save_history_to_storage():
    try:
        save_history_to_file(st.session_state.history)
        
        history_json = json.dumps(st.session_state.history)
        history_json = history_json.replace("'", "\\'")
        save_js = f"""
        localStorage.setItem('qa_history', '{history_json}');
        return true;
        """
        streamlit_js_eval(js_expressions=save_js, key=f'save_history_{len(st.session_state.history)}')
    except Exception as e:
        st.sidebar.error(f"Could not save history: {str(e)}")

st.sidebar.title("📜 History")

def load_history_item(index):
    job_role, result = st.session_state.history[index]
    st.session_state.job_role = job_role
    st.session_state.result = result
    st.session_state.from_cache = True
    st.session_state.submitted = True

def clear_history():
    st.session_state.history = []
    save_history_to_file([])
    clear_js = """
    localStorage.removeItem('qa_history');
    return true;
    """
    streamlit_js_eval(js_expressions=clear_js, key='clear_history')
    st.sidebar.success("History cleared!")

if st.session_state.history:
    for i, (job_role, _) in enumerate(st.session_state.history):
        st.sidebar.button(
            f"🔍 {job_role}",
            key=f"history_{i}",
            on_click=load_history_item,
            args=(i,)
        )
    
    st.sidebar.button("🗑️ Clear History", on_click=clear_history, type="primary")
else:
    st.sidebar.info("No history yet. Generate some Q&As to see them here!")

st.title("🎯 AI Interview Q&A Generator (RAG-powered)")
st.write("Enter a job role and get smart interview questions and answers.")

if "job_role" not in st.session_state:
    st.session_state.job_role = ""
if "result" not in st.session_state:
    st.session_state.result = ""
if "from_cache" not in st.session_state:
    st.session_state.from_cache = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False

job_role = st.text_input("💼 Job Role", 
                         placeholder="e.g., Frontend Developer, Data Analyst",
                         value=st.session_state.job_role)

def generate_qa():
    st.session_state.job_role = job_role
    st.session_state.submitted = True
    
    with st.spinner("Fetching from DB or generating..."):
        result, from_cache = generate_or_retrieve_qa(job_role)
        st.session_state.result = result
        st.session_state.from_cache = from_cache
        
        history_roles = [item[0] for item in st.session_state.history]
        if job_role.strip() and job_role not in history_roles:
            st.session_state.history.append((job_role, result))
            save_history_to_storage()

if st.button("Generate / Retrieve"):
    if job_role.strip():
        generate_qa()
    else:
        st.warning("Please enter a job role.")

if st.session_state.submitted and st.session_state.result:
    if st.session_state.from_cache:
        st.info("✅ Retrieved from previous saved sessions (Vector DB).")
    else:
        st.success("✅ Generated fresh via OpenAI API and stored.")

    st.code(st.session_state.result)

    if st.download_button("💾 Save to file", 
                         data=st.session_state.result, 
                         file_name=f"{st.session_state.job_role}_QnA.txt"):
        st.toast("Saved for offline use!")
