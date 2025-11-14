import streamlit as st
import os
import asyncio
from openai import OpenAI
from agents import Agent, FileSearchTool, Runner, WebSearchTool, handoff
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Logging system
def log_system_message(message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.setdefault("system_logs", [])
    st.session_state["system_logs"].append(f"[{timestamp}] {message}")

# AGENT SETUP 
# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
vector_store_id = os.environ.get("VECTOR_STORE_ID")

# Load prompts 
def load_instructions(file_name):
    try:
        with open(file_name, "r") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"❌ {file_name} not found. Using default instructions.")
        return """You are an experienced and knowledgeable yoga teacher. You provide accurate, helpful information about yoga practices, philosophy, poses, breathing techniques, and wellness. 

Always cite your sources and provide practical, safe guidance. When discussing physical practices, remind users to listen to their bodies and consult healthcare professionals for medical advice.

Be warm, encouraging, and mindful in your responses. Use yoga terminology appropriately but explain terms when needed."""

router_agent_instructions = load_instructions("router_agent_prompt.txt")
file_agent_instructions = load_instructions("file_agent_prompt.txt")
web_agent_instructions = load_instructions("web_agent_prompt.txt")

# Initialize tools 
tools = [
    WebSearchTool(),  # web search tool 
    FileSearchTool(
        max_num_results=3,
        vector_store_ids=[vector_store_id],  # file search tool 
    ),
]

# Handoff callback
def create_handoff_callback(agent_type):
    def callback(context):
        log_system_message(f"🔄 Handoff to {agent_type} agent")
    return callback

# Initialize specialized agents first (they need to exist before router can reference them)
file_search_agent = Agent(
    name="FileSearchAgent",
    instructions=file_agent_instructions,
    tools=[tools[1]],
    model="gpt-4o-mini"
)

web_search_agent = Agent(
    name="WebSearchAgent",
    instructions=web_agent_instructions,
    tools=[tools[0]],
    model="gpt-4o-mini"
)

# Initialize router agent with handoffs
router_agent = Agent(
    name="RouterAgent",
    instructions=router_agent_instructions,
    tools=[],
    model="gpt-4o-mini",
    handoffs=[
        handoff(file_search_agent, on_handoff=create_handoff_callback("FileSearch")),
        handoff(web_search_agent, on_handoff=create_handoff_callback("WebSearch")),
    ]
)

# Define a function to run the agent
async def generate_tasks(goal, conversation_history=""):
    full_prompt = f"{conversation_history}\n\nUser: {goal}" if conversation_history else goal
    log_system_message(f"🤖 Sending prompt to router agent with conversation history")
    result = await Runner.run(router_agent, full_prompt)
    log_system_message("✅ Agent response received")
    return result.final_output

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []
    log_system_message("🚀 Application initialized")

st.title("RouterAgent")

# Create two columns: chat and logs
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("What would you like me to do?"):
        log_system_message(f"📝 User input received: '{prompt}'")
        
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_system_message("💾 User message saved to history")
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            log_system_message("⏳ Generating agent response...")
            
            # Build conversation history
            conversation_history = "\n\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in st.session_state.messages[:-1]  # Exclude the current message
            ])
            log_system_message(f"📚 Added {len(st.session_state.messages)-1} previous messages to context")
            
            assistant_message = asyncio.run(generate_tasks(prompt, conversation_history))
            st.markdown(assistant_message)
            log_system_message("💾 Assistant message saved to history")
        
        # Add assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        log_system_message("✨ Conversation turn complete")

with col2:
    st.subheader("System Logs")
    log_container = st.container(height=600)
    with log_container:
        if "system_logs" in st.session_state:
            for log in st.session_state["system_logs"]:
                st.text(log)
        else:
            st.text("No logs yet...")