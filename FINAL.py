import PyPDF2
import pdfplumber
import os
import json
import streamlit as st
from groq import Groq

#GROQ_API_KEY = "xai-inmQSGvOzLNSuhoHZrYi4mzZI0OQsFNrMdRf5i0KXCwKXzrYCSdvIFwVxjB937DhGEqY3cZOXWc3SaRL"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "current_stage" not in st.session_state:
    st.session_state.current_stage = "pre_start"
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# Initialize Groq client
GROQ_API_KEY=st.secrets["GROQ_API_KEY"]
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Page configuration
st.set_page_config(
    page_title="FastTrackHire",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS with modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --danger-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        --dark-bg: #0f0f23;
        --card-bg: rgba(255, 255, 255, 0.05);
        --text-primary: #ffffff;
        --text-secondary: #a0a0a0;
        --accent: #00d4ff;
        --border-color: rgba(255, 255, 255, 0.1);
    }

    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1rem 2rem;
        color: var(--text-primary);
    }
    
    .header-wrapper {
        background: var(--primary-gradient);
        border-radius: 24px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .header-wrapper::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="50" cy="10" r="0.5" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
        opacity: 0.3;
    }
    
    .header-content {
        position: relative;
        z-index: 1;
        text-align: center;
    }
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(45deg, #ffffff, #e0e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    .user-message {
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
   color: white !important;
   border-radius: 25px 25px 8px 25px;
   margin-left: 20%;
   margin-bottom: 1.5rem;
   border: 1px solid rgba(255,255,255,0.15);
   box-shadow: 
       0 12px 40px rgba(102, 126, 234, 0.25),
       0 4px 16px rgba(118, 75, 162, 0.15),
       inset 0 1px 0 rgba(255,255,255,0.1);
   backdrop-filter: blur(15px);
   padding: 1.8rem 2rem !important;
   position: relative;
   transform: translateY(0);
   transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   overflow: hidden;
}
    
    .user-message::before {
        content: '👤';
        position: absolute;
        top: -10px;
        right: -10px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    
    .assistant-message {
        background: var(--card-bg) !important;
        color: var(--text-primary) !important;
        border-radius: 20px 20px 20px 5px;
        margin-right: 15%;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.2);
        backdrop-filter: blur(20px);
        padding: 1.5rem !important;
        position: relative;
    }
    
    .assistant-message::before {
        content: '🤖';
        position: absolute;
        top: -10px;
        left: -10px;
        background: var(--success-gradient);
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(15, 15, 35, 0.95);
        backdrop-filter: blur(20px);
        padding: 1.5rem;
        box-shadow: 0 -10px 40px rgba(0,0,0,0.3);
        border-top: 1px solid var(--border-color);
    }
    
    .stTextArea textarea {
        background: var(--card-bg) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
    }
    
    .stTextArea textarea::placeholder {
        color: var(--text-secondary) !important;
    }

    .celebration-animation {
        animation: celebrate 1.5s ease;
        background: var(--success-gradient);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 15px 35px rgba(79, 172, 254, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .celebration-animation::before {
        content: '🎉';
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 2rem;
        animation: bounce 2s infinite;
    }

    .rejection-animation {
        animation: reject 1.5s ease;
        background: var(--danger-gradient);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin: 2rem 0;
        font-size: 1.3rem;
        font-weight: 600;
        box-shadow: 0 15px 35px rgba(250, 112, 154, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .rejection-animation::before {
        content: '💔';
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 2rem;
        animation: shake 2s infinite;
    }
    
    @keyframes celebrate {
        0% { transform: scale(0.8) rotate(-5deg); opacity: 0; }
        50% { transform: scale(1.05) rotate(2deg); }
        100% { transform: scale(1) rotate(0deg); opacity: 1; }
    }

    @keyframes reject {
        0% { transform: translateX(-30px) rotate(-3deg); opacity: 0; }
        25% { transform: translateX(30px) rotate(3deg); }
        50% { transform: translateX(-15px) rotate(-1deg); }
        75% { transform: translateX(15px) rotate(1deg); }
        100% { transform: translateX(0) rotate(0deg); opacity: 1; }
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: rgba(15, 15, 35, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    .css-1d391kg .stMarkdown {
        color: var(--text-primary) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .stFileUploader > div {
        background: var(--card-bg) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--accent) !important;
        background: rgba(0, 212, 255, 0.05) !important;
    }
    
    .stTextInput > div > div > input {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.2) !important;
    }
    
    .stButton > button {
        background: var(--primary-gradient) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Warning and Error Messages */
    .element-container .stAlert {
        background: var(--card-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    /* Chat Message Spacing */
    .stChatMessage {
        margin: 1.5rem 0 !important;
    }
    
    /* Custom Warning Box */
    .warning-box {
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #ffc107;
        font-weight: 500;
        text-align: center;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Enhanced Header Section
st.markdown(f"""
<div class="header-wrapper">
    <div class="header-content">
        <h1 class="header-title">🚀 Interview Fever</h1>
        <p style="font-size: 1.2rem; opacity: 0.9; margin: 1rem 0 0 0;">
            AI-Powered Technical Interview Platform
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Chat Container
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            bubble_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f'<div class="{bubble_class}">{message["content"]}</div>', 
                        unsafe_allow_html=True)

def process_pdf(file):
    if file.size > 5_000_000:
        st.error("File size too large (max 5MB)")
        return None
    
    pdf_text = ""
    
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                pdf_text += page_text + "\n"
    except Exception as e:
        st.error(f"PyPDF2 Error: {str(e)}")
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pdf_text += page_text + "\n"
        except Exception as e:
            st.error(f"PDF Processing Failed: {str(e)}")
            return None
    
    pdf_text = " ".join(pdf_text.split())
    pdf_text = pdf_text.replace("\x00", "")
    
    try:
        pdf_text = pdf_text.encode('utf-8', 'ignore').decode()
    except UnicodeDecodeError:
        pdf_text = pdf_text.encode('ascii', 'ignore').decode()
    
    if len(pdf_text.strip()) < 100:
        st.error("This appears to be a scanned PDF. Please upload a text-based PDF.")
        return None
    
    required_keywords = ["experience", "skills", "education"]
    if not any(kw in pdf_text.lower() for kw in required_keywords):
        st.error("Invalid resume format: Missing key sections")
        return None
    
    return pdf_text

# Enhanced Sidebar
import re
import streamlit as st

def is_valid_email(email):
    """Validate email format using regex."""
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_pattern, email) is not None

with st.sidebar:
    st.markdown("### 📧 Contact Information")
    email = st.text_input("Enter your Email", key="email_input", placeholder="your.email@example.com")
    
    st.markdown("### 📄 Upload Resume")
    pdf_file = st.file_uploader("Choose your resume (PDF format)", type="pdf", key="resume_uploader")
    
    st.markdown("### 🏢 Target Company")
    company_options = ['Select a Company', 'Google', 'Amazon', 'Microsoft', 'Product-Based', 'TCS', 'Infosys', 'Service-based']
    selected_company = st.selectbox('Choose the Company:', company_options, key="company_dropdown")
    
    if selected_company != "Select a Company":
        st.session_state.company = selected_company

    if pdf_file is not None and email.strip() != "" and selected_company != "Select a Company":
        if is_valid_email(email):
            if st.session_state.current_stage == "pre_start":
                with st.spinner("🔍 Analyzing Resume..."):
                    processed_text = process_pdf(pdf_file)

                    if processed_text:
                        st.session_state.pdf_text = processed_text
                        st.session_state.current_stage = "interview"
                        st.session_state.question_count = 0
                        st.session_state.chat_history = []
                        st.session_state.user_email = email
                        st.session_state.api_key = GROQ_API_KEY
                        st.rerun()
        else:
            st.error("❌ Please enter a valid email address.")
    elif pdf_file is not None and email.strip() == "":
        st.warning("⚠️ Please enter your email before uploading your resume.")
    elif selected_company == "Select a Company":
        st.warning("⚠️ Please select a company before uploading your resume.")

    st.markdown("### 📝 Interview Instructions")
    st.markdown("""
    <div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 12px; border: 1px solid rgba(0, 212, 255, 0.2);">
        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5;">
            💡 <strong>Quick Start:</strong><br>
            • Type <code>hello</code> or <code>Let's Start</code> to begin<br>
            • Answer questions one by one<br>
            • Use the text area for detailed responses<br>
            • Complete all sections for full feedback
        </p>
    </div>
    """, unsafe_allow_html=True)

if not st.session_state.pdf_text:
    st.markdown("""
        <div class="warning-box">
            <h3 style="margin: 0 0 1rem 0;">⚡ Ready to Start?</h3>
            <p style="margin: 0;">Please upload your credentials above to begin your AI-powered interview experience.</p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# Enhanced Input Section
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    user_input = ""
    
    with col1:
        user_input = st.text_area(
            "Type your answer here...", 
            height=100, 
            key="text_input",
            label_visibility="collapsed",
            placeholder="✍️ Share your thoughts, code, or detailed explanation here..."
        )
    
    with col2:
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)        
        if st.button("🚀 Submit Answer", use_container_width=True, type="primary") and not st.session_state.interview_complete:
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.question_count += 1
                st.session_state.progress = min(st.session_state.question_count * 20, 100)

# Generate AI Response
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user" and not st.session_state.interview_complete:
    prompt = f"""
You are an interviewer from **{st.session_state.company}** conducting a technical interview.

## Candidate Resume:
{st.session_state.pdf_text}

---

**Instructions:**
Only give the feedback after the interview if the candidate ask the feedback before completion tell that you need to complete the interview to give the feedback.

1. Greet the candidate by name, extracted from the resume.
2. Start the interview by asking **3 DSA questions** at the level typically asked by {st.session_state.company}, focusing on the most commonly asked DSA problems by the {st.session_state.company} and make sure the questions must be medium-hard.
3. Ask **only one question at a time**, waiting for the candidate's response before proceeding to the next and if cnadidate's response is like I don't know skip to next quesiton.
4. After the DSA questions, ask **5 to 6 very in-depth questions based on the candidate's resume**.
5. Once all questions are completed, provide a **summary feedback**, including:
   - Overall performance
   - Strengths
   - Areas for improvement
   
6. Maintain a natural, conversational style as if you are an actual {st.session_state.company} interviewer.

**Do not** ask multiple questions in one turn.

---

"""
    
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": prompt},
                *st.session_state.chat_history
            ]
        )
        ai_response = response.choices[0].message.content
        
        if any(phrase in ai_response.lower() for phrase in ["you are selected", "not selected"]):
            st.session_state.interview_complete = True
        
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")        
        
        