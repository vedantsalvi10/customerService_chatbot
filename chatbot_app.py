# ====================================================
# 🤖 Food Customer Service Chatbot (OpenAI v1 SDK + Streamlit + Tool Calling)
# ====================================================

import os
import streamlit as st
import json
from dotenv import load_dotenv
from exa_py import Exa
from openai import OpenAI  # New v1 SDK client

load_dotenv()

# ====================================================
# 🔐 OpenAI & EXA Setup
# ====================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

if not OPENAI_API_KEY or not EXA_API_KEY:
    st.error("Missing OPENAI_API_KEY or EXA_API_KEY in environment variables.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize EXA client
exa = Exa(api_key=EXA_API_KEY)

# ====================================================
# 🛠 Tool definition for function calling
# ====================================================
TOOLS = [
    {
        "name": "search_recipes",
        "description": "Search the web for top recipes or food recommendations using Exa search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query to perform"},
                "num_results": {"type": "integer", "description": "Number of results to return", "default": 5},
            },
            "required": ["query"],
        },
    }
]

# ====================================================
# 🧠 EXA search function
# ====================================================
def search_recipes_tool(query, num_results = 5):
    results = exa.search_and_contents(query, num_results=num_results,highlights=True)
    return [{"title": r.title, "url": r.url, "content": r.highlights} for r in results.results]

# ====================================================
# 🧠 AI response with function calling
# ====================================================
def get_ai_response(user_message):
    if not user_message.strip():
        return "Please type a message so I can help you."

    # Build conversation history
    messages = [
        {"role": "system", "content": "You are a polite AI helping users with recipes and cooking questions."}
    ]
    if "chat_history" in st.session_state:
        for role, msg in st.session_state.chat_history:
            messages.append({"role": "user" if role=="👤 You" else "assistant", "content": msg})
    messages.append({"role": "user", "content": user_message})

    # Call OpenAI Chat API using new client
    response = client.chat.completions.create(
        model="gpt-4-0613",
        messages=messages,
        functions=TOOLS,
        function_call="auto",
        temperature=0.7,
    )

    message = response.choices[0].message

    # Handle tool call
    if message.function_call:
        func_args = json.loads(message.function_call.arguments)
        tool_results = search_recipes_tool(**func_args)
        summary = "\n".join( [f"**{r['title']}**\n{r['content']}\n[{r['url']}]({r['url']})" for r in tool_results])
        follow_up = client.chat.completions.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "Summarize search results for the user politely."},
                {"role": "user", "content": f"User asked: {user_message}\nHere are the results:\n{summary}"}
            ],
            temperature=0.7,
        )
        return follow_up.choices[0].message.content

    return message.content or "Sorry, I couldn't generate a response."

# ====================================================
# 💬 Streamlit Chat UI
# ====================================================
st.set_page_config(page_title="Customer Service", page_icon="💬") 
st.markdown(""" 
<style> body { background-color: #F9FAFB; } 
.user-bubble { background-color: #DCF8C6; color: #000; padding:10px 15px; 
border-radius:12px; margin:8px 0; max-width:80%; margin-left:auto; } 
.bot-bubble { background-color: #E6E6E6; color:#000; padding:10px 15px; 
border-radius:12px; margin:8px 0; max-width:80%; margin-right:auto; } 
</style> 
""", unsafe_allow_html=True) 
st.title("💬 Food Customer Service Bot") 
st.caption("Ask about cooking doubts, accounts, or diet!") 
if "chat_history" not in st.session_state: 
      st.session_state.chat_history = [("🤖 Vedant", "Hello! 👋 How can I help you today?")] 
user_message = st.chat_input("Type your question here...") 
if user_message:
        ai_reply = get_ai_response(user_message) 
        st.session_state.chat_history.append(("👤 You", user_message)) 
        st.session_state.chat_history.append(("🤖 Vedant", ai_reply)) 
# Display chat history 
for role, msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if role == "👤 You" else "bot-bubble" 
    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b> {msg}</div>", unsafe_allow_html=True) 
    # Clear chat 
if st.button("🧹 Clear Chat"):
   st.session_state.chat_history = [("🤖 Vedant", "Hello! 👋 How can I help you today?")]
   st.success("Chat cleared!")