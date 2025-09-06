import streamlit as st
import json
import os
from utils.qa_generator import generate_or_retrieve_qa
from datetime import datetime
import time

# Page config with mobile-responsive settings
st.set_page_config(
    page_title="InterGeniX: AI Interviewer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile responsiveness and modern UI
st.markdown("""
<style>
    /* Global styles */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem 0.5rem;
        }
        .stButton > button {
            width: 100%;
            margin: 0.25rem 0;
        }
        .sidebar .sidebar-content {
            width: 100%;
        }
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin: -2rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
    }
    
    /* Input area styling */
    .input-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e9ecef;
        margin: 1rem 0;
    }
    
    .stTextArea textarea {
        min-height: 120px !important;
        border-radius: 10px !important;
        border: 2px solid #e9ecef !important;
        font-size: 16px !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25) !important;
    }
    
    /* Speech buttons */
    .speech-container {
        display: flex;
        gap: 10px;
        margin: 10px 0;
        flex-wrap: wrap;
    }
    
    .speech-btn {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 16px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        min-width: 120px;
    }
    
    .speech-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    }
    
    .speech-btn.recording {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
        animation: pulse 1.5s infinite;
    }
    
    .speech-btn.speaking {
        background: linear-gradient(45deg, #10ac84 0%, #00d2d3 100%);
        animation: pulse 1.5s infinite;
    }
    
    .speech-btn.disabled {
        background: #cccccc;
        cursor: not-allowed;
        transform: none;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    /* Generate button */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 16px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* History items */
    .history-item {
        margin: 0.5rem 0;
        padding: 0.75rem;
        background: white;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .history-item:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    /* Loading spinner */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .response-speech-container {
        margin: 15px 0;
        text-align: center;
    }
    .response-speech-btn {
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
    }
    .response-speech-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .response-speech-btn.speaking {
        background: linear-gradient(45deg, #ff6b6b 0%, #ee5a24 100%);
        animation: pulse 1.5s infinite;
    }
    .voice-status {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    .listening {
        background-color: #ffe6e6;
        color: #d63384;
        border: 1px solid #f5c6cb;
    }
    .speaking {
        background-color: #e6f3ff;
        color: #0066cc;
        border: 1px solid #b8daff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'job_role' not in st.session_state:
    st.session_state.job_role = ""
if 'result' not in st.session_state:
    st.session_state.result = ""
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'from_cache' not in st.session_state:
    st.session_state.from_cache = False
if 'voice_active' not in st.session_state:
    st.session_state.voice_active = False
if 'tts_active' not in st.session_state:
    st.session_state.tts_active = False

# File path for history
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
            json.dump(history, f, indent=2)
    except Exception as e:
        st.sidebar.error(f"Error saving history file: {str(e)}")

# Load history
if 'history' not in st.session_state:
    st.session_state.history = load_history_from_file()

# App header
st.title("🎯 InterGeniX: AI Interviewer")
st.markdown("**Generate personalized interview questions & answers**")

# Job role input
job_role = st.text_area("💼 Job Role / JD", 
                       placeholder="Paste or type job role, JD, or requirements here...", 
                       value=st.session_state.job_role, 
                       height=120)

# Update session state when text changes
if job_role != st.session_state.job_role:
    st.session_state.job_role = job_role

# Voice controls using columns
col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Voice Input", use_container_width=True):
        st.session_state.voice_active = True
        
        # Show listening status
        status_placeholder = st.empty()
        status_placeholder.markdown('<div class="voice-status listening">🎤 Listening... Speak now!</div>', unsafe_allow_html=True)
        
        # Create voice recognition component
        voice_component = st.empty()
        with voice_component.container():
            st.components.v1.html(f"""
            <div id="voice-recognition">
                <script>
                (function() {{
                    if ('webkitSpeechRecognition' in window) {{
                        const recognition = new webkitSpeechRecognition();
                        recognition.lang = 'en-US';
                        recognition.interimResults = false;
                        recognition.maxAlternatives = 1;
                        recognition.continuous = false;
                        
                        recognition.onresult = function(event) {{
                            const transcript = event.results[0][0].transcript;
                            const currentText = `{st.session_state.job_role}`;
                            const newText = currentText ? currentText + ' ' + transcript : transcript;
                            
                            // Update the text area
                            const textareas = parent.document.querySelectorAll('textarea');
                            if (textareas.length > 0) {{
                                textareas[0].value = newText;
                                textareas[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                                textareas[0].dispatchEvent(new Event('change', {{ bubbles: true }}));
                            }}
                            
                            // Send completion signal
                            parent.postMessage({{
                                type: 'voice_complete',
                                transcript: newText
                            }}, '*');
                        }};
                        
                        recognition.onerror = function(event) {{
                            console.error('Speech recognition error:', event.error);
                            parent.postMessage({{
                                type: 'voice_error',
                                error: event.error
                            }}, '*');
                        }};
                        
                        recognition.onend = function() {{
                            parent.postMessage({{
                                type: 'voice_ended'
                            }}, '*');
                        }};
                        
                        recognition.start();
                        
                        // Auto-stop after 10 seconds
                        setTimeout(function() {{
                            recognition.stop();
                        }}, 10000);
                        
                    }} else {{
                        alert('Speech recognition not supported. Please use Chrome browser.');
                        parent.postMessage({{
                            type: 'voice_error',
                            error: 'not_supported'
                        }}, '*');
                    }}
                }})();
                </script>
            </div>
            """, height=50)
        
        # Wait for a moment then clear
        time.sleep(3)
        status_placeholder.empty()
        voice_component.empty()
        st.session_state.voice_active = False

with col2:
    if st.button("🔊 Read Text", use_container_width=True):
        if st.session_state.job_role.strip():
            st.session_state.tts_active = True
            
            # Show speaking status
            status_placeholder = st.empty()
            status_placeholder.markdown('<div class="voice-status speaking">🔊 Reading text...</div>', unsafe_allow_html=True)
            
            # Create TTS component
            tts_component = st.empty()
            with tts_component.container():
                # Clean text for speech
                clean_text = st.session_state.job_role.replace('\n', ' ').replace('"', '\\"').replace("'", "\\'").strip()
                
                st.components.v1.html(f"""
                <div id="text-to-speech">
                    <script>
                    (function() {{
                        if ('speechSynthesis' in window) {{
                            const text = `{clean_text}`;
                            
                            // Cancel any existing speech
                            window.speechSynthesis.cancel();
                            
                            if (text.trim()) {{
                                const utterance = new SpeechSynthesisUtterance(text);
                                utterance.lang = 'en-US';
                                utterance.rate = 0.9;
                                utterance.pitch = 1;
                                
                                utterance.onend = function() {{
                                    parent.postMessage({{
                                        type: 'speech_complete'
                                    }}, '*');
                                }};
                                
                                utterance.onerror = function() {{
                                    parent.postMessage({{
                                        type: 'speech_error'
                                    }}, '*');
                                }};
                                
                                window.speechSynthesis.speak(utterance);
                            }} else {{
                                parent.postMessage({{
                                    type: 'speech_error'
                                }}, '*');
                            }}
                        }} else {{
                            alert('Text-to-speech not supported in this browser.');
                            parent.postMessage({{
                                type: 'speech_error'
                            }}, '*');
                        }}
                    }})();
                    </script>
                </div>
                """, height=50)
            
            # Wait for speech to complete
            time.sleep(5)
            status_placeholder.empty()
            tts_component.empty()
            st.session_state.tts_active = False
        else:
            st.warning("Please enter some text to read aloud.")

# Message listener for JavaScript callbacks
st.components.v1.html("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'voice_complete') {
        console.log('Voice recognition completed:', event.data.transcript);
    } else if (event.data.type === 'voice_error') {
        console.error('Voice recognition error:', event.data.error);
    } else if (event.data.type === 'voice_ended') {
        console.log('Voice recognition ended');
    } else if (event.data.type === 'speech_complete') {
        console.log('Text-to-speech completed');
    } else if (event.data.type === 'speech_error') {
        console.error('Text-to-speech error');
    }
});
</script>
""", height=0)

# Interview level selection
interview_level = st.selectbox("🎚️ Interview Level", 
                              ["entry", "mid", "senior"], 
                              index=0)

# Generate button
col1, col2 = st.columns([3, 1])
with col1:
    if st.button("🚀 Generate Interview Q&A", type="primary", use_container_width=True):
        if st.session_state.job_role.strip():
            with st.spinner("🔄 Generating personalized interview content..."):
                try:
                    result, from_cache, title = generate_or_retrieve_qa(st.session_state.job_role, interview_level)
                    st.session_state.result = result
                    st.session_state.from_cache = from_cache
                    st.session_state.submitted = True
                    
                    # Save to history
                    new_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "job_role": st.session_state.job_role,
                        "interview_level": interview_level,
                        "title": title,
                        "result": result
                    }
                    st.session_state.history.insert(0, new_entry)
                    save_history_to_file(st.session_state.history)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a job role or description first!")

with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.job_role = ""
        st.session_state.result = ""
        st.session_state.submitted = False
        st.rerun()

# Display results with voice controls
if st.session_state.submitted and st.session_state.result:
    if st.session_state.from_cache:
        st.info("Retrieved from previous saved sessions")
    else:
<<<<<<< HEAD
        st.success("Generated new Q/A.")
=======
        st.success("✅ Generated fresh via OpenAI API and stored.")
>>>>>>> 1dbadc4ef07ac45f97c77f6d8657eac023b973a3
    
    # Display the Q&A content
    st.markdown(st.session_state.result)
    
    # Response voice control button
    if st.button("🔊 Read Response"):
        # Show speaking status
        status_placeholder = st.empty()
        status_placeholder.markdown('<div class="voice-status speaking">🔊 Reading response...</div>', unsafe_allow_html=True)
        
        # Create response TTS component
        response_component = st.empty()
        with response_component.container():
            # Clean the result text for speech
            clean_result = st.session_state.result.replace('#', '').replace('*', '').replace('`', '').replace('\n', ' ').replace('"', '\\"').replace("'", "\\'").strip()
            
            st.components.v1.html(f"""
            <div id="response-speech">
                <script>
                (function() {{
                    if ('speechSynthesis' in window) {{
                        const text = `{clean_result}`;
                        
                        // Cancel any existing speech
                        window.speechSynthesis.cancel();
                        
                        if (text.trim()) {{
                            const utterance = new SpeechSynthesisUtterance(text);
                            utterance.lang = 'en-US';
                            utterance.rate = 0.9;
                            utterance.pitch = 1;
                            
                            utterance.onend = function() {{
                                parent.postMessage({{
                                    type: 'response_speech_complete'
                                }}, '*');
                            }};
                            
                            utterance.onerror = function() {{
                                parent.postMessage({{
                                    type: 'response_speech_error'
                                }}, '*');
                            }};
                            
                            window.speechSynthesis.speak(utterance);
                        }} else {{
                            parent.postMessage({{
                                type: 'response_speech_error'
                            }}, '*');
                        }}
                    }} else {{
                        alert('Text-to-speech not supported in this browser.');
                        parent.postMessage({{
                            type: 'response_speech_error'
                        }}, '*');
                    }}
                }})();
                </script>
            </div>
            """, height=50)
        
        # Wait for speech to complete (longer for response)
        time.sleep(8)
        status_placeholder.empty()
        response_component.empty()
    
    # Download button
    if st.download_button("💾 Save to file", 
                        data=st.session_state.result, 
                        file_name=f"{st.session_state.job_role.replace(' ', '_')[:30]}_QnA.md"):
        st.toast("✅ Saved for offline use!")

# Sidebar with history
with st.sidebar:
    st.header("📚 Previous Sessions")
    
    if st.session_state.history:
        if st.button("🗑️ Clear All History", key="clear_history"):
            st.session_state.history = []
            save_history_to_file([])
            st.rerun()
        
        for i, entry in enumerate(st.session_state.history[:10]):  # Show last 10
            with st.expander(f"📝 {entry.get('title', 'Untitled')[:30]}..."):
                st.write(f"**Level:** {entry.get('interview_level', 'N/A')}")
                st.write(f"**Date:** {entry.get('timestamp', 'N/A')[:19]}")
                if st.button(f"Load Session", key=f"load_{i}"):
                    # Properly load the session data
                    st.session_state.job_role = entry.get('job_role', '')
                    st.session_state.result = entry.get('result', '')
                    st.session_state.submitted = True
                    st.session_state.from_cache = True
                    st.rerun()
    else:
        st.write("No previous sessions found.")

# Footer
st.markdown("---")
st.markdown("**🎯 InterGeniX** - AI-Powered Interview Preparation Tool")
