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

### 3. Run Local Installation

```bash
# Install new dependency
pip install supabase

# Create the database tables (run the SQL provided in setup guide)
# Go to Supabase Dashboard → SQL Editor → New Query → Paste SQL → Execute
```

### 4. Update app.py

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

### 5. Test Locally

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
