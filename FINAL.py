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

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary: #2A3F5F;
        --secondary: #4B6CB7;
        --background: #F8FAFF;
        --text: #0A0000;
    }

    .main {
        background-color: var(--background);
        padding: 2rem;
    }
    
    .header-wrapper {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        color: white;
    }
    
    .user-message {
        background: var(--primary) !important;
        color: white !important;
        border-radius: 15px 15px 0 15px;
        margin-left: 20%;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .assistant-message {
        background: rgba(255,255,255,0.95) !important;
        color: var(--text) !important;
        border-radius: 15px 15px 15px 0;
        margin-right: 20%;
        border: 1px solid rgba(0,0,0,0.1);
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(255,255,255,0.95);
        padding: 1rem;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.05);
    }
    
    .stTextArea textarea {
        border: 2px solid var(--primary) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }

    .celebration-animation {
        animation: celebrate 1s ease;
        background: linear-gradient(45deg, #4CAF50, #81C784);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        font-size: 1.2rem;
        font-weight: bold;
        box-shadow: 0 5px 15px rgba(76,175,80,0.3);
    }

    .rejection-animation {
        animation: reject 1s ease;
        background: linear-gradient(45deg, #f44336, #e57373);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        font-size: 1.2rem;
        font-weight: bold;
        box-shadow: 0 5px 15px rgba(244,67,54,0.3);
    }
    
    @keyframes celebrate {
        0% { transform: scale(0.9); opacity: 0; }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }

    @keyframes reject {
        0% { transform: translateX(-20px); opacity: 0; }
        50% { transform: translateX(20px); }
        100% { transform: translateX(0); opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown(f"""
<div class="header-wrapper">
    <div style="text-align: center;">
        <h1 style="margin: 0; font-size: 2.5rem;">Interview Fever</h1>
</div>
""", unsafe_allow_html=True)



# Chat Container
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            bubble_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f'<div class="{bubble_class}" style="padding: 1.2rem; margin: 1rem 0;">{message["content"]}</div>', 
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



# Sidebar
import re
import streamlit as st

def is_valid_email(email):
    """Validate email format using regex."""
    email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(email_pattern, email) is not None

with st.sidebar:

    st.markdown("### 📄 Upload Resume")
    # Email Input Field
    email = st.text_input("📧 Enter your Email", key="email_input")

    # Resume Upload Section
    pdf_file = st.file_uploader("Upload your resume (PDF)", type="pdf", key="resume_uploader")
    
    company_options = ['Select a Company', 'Google', 'Amazon', 'Microsoft', 'Product-Based', 'TCS', 'Infosys', 'Service-based']
    selected_company = st.selectbox('Choose the Company:', company_options, key="company_dropdown")
    
    if selected_company != "Select a Company":
        st.session_state.company = selected_company


    if pdf_file is not None and email.strip() != "" and selected_company != "Select a Company":
        if is_valid_email(email):
            if st.session_state.current_stage == "pre_start":
                with st.spinner("Analyzing Resume..."):
                    processed_text = process_pdf(pdf_file)

                    if processed_text:
                        st.session_state.pdf_text = processed_text
                        st.session_state.current_stage = "interview"
                        st.session_state.question_count = 0
                        st.session_state.chat_history = []
                        st.session_state.user_email = email  # Store email in session state
                        st.session_state.api_key = GROQ_API_KEY  # Save API key in session state
                        st.rerun()
        else:
            st.error("❌ Please enter a valid email address.")
    elif pdf_file is not None and email.strip() == "":
        st.warning("⚠️ Please enter your email before uploading your resume.")
    elif selected_company == "Select a Company":
        st.warning("⚠️ Please select a company before uploading your resume.")

    st.markdown("### 📝 Interview Instructions")
    st.markdown("""
    Type **`hello`** or **`Let's Start`** to start the interview.  
    Once started, questions will appear one-by-one.  
    Please write your answers in the text area itself provided.
    """)

if not st.session_state.pdf_text:
    st.markdown(
        """
        <div style="
            background-color: #ffcccc; 
            padding: 10px; 
            border-radius: 5px; 
            color: black; 
            font-weight: bold;
            text-align: center;">
            Please upload all the credentials to start the interview.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()

# Input Section
with st.container():
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    user_input = ""
    
    with col1:
        user_input = st.text_area(
            "Type your answer here...", 
            height=120, 
            key="text_input",
            label_visibility="collapsed",
            placeholder="✍️ Type your answer..."
        )
    
    with col2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)        
        if st.button("📤 Submit Answer", use_container_width=True, type="primary") and not st.session_state.interview_complete:
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
        # speak(ai_response)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        
        