# Multi-Agent Playground

A Streamlit application that intelligently routes user queries between multiple AI agents and models, including OpenAI GPT, Anthropic Claude, and local Ollama models.

## How It Works (Simple Explanation)
More in the presentation https://claude.ai/public/artifacts/c8ee4530-d8c4-4bc7-999b-2da2d1bbdae4

### 🎯 What Is It?

A smart chatbot that automatically picks the best AI for your question.

Think of it like having **3 different experts** and a **receptionist** who directs you to the right one.

### 👥 The Team

#### 1. **The Receptionist (Switch Agent)**
- First person you talk to
- Asks: "Which expert should handle this?"
- Makes the decision in seconds

#### 2. **OpenAI Expert**
- Good at: General questions, searching files, web searches
- Has helpers for specific tasks

#### 3. **Claude (Anthropic) Expert**
- Good at: Writing code, creative writing, detailed analysis

#### 4. **Offline Expert (Ollama)**
- Good at: Working without internet
- Runs on your computer

### 🔄 How Does It Work?

**Step 1: You Ask a Question**
```
"Help me write a Python function"
```

**Step 2: The Receptionist Decides**
- Sees you mentioned "write" and "code"
- Thinks: "Claude is best for coding!"
- Routes to Claude

**Step 3: You Get Your Answer**
- Claude writes the code
- You get a great response

### 📊 Real Example Flow

**Your Question:** *"Search my documents for yoga poses"*

```
You → Switch Agent
        ↓
   Sees "search documents"
        ↓
   Routes to OpenAI
        ↓
   OpenAI Router Agent
        ↓
   Sees "documents"
        ↓
   File Search Agent → Searches your files
        ↓
   Returns answer to you
```
---

## Features

### 🤖 Multi-Agent Architecture
- **Switch Agent**: Top-level router that determines which AI system to use
- **Router Agent**: OpenAI-based router that handles file search, web search, or general queries
- **File Search Agent**: Searches through uploaded documents using vector store
- **Web Search Agent**: Retrieves current information from the web
- **Anthropic Claude**: For coding, writing, and complex reasoning tasks
- **Ollama (Offline)**: Local AI models for offline operation

### 📊 Real-time System Logs
- Track all agent decisions and handoffs
- See which agent is handling each query
- Monitor routing logic in real-time

### 💬 Conversation Management
- Maintains full conversation history
- Context-aware responses across all agents
- Persistent chat state during session

## Architecture Flow

```
User Query
    ↓
Switch Agent (decides: ROUTER, ANTHROPIC, or OLLAMA)
    ↓
    ├─→ ROUTER → Router Agent (decides: FILE, WEB, or GENERAL)
    │       ├─→ FILE → File Search Agent
    │       ├─→ WEB → Web Search Agent
    │       └─→ GENERAL → Base OpenAI Agent
    │
    ├─→ ANTHROPIC → Claude Sonnet 4
    │
    └─→ OLLAMA → Local Gemma3 Model
```

## Prerequisites

- Python 3.8+
- OpenAI API key
- Anthropic API key
- Ollama (optional, for offline functionality)
- Vector store ID (for file search functionality)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd multi-agent-playground
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
VECTOR_STORE_ID=your_vector_store_id
```

5. (Optional) Install and set up Ollama:
```bash
# Install Ollama from https://ollama.ai
ollama pull gemma3
ollama serve
```

## Configuration Files

Create the following prompt instruction files in your project directory:

- `router_agent_prompt.txt` - Instructions for the main router agent
- `file_agent_prompt.txt` - Instructions for file search operations
- `web_agent_prompt.txt` - Instructions for web search operations
- `ollama_agent_prompt.txt` - System prompt for Ollama model
- `anthropic_agent_prompt.txt` - System prompt for Claude

If these files are not found, the application will use default instructions.

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Start chatting! The system will automatically route your queries to the appropriate agent:
   - **Mention "ChatGPT" or "OpenAI"** → Routes to OpenAI Router
   - **Mention "Claude" or "Anthropic"** → Routes to Anthropic
   - **Mention "Ollama" or "offline"** → Routes to local Ollama
   - **Ask about files/documents** → Routes to File Search Agent
   - **Ask about current events** → Routes to Web Search Agent
   - **General queries** → Automatically routed based on context

## Example Queries

```
"Search my documents for information about yoga poses"
→ Routes to File Search Agent

"What's the latest news on AI?"
→ Routes to Web Search Agent

"Help me write a Python function using Claude"
→ Routes to Anthropic Claude

"I want to work offline, help me debug this code"
→ Routes to Ollama

"Explain quantum computing" (no specification)
→ Switch Agent decides based on context
```

## System Logs

Monitor the right panel to see:
- Agent routing decisions
- Handoff events
- Response confirmations
- Error messages

## Customization

### Change Models

**OpenAI Model:**
```python
model="gpt-4o-mini"  # Change to "gpt-4o" for more powerful responses
```

**Anthropic Model:**
```python
model="claude-sonnet-4-20250514"  # Change to other Claude versions
```

**Ollama Model:**
```python
model='gemma3'  # Change to 'llama3.2', 'mistral', etc.
```

### Adjust Agent Instructions

Edit the prompt files or modify the inline instructions in the code to change agent behavior.

### Modify Routing Logic

Edit the Switch Agent instructions to change how queries are routed between different AI systems.

## Troubleshooting

### Ollama Connection Error
```
Error connecting to Ollama: [Errno 61] Connection refused
```
**Solution:** Make sure Ollama is running: `ollama serve`

### Missing API Keys
```
The api_key client option must be set
```
**Solution:** Check your `.env` file and ensure API keys are properly set

### File Search Not Working
**Solution:** Verify your `VECTOR_STORE_ID` is correct and you have uploaded documents to your vector store

## Dependencies

- `streamlit` - Web interface
- `openai` - OpenAI API client
- `anthropic` - Anthropic API client
- `ollama` - Local LLM client
- `agents` - OpenAI agents SDK
- `python-dotenv` - Environment variable management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- OpenAI for GPT models and Agents SDK
- Anthropic for Claude
- Ollama for local LLM support
- Streamlit for the amazing web framework
