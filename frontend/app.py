import streamlit as st
import requests
import uuid
from datetime import datetime
from pathlib import Path
import asyncio
import aiohttp
import json
import os
import bcrypt
import logging

# ---- Setup Logging ---- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- Initialization ---- #
st.set_page_config(
    page_title="Asha – Context-Aware Chatbot",
    page_icon="💬",
    layout="wide",
    menu_items={'About': "Asha Chatbot - Empowering Women through AI | JobsForHer Foundation"}
)

# Load external CSS
css_file = "styles.css"
try:
    with open(css_file, "r") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error(f"CSS file '{css_file}' not found. Please ensure it exists in the same directory as this script.")
    st.stop()

# Initial bot greeting
if "chat_history" not in st.session_state or not st.session_state.chat_history:
    st.session_state.chat_history = [("Asha", "Hello! How can I help you with your career development, job opportunities, or finding a mentorship program today? I'm Asha Bot, and I'm here to support you.")]

# ---- User Management ---- #
USER_FILE = "users.json"

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
            return {}
    return {}

def save_users(users):
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {str(e)}")

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ---- Session Setup ---- #
if "user" not in st.session_state:
    st.session_state.user = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "cache" not in st.session_state:
    st.session_state.cache = {}

# ---- Sign-Up/Login Page ---- #
def auth_page():
    st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
    st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
    
    st.markdown("<div class='auth-title'>Asha Chatbot</div>", unsafe_allow_html=True)
    
    # Tab selection for Sign Up / Login
    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "Login"
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", key="login_tab", use_container_width=True):
            st.session_state.auth_tab = "Login"
    with col2:
        if st.button("Sign Up", key="signup_tab", use_container_width=True):
            st.session_state.auth_tab = "Sign Up"
    
    # Apply active class to tabs dynamically
    tab_login_class = "tab active" if st.session_state.auth_tab == "Login" else "tab"
    tab_signup_class = "tab active" if st.session_state.auth_tab == "Sign Up" else "tab"
    st.markdown(f"""
    <style>
        #login_tab .stButton>button {{ width: 100%; }}
        #signup_tab .stButton>button {{ width: 100%; }}
        #login_tab .stButton>button {{ {tab_login_class} }}
        #signup_tab .stButton>button {{ {tab_signup_class} }}
    </style>
    """, unsafe_allow_html=True)
    
    # Auth form
    with st.form("auth_form", clear_on_submit=True):
        st.markdown("<div class='auth-form'>", unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Submit")
        
        if submit and username and password:
            users = load_users()
            
            if st.session_state.auth_tab == "Sign Up":
                if username in users:
                    st.markdown("<div class='error-message'>Username already exists. Please choose another.</div>", unsafe_allow_html=True)
                else:
                    users[username] = {"password": hash_password(password)}
                    save_users(users)
                    st.markdown("<div class='success-message'>Sign-up successful! You can now log in.</div>", unsafe_allow_html=True)
            
            elif st.session_state.auth_tab == "Login":
                if username in users and verify_password(password, users[username]["password"]):
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.markdown("<div class='error-message'>Invalid username or password.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---- Chatbot Page ---- #
def chatbot_page():
    # API endpoints (configurable)
    BASE_API_URL = "http://localhost:8000/api"
    CHAT_ENDPOINT = f"{BASE_API_URL}/chat"
    FEEDBACK_ENDPOINT = f"{BASE_API_URL}/feedback"
    NAUKRI_JOBS_ENDPOINT = f"{BASE_API_URL}/jobs/naukri"

    # Serper search function
    async def search_serper(query: str) -> str:
        top_result_to_return = 4
        url = "https://google.serper.dev/search"
        logger.info(f"Serper query: {query}")
        headers = {
            "X-API-KEY": os.environ.get('SERPER_API_KEY', 'YOUR_SERPER_API_KEY'),,
            "Content-Type": "application/json"
        }
        payload = json.dumps({"q": query, "num": top_result_to_return})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'organic' not in data:
                        result = "Sorry, I couldn't find anything about that. There may be an issue with the Serper API key."
                    else:
                        results = data['organic']
                        string = []
                        for result in results[:top_result_to_return]:
                            try:
                                string.append('\n'.join([
                                    f"Title: {result['title']}",
                                    f"Link: {result['link']}",
                                    f"Snippet: {result['snippet']}",
                                    "\n-----------------"
                                ]))
                            except KeyError:
                                continue
                        result = '\n'.join(string) if string else "No recent updates found."
                    return result
                else:
                    logger.error(f"Serper API error: {response.status}")
                    return f"API error: {response.status}"

    # ---- Sidebar ---- #
    with st.sidebar:
        st.markdown(f"<div class='sidebar-header'>Welcome, {st.session_state.user}!</div>", unsafe_allow_html=True)
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.chat_history = []
            st.rerun()
        
        st.markdown("<div class='sidebar-header'>📝 Feedback</div>", unsafe_allow_html=True)
        with st.form("feedback_form"):
            feedback_text = st.text_area("Share your thoughts or report issues:", height=100)
            submitted = st.form_submit_button("Submit Feedback")
            if submitted and feedback_text:
                try:
                    response = requests.post(
                        FEEDBACK_ENDPOINT,
                        json={
                            "session_id": st.session_state.session_id,
                            "query": feedback_text,
                            "contact_info": None
                        }
                    )
                    if response.status_code == 200:
                        st.success("Thank you for your feedback!")
                    else:
                        st.error("Failed to submit feedback. Please try again.")
                except Exception as e:
                    st.error(f"Error submitting feedback: {str(e)}")

    # ---- Main Interface ---- #
    st.markdown("<div class='chatbot-main'>", unsafe_allow_html=True)
    st.title("💬 Asha – Context-Aware Chatbot")
    st.markdown("<div class='chatbot-caption'>Empowering Women through AI | JobsForHer Foundation</div>", unsafe_allow_html=True)

    # ---- Chat Interface ---- #
    chat_container = st.container()
    with chat_container:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        for sender, msg in st.session_state.chat_history:
            if sender == "You":
                st.markdown(f"<div class='chat-bubble-user'><span>{msg}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble-bot'><span>{msg}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        st.markdown("<div class='chatbot-form'>", unsafe_allow_html=True)
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input(
                "Ask about jobs, events, mentorship, or more...",
                key="user_input",
                label_visibility="collapsed",
                placeholder="Ask about jobs, events, mentorship, or more..."
            )
        with col2:
            submit = st.form_submit_button("Send", use_container_width=True)
        
        contact_info = st.text_input(
            "Email (optional, for follow-ups)",
            key="contact_info",
            help="Provide your email if you'd like us to follow up"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if submit and user_input:
            st.session_state.chat_history.append(("You", user_input))
            with st.spinner("Asha is thinking..."):
                try:
                    response = requests.post(
                        CHAT_ENDPOINT,
                        json={
                            "session_id": st.session_state.session_id,
                            "query": user_input,
                            "contact_info": contact_info or None
                        }
                    )
                    response.raise_for_status()
                    bot_reply = response.json().get("response", "Sorry, I couldn't understand that.")
                    st.session_state.chat_history.append(("Asha", bot_reply))
                    st.rerun()
                except requests.RequestException as e:
                    st.session_state.chat_history.append(("Asha", f"🚫 Error: {str(e)}"))
                    st.rerun()

    # ---- Quick Actions ---- #
    st.subheader("Quick Actions")
    quick_queries = {
        "🔍 Women Empowerment Updates": "Tell me the latest updates on women empowerment from Internet",
        "💼 Job from naukri.com": "Show me current job from `naukri.com`",
        "💼 Job from Herkey.com": "Show me current job from `herkey.com`",
        "📅 Community Events": "What events are coming up?",
        "🗓️ Weekly Sessions": "List the sessions happening this week",
        "📢 Mentorship Programs": "Are there any mentorship programs available?",
        "👩‍💼 Women Leadership Stories": "Share success stories of women in leadership",
        "❓ About Asha Bot": "What is Asha Bot?"
    }

    # Responsive grid for quick actions
    cols = st.columns([1, 1, 1, 1])
    for i, (label, query) in enumerate(quick_queries.items()):
        with cols[i % 4]:
            if st.button(label, key=f"quick_action_{i}", use_container_width=True):
                st.session_state.chat_history.append(("You", query))
                with st.spinner("Asha is thinking..."):
                    try:
                        if label in [
                            "🔍 Women Empowerment Updates",
                            "📅 Community Events",
                            "🗓️ Weekly Sessions",
                            "👩‍💼 Women Leadership Stories"
                        ]:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            bot_reply = loop.run_until_complete(search_serper(query))
                            loop.close()
                        elif label == "💼 Job from naukri.com":
                            response = requests.post(
                                NAUKRI_JOBS_ENDPOINT,
                                json={
                                    "session_id": st.session_state.session_id,
                                    "query": query
                                }
                            )
                            response.raise_for_status()
                            bot_reply = response.json().get("response", "Sorry, I couldn't find any jobs from Naukri.com.")
                        else:
                            response = requests.post(
                                CHAT_ENDPOINT,
                                json={
                                    "session_id": st.session_state.session_id,
                                    "query": query
                                }
                            )
                            response.raise_for_status()
                            bot_reply = response.json().get("response", "Sorry, I couldn't understand that.")
                        
                        st.session_state.chat_history.append(("Asha", bot_reply))
                        st.rerun()
                    except Exception as e:
                        st.session_state.chat_history.append(("Asha", f"🚫 Error: {str(e)}"))
                        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ---- Main Logic ---- #
if st.session_state.user is None:
    auth_page()
else:
    chatbot_page()