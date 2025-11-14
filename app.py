import streamlit as st
import os
import asyncio
from openai import OpenAI
from anthropic import Anthropic
from ollama import chat
from agents import Agent, FileSearchTool, Runner, WebSearchTool, handoff, RunContextWrapper
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

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

vector_store_id = os.getenv("VECTOR_STORE_ID")

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
ollama_instructions = load_instructions("ollama_agent_prompt.txt")
anthropic_instructions = load_instructions("anthropic_agent_prompt.txt")

# Add router instructions if prompt file doesn't exist or is empty
if not router_agent_instructions or router_agent_instructions == load_instructions("missing_file.txt"):
    router_agent_instructions = """You are a Router Agent that directs user requests to specialized agents.

Your available agents:
1. **FileSearchAgent**: Use for questions about uploaded documents, PDFs, or local knowledge base
2. **WebSearchAgent**: Use for current events, news, real-time information, or anything requiring web search

Decision rules:
- If user asks about documents, files, or references uploaded content → FileSearchAgent
- If user asks about current events, news, or needs fresh information → WebSearchAgent  
- For general conversation, coding, or analysis → respond directly

Always hand off to the appropriate agent when needed."""

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
    def on_handoff(ctx: RunContextWrapper[None]):
        log_system_message(f"🔄 Handoff to {agent_type} agent")
    return on_handoff

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

# Anthropic agent function
async def generate_anthropic_response(goal, conversation_history=""):
    log_system_message(f"🤖 Sending prompt to Claude agent")
    
    # Build messages for Anthropic API
    messages = []
    
    # Add conversation history
    if conversation_history:
        for line in conversation_history.split("\n\n"):
            if line.startswith("User: "):
                messages.append({"role": "user", "content": line.replace("User: ", "")})
            elif line.startswith("Assistant: "):
                messages.append({"role": "assistant", "content": line.replace("Assistant: ", "")})
    
    # Add current message
    messages.append({"role": "user", "content": goal})
    
    # Call Claude
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=messages
    )
    
    log_system_message("✅ Claude response received")
    return response.content[0].text

# Ollama agent function
async def generate_ollama_response(goal, conversation_history=""):
    log_system_message(f"🤖 Sending prompt to Ollama agent")
    
    # Build messages for Ollama
    messages = [
        {
            'role': 'system',
            'content': ollama_instructions
        }
    ]
    
    # Add conversation history
    if conversation_history:
        for line in conversation_history.split("\n\n"):
            if line.startswith("User: "):
                messages.append({"role": "user", "content": line.replace("User: ", "")})
            elif line.startswith("Assistant: "):
                messages.append({"role": "assistant", "content": line.replace("Assistant: ", "")})
    
    # Add current message
    messages.append({"role": "user", "content": goal})
    
    # Call Ollama
    try:
        response = chat(
            model='gemma3',
            messages=messages
        )
        log_system_message("✅ Ollama response received")
        return response['message']['content']
    except Exception as e:
        log_system_message(f"❌ Ollama error: {str(e)}")
        return f"Error connecting to Ollama: {str(e)}. Make sure Ollama is running locally."

# Custom handoff system - intercept and route to appropriate agent
async def custom_agent_runner(goal, conversation_history=""):
    full_prompt = f"{conversation_history}\n\nUser: {goal}" if conversation_history else goal
    log_system_message(f"🤖 Sending prompt to switch agent")
    
    # First, ask switch agent to decide which system to use
    switch_decision = await Runner.run(
        Agent(
            name="SwitchAgent",
            instructions="""You are a switch agent that determines which AI system to use. Analyze the user's request and respond with ONLY ONE WORD:
            - "ROUTER" if user wants to work with ChatGPT/OpenAI, needs file search, web search, or doesn't specify a preference
            - "ANTHROPIC" if user explicitly mentions Anthropic/Claude or wants help with coding/writing
            - "OLLAMA" if user explicitly mentions Ollama or wants to work offline
            
            Respond with just one word: ROUTER, ANTHROPIC, or OLLAMA""",
            tools=[],
            model="gpt-4o-mini"
        ),
        full_prompt
    )
    
    decision = switch_decision.final_output.strip().upper()
    log_system_message(f"🎯 Switch decision: {decision}")
    
    # Route based on decision
    if decision == "ROUTER":
        log_system_message(f"🔄 Routing to OpenAI Router Agent")
        
        # Now let router decide between FILE, WEB, or GENERAL
        router_decision = await Runner.run(
            Agent(
                name="RouterAgent",
                instructions="""Analyze the request and respond with ONE WORD:
                - "FILE" if asking about documents or uploaded files
                - "WEB" if needs current information or web search
                - "GENERAL" for general questions, coding help, or analysis
                
                Respond with: FILE, WEB, or GENERAL""",
                tools=[],
                model="gpt-4o-mini"
            ),
            full_prompt
        )
        
        sub_decision = router_decision.final_output.strip().upper()
        log_system_message(f"📍 Router sub-decision: {sub_decision}")
        
        if sub_decision == "FILE":
            log_system_message(f"🔄 Handoff to FileSearch agent")
            result = await Runner.run(file_search_agent, full_prompt)
            return result.final_output
        
        elif sub_decision == "WEB":
            log_system_message(f"🔄 Handoff to WebSearch agent")
            result = await Runner.run(web_search_agent, full_prompt)
            return result.final_output
        
        else:
            log_system_message(f"🔄 Handling with base OpenAI agent")
            result = await Runner.run(router_agent, full_prompt)
            return result.final_output
    
    elif decision == "ANTHROPIC":
        log_system_message(f"🔄 Routing to Anthropic Claude")
        return await generate_anthropic_response(goal, conversation_history)
    
    elif decision == "OLLAMA":
        log_system_message(f"🔄 Routing to Ollama (Offline)")
        return await generate_ollama_response(goal, conversation_history)
    
    else:
        # Default to router if decision is unclear
        log_system_message(f"⚠️ Unclear decision, defaulting to OpenAI Router")
        result = await Runner.run(router_agent, full_prompt)
        return result.final_output

# Define a function to run the agent (keep for backwards compatibility)
async def generate_tasks(goal, conversation_history=""):
    return await custom_agent_runner(goal, conversation_history)

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []
    log_system_message("🚀 Application initialized")

st.title("Multi Agent Playground")

# Create two columns: chat and logs
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Chat")
    
    # Display chat history in a scrollable container
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat input (always at bottom)
    prompt = st.chat_input("What would you like me to do?")

    # Process input
    if prompt:
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
            
            # Use the router agent system
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