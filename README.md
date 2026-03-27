# Derei Assistant

A multifunction AI assistant with web, terminal, and Discord interfaces.

## Features

- **Web App** — Chat interface with model selection, file upload, and auth
- **Terminal App** — Rich CLI with streaming responses
- **Discord Bot** — Native Discord integration with `/ask` commands
- **Authentication** — User login/signup with Supabase PostgreSQL
- **AI** — Groq API for fast LLM inference
- **Vision** — Image analysis support
- **Files** — PDF and text file analysis

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** Supabase PostgreSQL
- **Auth:** Supabase session tokens
- **AI/LLM:** Groq API
- **Discord:** discord.py
- **Frontend:** HTML/CSS/JS

## Quick Start

### Prerequisites

- Python 3.8+
- Groq API key ([console.groq.com](https://console.groq.com))
- Supabase project ([supabase.com](https://supabase.com))

### Install & Setup

```bash
# Clone and install
git clone https://github.com/maadhavsaini/gigglegiggle.git
cd gigglegiggle/chatbot_hosting_files
pip install -r requirements.txt

# Create .env with your API keys
cat > .env << EOF
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GROQ_API_KEY=your-groq-api-key
DISCORD_TOKEN=your-discord-token
FLASK_DEBUG=1
PORT=5000
EOF
```

### Initialize Supabase Database

Go to [app.supabase.com](https://app.supabase.com) → SQL Editor → paste & run:

```sql
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  session_token TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  expires_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  chat_id UUID REFERENCES chats(id) ON DELETE CASCADE NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);
```

### Run

```bash
# Web app
python app.py
# Visit http://localhost:5000

# Terminal app
python chatbot.py

# Discord bot
python discord_bot.py
```

## Project Structure

```
chatbot_hosting_files/
├── app.py                 # Flask web server
├── chatbot.py             # Terminal interface
├── discord_bot.py         # Discord bot
├── auth_supabase.py       # Supabase auth manager
├── requirements.txt       # Dependencies
├── templates/             # HTML templates
├── static/                # CSS/JS assets
└── data/                  # Chat history storage
```

## Discord Bot Commands

| Command  | Usage                          | Description             |
| -------- | ------------------------------ | ----------------------- |
| `/ask`   | `/ask What is photosynthesis?` | Ask Derei a question    |
| `/clear` | `/clear`                       | Clear your chat history |

## Environment Variables

| Variable        | Required | Description                            |
| --------------- | -------- | -------------------------------------- |
| `SUPABASE_URL`  | Yes      | Your Supabase project URL              |
| `SUPABASE_KEY`  | Yes      | Your Supabase anon key                 |
| `GROQ_API_KEY`  | Yes      | Your Groq API key                      |
| `DISCORD_TOKEN` | No       | Discord bot token (for Discord bot)    |
| `FLASK_DEBUG`   | No       | Set to `1` for debug mode (local only) |
| `PORT`          | No       | HTTP port (default: 5000)              |

## License

See [LICENSE](LICENSE) for details.
