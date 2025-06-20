import streamlit as st
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import hashlib
from datetime import datetime
import pdfplumber
from groq import Groq
import os
import base64

def load_css():
    st.markdown("""
    <style>
        /* Global styles */
        .stApp {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: #e2e8f0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            overflow-x: hidden;
        }

        /* Header styles */
        .header {
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            color: white;
            padding: 3rem 2rem;
            border-radius: 0 0 30px 30px;
            margin-bottom: 2.5rem;
            box-shadow: 0 12px 32px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 1;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotateGlow 10s linear infinite;
            z-index: -1;
        }

        .header h1 {
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #ffffff, #a5b4fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.3rem;
            opacity: 0.9;
            font-weight: 300;
        }

        /* Card styles */
        .card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            transition: transform 0.4s ease, box-shadow 0.4s ease;
        }

        .card:hover {
            transform: translateY(-10px);
            box-shadow: 0 16px 40px rgba(0,0,0,0.2);
        }

        /* Button styles */
        .stButton>button {
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            color: white;
            border: none;
            border-radius: 14px;
            padding: 1rem 2rem;
            font-weight: 700;
            font-size: 1.1rem;
            transition: all 0.3s ease;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(124, 58, 237, 0.4);
            background: linear-gradient(135deg, #6d28d9 0%, #2563eb 100%);
        }

        /* Chat container */
        .chat-container {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(8px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* Chat bubbles */
        .user-bubble {
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            color: white;
            border-radius: 20px 20px 0 20px;
            padding: 1.2rem 1.8rem;
            margin: 0.8rem 1.5rem;
            margin-left: 30%;
            box-shadow: 0 6px 16px rgba(124, 58, 237, 0.3);
            max-width: 65%;
            word-wrap: break-word;
            animation: slideInRight 0.4s ease-out;
            font-size: 1rem;
        }

        .assistant-bubble {
            display: flex;
            align-items: center;
            background: rgba(255,255,255,0.05);
            color: #e2e8f0;
            border-radius: 20px 20px 20px 0;
            padding: 1.2rem 1.8rem;
            margin: 0.8rem 1.5rem;
            margin-right: 30%;
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.1);
            max-width: 65%;
            word-wrap: break-word;
            animation: slideInLeft 0.4s ease-out;
            font-size: 1rem;
        }

        /* Chat icons */
        .chat-icon {
            font-size: 1.5rem;
            margin-right: 1rem;
            flex-shrink: 0;
        }

        .user-bubble .chat-icon {
            color: #ffffff;
        }

        .assistant-bubble .chat-icon {
            color: #a5b4fc;
        }

        /* Sidebar styles */
        [data-testid="stSidebar"] {
            background: linear-gradient(135deg, #1e293b 0%, #2d3748 100%) !important;
            color: #e2e8f0 !important;
            padding-top: 1.5rem;
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        .sidebar-profile {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 2.5rem;
            border-radius: 20px;
            margin: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        .sidebar-profile-avatar {
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            border-radius: 50%;
            margin: 0 auto 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            color: white;
            font-weight: 800;
            box-shadow: 0 6px 16px rgba(124, 58, 237, 0.3);
            border: 2px solid rgba(255,255,255,0.2);
        }

        /* Input styles */
        .stTextInput>div>div>input, .stChatInput>div>textarea {
            border-radius: 14px !important;
            padding: 14px 20px !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            background: rgba(255,255,255,0.05) !important;
            color: #e2e8f0 !important;
            transition: all 0.3s ease;
            font-size: 1rem;
        }

        .stTextInput>div>div>input:focus, .stChatInput>div>textarea:focus {
            border-color: #7c3aed !important;
            box-shadow: 0 0 12px rgba(124, 58, 237, 0.3) !important;
            background: rgba(255,255,255,0.1) !important;
        }

        /* Wide chat input */
        .stChatInput {
            width: 100% !important;
            max-width: 1200px !important;
            margin: 0 auto !important;
        }

        .stChatInput>div>textarea {
            width: 100% !important;
            min-width: 800px !important;
            max-width: 100% !important;
        }

        /* Selectbox styles */
        .stSelectbox>div>div>select {
            border-radius: 14px !important;
            padding: 14px 20px !important;
            background: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            color: #e2e8f0 !important;
            font-size: 1rem;
        }

        /* Progress bar */
        .stProgress>div>div>div {
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%) !important;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.05);
        }

        /* Animations */
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }

        @keyframes rotateGlow {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .fade-in {
            animation: fadeIn 0.6s ease-out forwards;
        }

        /* Instructions card */
        .instructions-card {
            background: rgba(255,255,255,0.08);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(255,255,255,0.1);
            font-size: 0.95rem;
            line-height: 1.6;
            color: #cbd5e1;
        }

        .instructions-card h4 {
            color: #a5b4fc;
            margin-bottom: 0.8rem;
            font-size: 1.1rem;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Session States
def init_session_state():
    session_vars = {
        "chat_history": [],
        "progress": 0,
        "question_count": 0,
        "interview_complete": False,
        "current_stage": "pre_start",
        "pdf_text": "",
        "logged_in": False,
        "user_email": "",
        "show_login": True,
        "show_signup": False,
        "user_id": None,
        "full_name": "",
        "company": "",
        "resume_uploaded": False
    }
    for key, value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# Hardcoded because lot of issues during deployment 
# IF THERE ARE NO PROBLEMS DURING DEPLOYMENT KEEP
# IT IN THE SECRETS FILE 
MONGO_URI = "mongodb+srv://suggalasaicharan789:Saicharan-18@cluster0.zpo87.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "FastTrackHire"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

def get_db_connection():
    try:
        client.admin.command('ping')
        db = client[DB_NAME]
        return db
    except ConnectionFailure as e:
        st.error(f"🔌 Connection Error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"⚠️ Database Error: {str(e)}")
        return None

def init_db():
    db = get_db_connection()
    if db is not None:
        try:
            db.users.create_index("email", unique=True)
            db.interview_sessions.create_index("user_id")
            db.interview_sessions.create_index("created_at")
            return True
        except Exception as e:
            st.error(f"🔧 Setup Error: {str(e)}")
            return False
    return False

def save_interview_session(user_id, company, resume_text, chat_history, feedback):
    db = get_db_connection()
    if db is None:
        return False
    try:
        session_data = {
            "user_id": user_id,
            "company": company,
            "resume_text": resume_text,
            "chat_history": chat_history,
            "feedback": feedback,
            "created_at": datetime.utcnow()
        }
        result = db.interview_sessions.insert_one(session_data)
        return result.inserted_id is not None
    except Exception as e:
        st.error(f"💾 Error saving interview session: {str(e)}")
        return False


if not init_db():
    st.error("🚨 Failed to initialize database. Please check your MONGO_URI settings in the deployment environment.")
    st.stop()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password, full_name):
    db = get_db_connection()
    if db is None:
        return False
    
    try:
        user_data = {
            "email": email,
            "password": hash_password(password),
            "full_name": full_name,
            "created_at": datetime.utcnow()
        }
        result = db.users.insert_one(user_data)
        return result.inserted_id is not None
    except DuplicateKeyError:
        st.error("📧 Email already exists. Please use a different email.")
        return False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return False

def verify_user(email, password):
    db = get_db_connection()
    if db is None:
        return None
    
    try:
        user = db.users.find_one({
            "email": email,
            "password": hash_password(password)
        })
        return user
    except Exception as e:
        st.error(f"🔐 Error: {str(e)}")
        return None


def process_pdf(file):
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        return text if len(text) > 100 else None
    except Exception as e:
        st.error(f"📄 Error processing PDF: {str(e)}")
        return None

if not st.session_state.logged_in:
    st.markdown("""
    <div class="header">
        <h1>🚀 FastTrackHire</h1>
        <p>Your AI-powered interview coach</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")
    
    # Login
    with col1:
        if st.session_state.show_login:
            with st.container():
                st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
                st.markdown('<h3 style="text-align: center; color: #a5b4fc;">🔒 Login</h3>', unsafe_allow_html=True)
                
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email", placeholder="your.email@example.com")
                    password = st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
                    
                    if st.form_submit_button("Login", type="primary"):
                        user = verify_user(email, password)
                        if user:
                            st.session_state.logged_in = True
                            st.session_state.user_id = str(user["_id"])
                            st.session_state.user_email = user["email"]
                            st.session_state.full_name = user["full_name"]
                            st.rerun()
                        else:
                            st.error("Invalid email or password")
                
                if st.button("Create an Account", key="signup_button"):
                    st.session_state.show_login = False
                    st.session_state.show_signup = True
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Signup 
    with col2:
        if st.session_state.show_signup:
            with st.container():
                st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
                st.markdown('<h3 style="text-align: center; color: #a5b4fc;">✨ Create Account</h3>', unsafe_allow_html=True)
                
                with st.form("signup_form"):
                    email = st.text_input("Email", key="signup_email", placeholder="your.email@example.com")
                    password = st.text_input("Password", type="password", key="signup_password", placeholder="••••••••")
                    confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="••••••••")
                    full_name = st.text_input("Full Name", key="signup_name", placeholder="John Doe")
                    
                    if st.form_submit_button("Sign Up", type="primary"):
                        if password != confirm_password:
                            st.error("Passwords don't match")
                        elif not all([email, password, full_name]):
                            st.error("All fields are required")
                        else:
                            if create_user(email, password, full_name):
                                st.success("Account created successfully! Please login.")
                                st.session_state.show_signup = False
                                st.session_state.show_login = True
                                st.rerun()
                
                if st.button("Back to Login", key="back_to_login"):
                    st.session_state.show_signup = False
                    st.session_state.show_login = True
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# Main Application  will be loaded after Login

# Sidebar for taking inputs(i.e Resume,Target Company)
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-profile">
        <div class="sidebar-profile-avatar">
            {st.session_state.full_name[0].upper() if st.session_state.full_name else '?'}
        </div>
        <h3>{st.session_state.full_name}</h3>
        <p style="color: rgba(255,255,255,0.7);">{st.session_state.user_email}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🛠️ Interview Setup")
    
    uploaded_file = st.file_uploader("📄 Upload Resume (PDF)", type="pdf", key="resume_upload")
    if uploaded_file and not st.session_state.resume_uploaded:
        with st.spinner("🔍 Analyzing resume..."):
            processed_text = process_pdf(uploaded_file)
            if processed_text:
                st.session_state.pdf_text = processed_text
                st.session_state.resume_uploaded = True
                st.success("✅ Resume processed successfully!")
    
    company = st.selectbox(
        "🏢 Select Target Company",
        ["Select a company", "Google", "Amazon", "Microsoft", "Apple", "Meta", "Netflix", "Other"],
        key="company_select"
    )
    if company != "Select a company":
        st.session_state.company = company
    
    # Interview Instructions in the side bar
    st.markdown("""
    <div class="instructions-card fade-in">
        <h4>📋 Interview Instructions</h4>
        <ul style="margin: 0; padding-left: 1.2rem;">
            <li>Upload your resume in PDF format.</li>
            <li>Select a target company to tailor the interview.</li>
            <li>Answer one question at a time in the chat below.</li>
            <li>Type "Hello" or "Let's Start" to start the interview.</li>
            <li>Say "I don't know" to skip a question.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Main Content Area i.e Chat Interface for Interview
st.markdown(f"""
<div class="header">
    <h1>👨‍💻 FastTrackHire</h1>
    <p>Fast-track your hiring process with AI-powered mock interviews.</p>
</div>
""", unsafe_allow_html=True)

# Chat Interface contains user input and chat history
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-bubble">
                <span class="chat-icon">🧑</span>
                <span>{message["content"]}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-bubble">
                <span class="chat-icon">🤖</span>
                <span>{message["content"]}</span>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Input will be taken here
if st.session_state.resume_uploaded and st.session_state.company != "Select a company":
    user_input = st.chat_input("💬 Type your response here...", key="chat_input")
    
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.question_count += 1
        
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
3. Ask **only one question at a time**, waiting for the candidate's response before proceeding to the next and if candidate's response is like I don't know skip to next question.
4. After the DSA questions, ask **3 to 4 very in-depth questions based on the candidate's resume**.
5. Once all questions are completed, provide a **summary feedback**, including:
   - Overall performance
   - Strengths
   - Areas for improvement
   
6. Maintain a natural, conversational style as if you are an actual {st.session_state.company} interviewer.

**Do not** ask multiple questions in one turn.

---
"""
            try:
                groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
                response = groq_client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[
                        {"role": "system", "content": prompt},
                        *[{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]
                    ],
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
                
                # Check if interview is complete (contains selection-related phrases)
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
                st.error(f"🤖 Error generating response: {str(e)}")
else:
    st.warning("⚠️ Please upload your resume and select a company to start the interview.", icon="⚠️")
    
    