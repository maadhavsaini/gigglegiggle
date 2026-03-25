# Derei Assistant

A multifunction AI assistant project with three interfaces:

- **Web app** built with Flask + Groq (`app.py`)
- **Terminal app** built with Rich + Groq (`chatbot.py`)
- **Discord bot** built with discord.py + Groq (`discord_bot.py`)

This project combines chat, model selection, notes, to-do workflow, DECA prep, medical term breakdowns, web search + URL summarization, global RSS news summarization, and Discord integration.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Features](#core-features)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Run the Project](#run-the-project)
- [Discord Bot](#discord-bot)
- [API Reference (Web)](#api-reference-web)
- [Terminal Commands](#terminal-commands)
- [Configuration Notes](#configuration-notes)
- [Security and Code Protection](#security-and-code-protection)
- [Deployment Notes](#deployment-notes)
- [Troubleshooting](#troubleshooting)
- [Roadmap Ideas](#roadmap-ideas)

---

## Project Overview

Derei Assistant is designed as a **student-focused productivity and learning assistant**.

It supports:

- General AI chat with history
- Dynamic Groq model catalog + model-specific routing
- Vision chat for image attachments
- File-aware Q&A with text/PDF ingestion
- Structured study modes (DECA, medical terminology, essay feedback, math helper)
- Productivity modules (to-do + pomodoro timer + notes)
- Lightweight web intelligence (search + URL summarize + global news summaries)
- **Discord integration** — Chat with Derei directly in Discord servers

---

## Core Features

### 1) AI Chat (Web + Terminal)

- Multi-turn conversation with full message history
- Configurable system prompts and "prep messages"
- Live token estimation and model selection
- Both text and vision support (where model allows)

### 2) Model Management

- Dynamic Groq model catalog discovery
- Model-specific capability routing (text-only, vision, voice, etc.)
- Fallback logic when requested model is unavailable
- Curated model summaries and naming

### 3) File & Context Ingestion

- **Text files**: Smart chunking with overlap for semantic retrieval
- **PDF files**: Full-text extraction with page limits
- **Image attachments**: Vision-model analysis (when supported)
- Retrieval-augmented generation (RAG) for long documents

### 4) Study & Learning Modes

- **DECA Prep**: Specific guidance for competition preparation
- **Medical Terminology**: Medical term definitions and contexts
- **Essay Feedback**: Structured review with rubric considerations
- **Math Helper**: Problem-solving with step-by-step explanations

### 5) Productivity Suite

- **To-Do Manager**: Add, mark done, clear daily
- **Pomodoro Timer**: Floating popup timer with pause/resume
- **Notes Integration**: Create and manage notes (optional Obsidian sync)
- **Daily Task Seeding**: Auto-populate daily tasks from template

### 6) Web Intelligence

- **Web Search**: Live search + URL summarization
- **URL Summarization**: Fast content extraction from any URL
- **Global News Feed**: Multi-source RSS aggregation with AI summaries
- **Continent Organization**: News sorted by geographic region

### 7) Discord Integration

- **Discord Bot**: Chat with Derei directly in Discord servers
- **Slash Commands**: `/ask <question>` for instant AI responses
- **Multi-turn Conversations**: Derei remembers context per Discord user
- **Study in Discord**: No context-switching needed; stay with your study group
- **Command History**: `/clear` to reset conversation history

---

## Tech Stack

- **Backend**: Flask (Python)
- **Discord**: discord.py (Python)
- **AI/LLM**: Groq API (llama-3.3-70b-versatile, llama-4-scout-17b, etc.)
- **Frontend**: Vanilla JS + CSS
- **Terminal UI**: Rich library (Python)
- **Data**: JSON files (chat history, todos, notes)
- **PDF Processing**: PyPDF2
- **Deployment**: Gunicorn + Railway (or similar cloud provider)

---

## Repository Structure

```
gigglegiggle/
├── chatbot_hosting_files/
│   ├── app.py                    # Flask web app
│   ├── chatbot.py                # Terminal CLI app
│   ├── discord_bot.py            # Discord bot (NEW)
│   ├── derei_constitution.md     # System prompt override
│   ├── requirements.txt           # Python dependencies (includes discord.py)
│   ├── runtime.txt                # Python version (for Railway)
│   ├── Procfile                   # Deployment config
│   ├── .env                       # Local env vars (not committed)
│   ├── templates/
│   │   └── index.html             # Web UI
│   ├── static/
│   │   └── design-system.css      # Styling system
│   └── data/
│       ├── chats/                 # Chat history JSONs
│       ├── notes/                 # User notes
│       └── todos.txt              # To-do list
├── README.md                       # This file
├── LICENSE                         # License info
└── DEPLOYMENT_GUIDE.md            # Railway deployment guide
```

---

## Setup

### Prerequisites

- Python 3.9+
- pip or conda
- Groq API key (from [console.groq.com](https://console.groq.com))

### Local Installation

```bash
# Clone the repo
git clone https://github.com/maadhavsaini/gigglegiggle.git
cd gigglegiggle/chatbot_hosting_files

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "GROQ_API_KEY=your_api_key_here" > .env
```

---

## Environment Variables

### Required

- **`GROQ_API_KEY`** — Your Groq API key (get one at [console.groq.com](https://console.groq.com))

### Optional

- **`DATA_DIR`** — Base directory for chat/todo/notes storage (default: `./data`)
- **`FLASK_DEBUG`** — Set to `1` for debug mode locally (never in production)

### Optional (Advanced)

- **`PORT`** — HTTP port (default: `5000`, Railway sets automatically)

---

## Run the Project

### Web App (Flask)

```bash
cd chatbot_hosting_files
python app.py
```

Then visit: **http://localhost:5000**

### Terminal App (CLI)

```bash
cd chatbot_hosting_files
python chatbot.py
```

Fully interactive terminal UI with rich formatting.

### Discord Bot

```bash
cd chatbot_hosting_files
python discord_bot.py
```

The bot will connect to Discord and listen for commands. **Before running, follow the [Discord Bot Setup Guide](DISCORD_BOT_SETUP.md) to:**

1. Create a Discord application
2. Get your bot token
3. Set `DISCORD_TOKEN` in `.env` or Railway Variables

Once running, use `/ask <question>` in Discord to chat with Derei!

---

## Discord Bot

The Derei Discord bot allows users to chat with AI directly in Discord without leaving their server. Perfect for study groups!

### Quick Start

1. **Create Discord app** (see [Discord Bot Setup Guide](DISCORD_BOT_SETUP.md))
2. **Set DISCORD_TOKEN** in `.env` or Railway Variables
3. **Run bot**: `python discord_bot.py`
4. **In Discord**: Type `/ask <question>` to chat with Derei

### Commands

| Command  | Usage                          | Description                          |
| -------- | ------------------------------ | ------------------------------------ |
| `/ask`   | `/ask What is photosynthesis?` | Ask Derei any question               |
| `/clear` | `/clear`                       | Reset your conversation history      |
| `/derei` | `/derei`                       | Show bot info and available commands |

### Features

- ✅ Multi-turn conversations (remembers context per user)
- ✅ Beautiful embedded responses
- ✅ Automatic response trimming (fits Discord's 2000-char limit)
- ✅ Graceful error handling
- ✅ No persistent storage (privacy-focused)

### Deploy to Railway (Optional)

For 24/7 bot uptime, create a new Railway service:

1. In Railway, create a new service for this repo
2. Set start command: `python chatbot_hosting_files/discord_bot.py`
3. Add `DISCORD_TOKEN` variable
4. Deploy

See [Discord Bot Setup Guide](DISCORD_BOT_SETUP.md) for detailed instructions.

---

## API Reference (Web)

The web app exposes REST endpoints for frontend to call:

### `/api/chat` (POST)

Send a message and get a response.

**Request:**

```json
{
  "message": "What is photosynthesis?",
  "model": "llama-3.3-70b-versatile",
  "session_file": "default"
}
```

**Response:**

```json
{
  "reply": "Photosynthesis is...",
  "model_used": "llama-3.3-70b-versatile",
  "tokens_estimate": 250
}
```

### `/api/groq-models` (GET)

Get list of available Groq models.

**Response:**

```json
{
  "source": "api",
  "models": [
    {
      "id": "llama-3.3-70b-versatile",
      "name": "Meta Llama 3.3 70B Versatile",
      "summary": "Strong general-purpose...",
      "supportsText": true,
      "supportsImage": false,
      "group": "text-only"
    }
  ]
}
```

### `/api/todo` (GET, POST, DELETE)

Manage to-do items.

**POST** (add task):

```json
{
  "action": "add",
  "task": "Study for exams"
}
```

**GET** (list tasks): Returns `{"todos": [...], "done": [...]}`

**DELETE** (mark done):

```json
{
  "action": "mark_done",
  "index": 0
}
```

### `/api/timer` (POST)

Start a Pomodoro timer (frontend controls).

### `/api/notes` (GET, POST)

Manage notes.

### `/api/search` (POST)

Web search + URL summarization.

### `/api/news` (GET, POST)

Global RSS news feed with AI summaries.

---

## Terminal Commands

In the terminal CLI (`chatbot.py`), after launching, you can type commands:

- **`/help`** — Show all commands
- **`/clear`** — Clear chat history
- **`/private`** — Toggle private mode (no history saved)
- **`/todo`** — Show to-do list
- **`/done`** — Mark a task as done
- **`/notes`** — Show notes menu
- **`/model <name>`** — Switch AI model
- **`/exit`** — Exit the app

---

## Configuration Notes

### Customize System Prompt

Edit `derei_constitution.md` to change the assistant's personality and behavior.

### Add Daily Tasks

Edit the `DAILY_TASKS` list in `app.py` or `chatbot.py` to customize seeded tasks.

### Adjust Safety Limits

In `app.py`, tune these constants:

- `MAX_HISTORY_MESSAGES` — Chat history size
- `MAX_FILE_SIZE_BYTES` — Max file upload size
- `MAX_PDF_PAGES` — Max PDF pages to process
- `MAX_INPUT_TOKENS` — Max input token limit
- `MAX_OUTPUT_TOKENS` — Max response token limit

---

## Security and Code Protection

### Best Practices

1. **Never commit `.env`** — Add it to `.gitignore`
2. **Rotate API keys** regularly in production
3. **Use environment variables** for all secrets
4. **Keep dependencies updated** (`pip install -r requirements.txt --upgrade`)
5. **Monitor API usage** at [console.groq.com](https://console.groq.com)

### Rate Limiting

The app does not enforce rate limits locally, but Groq API has built-in quotas based on your plan.

---

## Deployment Notes

**See `DEPLOYMENT_GUIDE.md`** for step-by-step Railway deployment instructions.

Quick summary:

- Push to GitHub
- Connect Railway to your repo
- Set `GROQ_API_KEY` in Railway Variables
- Deploy (automatic on push)

---

## Troubleshooting

### "Missing GROQ_API_KEY"

- Ensure your `.env` file (locally) or Railway Variables (production) include `GROQ_API_KEY`

### "ModuleNotFoundError: No module named ..."

- Run `pip install -r requirements.txt` to install dependencies

### "Connection refused" when running locally

- Make sure no other app is using port 5000
- Or set `PORT=8000` and run: `PORT=8000 python app.py`

### "ImageProcessing failed" or vision issues

- Not all Groq models support vision; check `/api/groq-models` response
- The app auto-falls back to text-only models if needed

### Chat history not saving

- Check that the `data/` directory exists and is writable
- Verify `DATA_DIR` env variable (if set) points to a valid directory

---

## Roadmap Ideas

- [ ] User authentication & multi-user support
- [ ] Voice input/output (Whisper + TTS)
- [ ] Real-time collaboration
- [ ] Custom knowledge base upload
- [ ] Mobile app (React Native)
- [ ] Plugin system for custom tools
- [ ] Advanced RAG with vector embeddings
- [ ] Scheduled tasks & reminders

---

## License

See `LICENSE` file for details.

---

**Happy coding!** 🚀
