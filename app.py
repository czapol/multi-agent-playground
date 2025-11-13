import streamlit as st
import os
from openai import OpenAI
from agents import Agent, FileSearchTool, Runner, WebSearchTool
from dotenv import load_dotenv, find_dotenv


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("RouterAgent")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages
        )
        assistant_message = response.choices[0].message.content
        st.markdown(assistant_message)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_message})

