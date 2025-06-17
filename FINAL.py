import streamlit as st
# Page configuration
st.set_page_config(
    page_title="FastTrackHire",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

import PyPDF2
import pdfplumber
import os
import json
from groq import Groq
import pyodbc
import hashlib
from datetime import datetime

# Database configuration 
SERVER = 'SAICHARAN' 
DATABASE = 'FastTrackHire'

# Database connection through pyodbc
def get_db_connection():
    try:
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};'
            f'DATABASE={DATABASE};'
            f'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Database setup
def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        
        # Create users table if not exists
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            email NVARCHAR(255) UNIQUE,
            password NVARCHAR(255),
            full_name NVARCHAR(255),
            created_at DATETIME DEFAULT GETDATE()
        )
        ''')
        
        # Create interview_sessions table if not exists
        cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'interview_sessions')
        CREATE TABLE interview_sessions (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT FOREIGN KEY REFERENCES users(id),
            company NVARCHAR(255),
            resume_text NVARCHAR(MAX),
            chat_history NVARCHAR(MAX),
            feedback NVARCHAR(MAX),
            created_at DATETIME DEFAULT GETDATE()
        )
        ''')
        
        conn.commit()
        conn.close()

init_db()

# Session state initialization
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
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "show_login" not in st.session_state:
    st.session_state.show_login = True
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=st.secrets["GROQ_API_KEY"])


# Enhanced CSS Components
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

    /* Base Styles */
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: var(--text-primary);
    }
    
    /* Header Styles */
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
    
    .header-title {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(45deg, #ffffff, #e0e0e0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }

    /* Authentication Styles */
    .auth-container {
        background: rgba(15, 15, 35, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .auth-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
    }
    
    .auth-header {
        color: #00d4ff;
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
        text-align: center;
        font-weight: 600;
        background: linear-gradient(45deg, #00d4ff, #667eea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .auth-input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 0.8rem 1rem !important;
        color: var(--text-primary) !important;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .auth-input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
    }
    
    .auth-button {
        background: var(--primary-gradient) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem 1.5rem !important;
        width: 100%;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        margin-top: 1rem !important;
    }
    
    .auth-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }
    
    .switch-auth {
        text-align: center;
        margin-top: 1.5rem;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    
    .switch-link {
        color: var(--accent);
        text-decoration: none;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .switch-link:hover {
        text-decoration: underline;
    }

    /* Chat Message Styles */
    .user-message {
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%) !important;
        color: white !important;
        border-radius: 25px 25px 8px 25px;
        margin-left: 10%;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25),
                    0 4px 16px rgba(118, 75, 162, 0.15),
                    inset 0 1px 0 rgba(255,255,255,0.1);
        backdrop-filter: blur(15px);
        padding: 1.8rem 2rem !important;
        position: relative;
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

    /* Sidebar Styles */
    .css-1d391kg {
        background: rgba(15, 15, 35, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    /* Input Container */
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
        z-index: 100;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    /* Responsive Adjustments */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }
        
        .auth-container {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password, full_name):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            hashed_pw = hash_password(password)
            cursor.execute(
                "INSERT INTO users (email, password, full_name) VALUES (?, ?, ?)",
                email, hashed_pw, full_name
            )
            conn.commit()
            return True
        except pyodbc.IntegrityError:
            st.error("Email already exists. Please use a different email.")
            return False
        except Exception as e:
            st.error(f"Error creating user: {str(e)}")
            return False
        finally:
            conn.close()
    return False

def verify_user(email, password):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            hashed_pw = hash_password(password)
            cursor.execute(
                "SELECT id, email, full_name FROM users WHERE email = ? AND password = ?",
                email, hashed_pw
            )
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'full_name': user[2]
                }
            return None
        except Exception as e:
            st.error(f"Error verifying user: {str(e)}")
            return None
        finally:
            conn.close()
    return None

def save_interview_session(user_id, company, resume_text, chat_history, feedback):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO interview_sessions (user_id, company, resume_text, chat_history, feedback) VALUES (?, ?, ?, ?, ?)",
                user_id, company, resume_text, json.dumps(chat_history), feedback
            )
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Error saving interview session: {str(e)}")
            return False
        finally:
            conn.close()
    return False

def get_user_interviews(user_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, company, created_at FROM interview_sessions WHERE user_id = ? ORDER BY created_at DESC",
                user_id
            )
            return cursor.fetchall()
        except Exception as e:
            st.error(f"Error retrieving interviews: {str(e)}")
            return []
        finally:
            conn.close()
    return []

# Header Section
st.markdown(f"""
<div class="header-wrapper">
    <div class="header-content">
        <h1 class="header-title">🚀 FastTrackHire</h1>
        <p style="font-size: 1.2rem; opacity: 0.9; margin: 1rem 0 0 0;">
            Fast-Track Your Way to Success.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# Authentication UI
if not st.session_state.logged_in:
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-top: 2rem;">
        <div style="max-width: 800px; width: 100%;">
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        if st.session_state.show_login:
            with st.container():
                st.markdown("""
                <div class="auth-container fade-in">
                    <div class="auth-header">Welcome Back</div>
                """, unsafe_allow_html=True)
                
                login_email = st.text_input("Email", key="login_email", placeholder="your.email@example.com")
                login_password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
                
                if st.button("Login", key="login_button", type="primary"):
                    user = verify_user(login_email, login_password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_email = user['email']
                        st.session_state.user_id = user['id']
                        st.session_state.full_name = user['full_name']
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                
                st.markdown("""
                <div class="switch-auth">
                    Don't have an account? <span class="switch-link" onclick="switchToSignup()">Sign up</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        if st.session_state.show_signup:
            with st.container():
                st.markdown("""
                <div class="auth-container fade-in">
                    <div class="auth-header">Create Account</div>
                """, unsafe_allow_html=True)
                
                signup_email = st.text_input("Email", key="signup_email", placeholder="your.email@example.com")
                signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="••••••••")
                signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password", placeholder="••••••••")
                signup_full_name = st.text_input("Full Name", key="signup_full_name", placeholder="John Doe")
                
                if st.button("Create Account", key="signup_button", type="primary"):
                    if signup_password != signup_confirm_password:
                        st.error("Passwords don't match")
                    else:
                        if create_user(signup_email, signup_password, signup_full_name):
                            st.success("Account created successfully! Please login.")
                            st.session_state.show_signup = False
                            st.session_state.show_login = True
                            st.rerun()
                
                st.markdown("""
                <div class="switch-auth">
                    Already have an account? <span class="switch-link" onclick="switchToLogin()">Login</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    
    <script>
        function switchToSignup() {
            window.streamlitSessionState.set({show_login: false, show_signup: true});
            window.streamlitSessionState.sync();
        }
        function switchToLogin() {
            window.streamlitSessionState.set({show_login: true, show_signup: false});
            window.streamlitSessionState.sync();
        }
    </script>
    """, unsafe_allow_html=True)
    
    st.stop()

# Main application (only shown if logged in)
st.sidebar.markdown(f"""
<div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div style="width: 40px; height: 40px; background: var(--primary-gradient); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
            {st.session_state.full_name[0].upper()}
        </div>
        <div>
            <div style="font-weight: 600;">{st.session_state.full_name}</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">{st.session_state.user_email}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Logout", type="primary"):
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.user_id = None
    st.session_state.full_name = ""
    st.session_state.show_login = True
    st.session_state.show_signup = False
    st.rerun()

# Chat Container
chat_container = st.container()
with chat_container:
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            bubble_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f'<div class="{bubble_class}">{message["content"]}</div>', 
                        unsafe_allow_html=True)

# PDF processing function
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
with st.sidebar:
    st.markdown("""
    <div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">
        <h3 style="margin-top: 0;">📄 Upload Resume</h3>
    """, unsafe_allow_html=True)
    
    pdf_file = st.file_uploader("Choose your resume (PDF format)", type="pdf", key="resume_uploader", label_visibility="collapsed")
    
    st.markdown("""
    </div>
    <div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">
        <h3 style="margin-top: 0;">🏢 Target Company</h3>
    """, unsafe_allow_html=True)
    
    company_options = ['Select a Company', 'Google', 'Amazon', 'Microsoft', 'Product-Based', 'TCS', 'Infosys', 'Service-based']
    selected_company = st.selectbox('Choose the Company:', company_options, key="company_dropdown", label_visibility="collapsed")
    
    if selected_company != "Select a Company":
        st.session_state.company = selected_company
    
    st.markdown("</div>", unsafe_allow_html=True)

    if pdf_file is not None and selected_company != "Select a Company":
        if st.session_state.current_stage == "pre_start":
            with st.spinner("🔍 Analyzing Resume..."):
                processed_text = process_pdf(pdf_file)

                if processed_text:
                    st.session_state.pdf_text = processed_text
                    st.session_state.current_stage = "interview"
                    st.session_state.question_count = 0
                    st.session_state.chat_history = []
                    st.rerun()
    elif selected_company == "Select a Company":
        st.warning("⚠️ Please select a company before uploading your resume.")

    st.markdown("""
    <div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 12px; margin-bottom: 1.5rem;">
        <h3 style="margin-top: 0;">📝 Interview Instructions</h3>
        <p style="margin: 0; font-size: 0.9rem; line-height: 1.5;">
            💡 <strong>Quick Start:</strong><br>
            • Type <code>hello</code> or <code>Let's Start</code> to begin<br>
            • Answer questions one by one<br>
            • Use the text area for detailed responses<br>
            • Complete all sections for full feedback
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show previous interviews
    with st.expander("📚 Previous Interviews", expanded=False):
        interviews = get_user_interviews(st.session_state.user_id)
        if interviews:
            for interview in interviews:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="font-weight: 600;">{interview[1]}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">
                        {interview[2].strftime('%Y-%m-%d %H:%M')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No previous interviews found")

if not st.session_state.pdf_text:
    st.markdown("""
    <div style="max-width: 800px; margin: 2rem auto; text-align: center;">
        <div style="background: rgba(0, 212, 255, 0.1); padding: 2rem; border-radius: 20px; border: 1px dashed rgba(0, 212, 255, 0.3);">
            <h2 style="margin-top: 0;">⚡ Ready to Start?</h2>
            <p>Please upload your resume and select a company to begin your AI-powered interview experience.</p>
            <div style="font-size: 3rem; margin-top: 1rem;">👨‍💻</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Input Section
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

# Response
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
            # Save the interview session to database
            feedback = "\n".join([msg["content"] for msg in st.session_state.chat_history if msg["role"] == "assistant"])
            save_interview_session(
                st.session_state.user_id,
                st.session_state.company,
                st.session_state.pdf_text,
                st.session_state.chat_history,
                feedback
            )
        
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        st.rerun()
        
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")