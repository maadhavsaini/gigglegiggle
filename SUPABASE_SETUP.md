# Supabase Integration Guide

## 🚀 Quick Start

### 1. Get Supabase Credentials

1. **Sign up** at [supabase.com](https://supabase.com)
2. **Create project** (pick region: `us-east-1` recommended)
3. **Go to Settings → API** and copy:
   - `Project URL` (looks like `https://xxxxx.supabase.co`)
   - `anon public key` (under "Project API keys")

### 2. Set Environment Variables

#### Local Development (.env)

Add to your `.env` file:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-key-here
GROQ_API_KEY=your-groq-key
DISCORD_TOKEN=your-discord-token
FLASK_DEBUG=1
PORT=5000
```

#### Railway Deployment

Go to Railway Dashboard → Your Project:

1. Click **Variables** tab
2. Add these variables:
   - `SUPABASE_URL` = your project URL
   - `SUPABASE_KEY` = your anon key
3. Keep existing variables (GROQ_API_KEY, PORT, etc.)
4. **Redeploy** after adding variables

---

## 📋 SQL TABLES YOU'RE CREATING

Here's what each table does:

| Table      | Purpose               | Fields                                             |
| ---------- | --------------------- | -------------------------------------------------- |
| `users`    | Stores user accounts  | id, username, email, password_hash, created_at     |
| `sessions` | Keeps users logged in | id, user_id, session_token, created_at, expires_at |
| `chats`    | Conversation threads  | id, user_id, title, created_at, updated_at         |
| `messages` | Chat messages         | id, chat_id, role, content, created_at             |

**How they connect:**

```
User (id)
  ↓ (one user has many sessions)
Session (user_id points to users.id)

User (id)
  ↓ (one user has many chats)
Chat (user_id points to users.id)
  ↓ (one chat has many messages)
Message (chat_id points to chats.id)
```

---

### 3. Create Database Tables (IMPORTANT!)

**Steps:**

1. Go to [app.supabase.com](https://app.supabase.com) → Click your project
2. Click **SQL Editor** (left sidebar)
3. Click **New Query** (top-right)
4. **Copy-paste the entire SQL block below** into the editor
5. Click **Run** button

**COPY-PASTE THIS SQL:**

```sql
-- ============================================
-- DEREI ASSISTANT - SUPABASE SCHEMA
-- ============================================

-- Users table
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Sessions table
CREATE TABLE sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  session_token TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  expires_at TIMESTAMP NOT NULL
);

-- Chats table
CREATE TABLE chats (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Messages table
CREATE TABLE messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  chat_id UUID REFERENCES chats(id) ON DELETE CASCADE NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for faster queries
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
CREATE INDEX idx_chats_user ON chats(user_id);
CREATE INDEX idx_messages_chat ON messages(chat_id);

-- Enable Row Level Security (temporary: allow public)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (for MVP)
CREATE POLICY "public_users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "public_sessions" ON sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "public_chats" ON chats FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "public_messages" ON messages FOR ALL USING (true) WITH CHECK (true);
```

**Expected result:** ✅ Success message appears

### 4. Install Supabase Package

```bash
pip install supabase
```

### 5. Update app.py

Replace the auth imports:

**OLD:**

```python
from auth import UserManager, ChatManager
user_manager = UserManager(BASE_DIR)
chat_manager = ChatManager(BASE_DIR)
```

**NEW:**

```python
from auth_supabase import SupabaseAuthManager, SupabaseChatManager
user_manager = SupabaseAuthManager()
chat_manager = SupabaseChatManager()
```

### 6. Test Locally

```bash
python app.py
# Visit http://localhost:5000
# Try: Register → Login → Create Chat → Add Message
```

All data should now appear in your Supabase dashboard!

---

## 📊 Advantages of Supabase

✅ **Persistent** - Data survives deployments  
✅ **Scalable** - Works with multiple app instances  
✅ **Backed up** - Automatic daily backups  
✅ **Free tier** - 500MB database included  
✅ **Real-time** - Can add live updates later  
✅ **Secure** - Password hashing + session tokens

---

## 🔄 Migration Path

**Option 1: Fresh Start (Recommended)**

- Keep old `auth.py` (not imported)
- New users use Supabase
- Old JSON data stays in `/data` folder

**Option 2: Migrate Existing Data**

- Export users from `data/users.json`
- Insert into Supabase `users` table manually

---

## 🐛 Troubleshooting

### Error: "Missing SUPABASE_URL"

→ Check your `.env` file or Railway Variables tab

### Error: "Connection refused"

→ Check SUPABASE_URL is correct (no typos)

### Sessions keep expiring

→ Check `expires_at` times in sessions table

### Data disappearing

→ Check Row Level Security policies (should allow public access for now)

---

## 📝 How It Works

### Registration Flow:

1. User submits username/email/password
2. Password hashed with PBKDF2-SHA256
3. User row inserted into `supabase.users` table
4. User redirected to login

### Login Flow:

1. Username looked up in `users` table
2. Password verified against hash
3. Random session token generated
4. Session stored with 30-day expiration
5. Token sent to frontend (saved in localStorage)

### Chat Flow:

1. Create chat row in `chats` table
2. Link to user via `user_id`
3. Messages stored in `messages` table
4. All linked via `chat_id`

---

## 🔒 Security Notes

✅ **Passwords hashed** - PBKDF2 with 100k iterations  
✅ **No plaintext storage** - Only hashes stored  
✅ **Session tokens** - 64-char random hex  
✅ **User isolation** - Each user only sees their data  
✅ **30-day expiration** - Sessions auto-expire

---

## 🚀 Next Steps

1. Get Supabase credentials
2. Create database tables (SQL provided)
3. Set environment variables (local + Railway)
4. Update app.py imports
5. Restart app
6. Test registration/login

Data now persists forever! 🎉
