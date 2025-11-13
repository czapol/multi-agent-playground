import streamlit as st
import os
import asyncio
from openai import OpenAI
from agents import Agent, Runner
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize agent with tools
router_agent = Agent(
    name="RouterAgent",
    instructions="You are a helpful assistant.",
    tools=[],
    model="gpt-4"
)

# Define a function to run the agent
async def generate_tasks(goal):
    result = await Runner.run(router_agent, goal)
    return result.final_output

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("RouterAgent")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like me to do?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        assistant_message = asyncio.run(generate_tasks(prompt))
        st.markdown(assistant_message)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})