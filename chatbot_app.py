# ====================================================
# 🤖 AI Customer Support Chatbot (Gemini + Streamlit)
# ====================================================

import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

# ====================================================
# 🔐 Gemini Configuration
# ====================================================

# Set your Gemini API Key (recommended: from environment variable)
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error(" GEMINI_API_KEY is missing. Please set it in environment variables.")
    st.stop()
client = genai.Client(api_key=API_KEY)

# ====================================================
# 🧠 Chatbot Logic
# ====================================================

def get_ai_response(user_message: str) -> str:
    """Generate AI response using Gemini model."""
    try:
        if not user_message.strip():
            return "Please type a message so I can help you."

        if len(user_message) > 1000:
            return "Your message is too long. Please shorten it."

        # Configure system behavior
        config = types.GenerateContentConfig(
            system_instruction=(
                "You are a polite and friendly AI customer service chatbot for a company that teaches you how to prepare food. "
                "You help users with questions about recpies, accounts, cooking. "
                "If unsure, politely suggest contacting human support by sending mail at xyx@gmail.com "
                "Keep responses short and professional."
            )
        )

        # Get response from Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=config,
            contents=user_message,
        )

        return response.text or "I'm not sure how to respond to that."

    except Exception as e:
        print("Error:", e)
        return "Sorry, something went wrong. Please try again later."

# ====================================================
# 💬 Streamlit Chat UI
# ====================================================

st.set_page_config(page_title="customer service", page_icon="💬")
st.markdown(
    """
    <style>
    body {
        background-color: #F9FAFB;
    }
    .user-bubble {
        background-color: #DCF8C6;
        color: #000000;
        padding: 10px 15px;
        border-radius: 12px;
        margin: 8px 0;
        width: fit-content;
        max-width: 80%;
        margin-left: auto;
    }
    .bot-bubble {
        background-color: #E6E6E6;
        color: #000000;
        padding: 10px 15px;
        border-radius: 12px;
        margin: 8px 0;
        width: fit-content;
        max-width: 80%;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💬 Food Customer Service Bot")
st.caption(" Ask about your cooking doubts, accounts, diet!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        ("🤖 Vedant", "Hello! 👋 How can I help you today?")
    ]

user_message = st.chat_input("Type your question here...")

if user_message:
    ai_reply = get_ai_response(user_message)
    st.session_state.chat_history.append(("👤 You", user_message))
    st.session_state.chat_history.append(("🤖 Vedant", ai_reply))

# Display chat history
for role, msg in st.session_state.chat_history:
    if role == "👤 You":
        st.markdown(f"<div class='user-bubble'><b>{role}:</b> {msg}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='bot-bubble'><b>{role}:</b> {msg}</div>", unsafe_allow_html=True)

# Clear chat
if st.button("🧹 Clear Chat"):
    st.session_state.chat_history = [("🤖 Vedant", "Hello! 👋 How can I help you today?")]
    st.success("Chat cleared!")