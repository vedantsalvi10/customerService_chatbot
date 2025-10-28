
import os
import streamlit as st
import json
import re
from dotenv import load_dotenv
from exa_py import Exa
from openai import OpenAI 


# setting the api keys
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

if not OPENAI_API_KEY or not EXA_API_KEY:
    st.error("Missing OPENAI_API_KEY or EXA_API_KEY in environment variables.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize EXA client
exa = Exa(api_key=EXA_API_KEY)

# system prompt
prompt = """
You are an AI chef assistant that follows the ReAct (Reason + Act) framework *strictly*.

Your reasoning loop ALWAYS follows this exact order, and you must produce **at least 4 reasoning-action-observation steps** before giving your final answer, unless explicitly told to stop.

Follow this structure exactly:

Thought: <your reasoning about what to do next>
Action: <tool_name>: <input>   (only if you need to use a tool)
Observation: (will be provided later)
Thought: <your reasoning after seeing the observation>
Action: <next tool or plan>
Observation: ...
(continue this loop for at least 4 total Thought/Action/Observation cycles)
Final Answer: <your final answer to the user, using all reasoning so far>

Rules:
- Use the tool only when needed.
- Never skip the "Thought", "Action", or "Observation" labels.
- Do NOT write the Final Answer until you have reasoned for at least 4 steps.
- Always refine your reasoning from the previous observations.

Available Tool:
- search_recipes: Search for relevant recipes or cooking details given a user's query.

Be clear, structured, and polite in your Final Answer.
"""

# exa function
def search_recipes_tool(query, num_results = 5):
    results = exa.search_and_contents(query, num_results=num_results,highlights=True)
    return [{"title": r.title, "url": r.url, "content": r.highlights} for r in results.results]

# Tool defination for function calling
tools = {
    "search_recipes":search_recipes_tool
}
# setting up the bot
class Agent:
    def __init__(self,system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role":"system","content":system})
    def __call__(self,message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    def execute(self):
        completion = client.chat.completions.create(
                        model="gpt-4o", 
                        temperature=0,
                        messages=self.messages)
        return completion.choices[0].message.content

# creating reAct loop for the query
action_re = re.compile('^Action: (\w+): (.*)$')
def query(question,maxturns=5):
    if "agent" not in st.session_state:
        st.session_state.agent = Agent(prompt)
    bot = st.session_state.agent
    next_prompt = question
    trace_log = []
    for i in range(maxturns):
        result = bot(next_prompt)
        content = result["content"] if isinstance(result, dict) else result
        lines = content.split("\n")
        thought = None
        for line in lines:
            if line.startswith("Thought:"):
                thought = line.replace("Thought:", "").strip()
                trace_log.append({"type": "thought", "text": thought})
                
        actions = [
            action_re.match(a)
            for a in content.split('\n')
            if action_re.match(a)
        ]
        if actions:
            action,action_input = actions[0].groups()
            trace_log.append({"type": "action", "text": f"{action}: {action_input}"})
            if action not in tools:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            st.sidebar.write(f"🧠 Debug: calling {action} with input -> {action_input}")
            observation = tools[action](action_input)
            trace_log.append({"type": "observation", "text": observation})
            next_prompt = "Observation: {}".format(observation)
        else:
            if "Final Answer:" in result:
                final_output = result.split("Final Answer:")[-1].strip()
                return final_output,trace_log
            else:
                return content, trace_log
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

if "trace_log" not in st.session_state:
    st.session_state.trace_log = [] 
    
user_message = st.chat_input("Type your question here...") 
if user_message:
    ai_reply, trace_log = query(user_message)
    st.session_state.trace_log = trace_log 
    st.session_state.chat_history.append(("👤 You", user_message))
    st.session_state.chat_history.append(("🤖 Vedant", ai_reply))
# Display chat history 
for role, msg in st.session_state.chat_history:
    bubble_class = "user-bubble" if role == "👤 You" else "bot-bubble" 
    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b> {msg}</div>", unsafe_allow_html=True) 

# side bar
st.sidebar.title("🧩 ReAct Trace Log")
st.sidebar.caption("See the reasoning and actions behind each AI response")

# Display logs
if st.session_state.trace_log:
    for step in st.session_state.trace_log:
        if step["type"] == "thought":
            st.sidebar.markdown(f"💭 **Thought:** {step['text']}")
        elif step["type"] == "action":
            st.sidebar.markdown(f"⚙️ **Action:** `{step['text']}`")
        elif step["type"] == "observation":
            st.sidebar.markdown(f"👁️ **Observation:** {step['text']}")
        st.sidebar.markdown("---")
else:
    st.sidebar.info("No trace log yet — ask a question to see the reasoning flow.")