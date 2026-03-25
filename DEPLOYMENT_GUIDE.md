# Railway Deployment Guide for Derei Assistant

## 🎯 Overview

This guide walks you through deploying your **web app** (Flask/Groq) to Railway. The terminal CLI (`chatbot.py`) should remain local-only; only `app.py` is deployed.

---

## ✅ What I Fixed

Your codebase had deployment blockers that prevented GitHub pushes and Railway deployment:

### 1. **Hardcoded Paths in `chatbot.py`** ❌ → ✅

- **Problem**: Absolute paths like `/Users/maadhavsaini/aaaa/hello/...` won't work on Railway
- **Fix**: Now uses `os.path.join(BASE_DATA_DIR, ...)` with `DATA_DIR` environment variable
- **Result**: Works both locally and on Railway

### 2. **Missing Runtime Dependencies** ❌ → ✅

- **Problem**: `requirements.txt` was missing:
  - `PyPDF2` (used for PDF processing)
  - `rich` (used by CLI)
  - `huggingface-hub` (dynamic import in chatbot.py)
  - `requests` (web utilities)
- **Fix**: Added all missing packages to `requirements.txt`
- **Result**: All imports will now resolve successfully

### 3. **Infrastructure Ready** ✅

- `Procfile` correctly runs: `web: gunicorn app:app --bind 0.0.0.0:$PORT`
- `app.py` uses environment variables for config
- `runtime.txt` specifies Python 3.11.9

---

## 🚀 Step-by-Step Deployment to Railway

### **Step 1: Push to GitHub**

```bash
cd /Users/maadhavsaini/Documents/gigglegiggle
git add -A
git commit -m "Fix deployment issues: add missing deps, fix paths for Railway"
git push
```

### **Step 2: Connect Railway to Your GitHub Repo**

1. Go to [railway.app](https://railway.app)
2. Sign up (if needed) with GitHub
3. Click **"New Project"** → **"Deploy from GitHub Repo"**
4. Select your `gigglegiggle` repository
5. Railway will auto-detect the `Procfile` and `runtime.txt`

### **Step 3: Set Environment Variables in Railway**

In the Railway dashboard, go to **Variables** and add:

```
GROQ_API_KEY=your_actual_groq_api_key_here
```

**Get your Groq API key:**

1. Visit [console.groq.com](https://console.groq.com)
2. Create/copy your API key
3. Paste it into Railway Variables

Optionally set:

```
DATA_DIR=/data        # (Railway will use /data directory)
FLASK_DEBUG=0         # (Keep at 0 for production)
```

### **Step 4: Deploy**

- Railway auto-deploys on every GitHub push
- Watch the **Build Logs** to ensure deployment succeeds
- Once deployed, you'll get a public URL like: `https://your-app.up.railway.app`

---

## 📋 Troubleshooting

### **"Missing GROQ_API_KEY" Error**

- **Fix**: Add `GROQ_API_KEY` to Railway Variables (see Step 3)

### **"Port binding failed"**

- **Fix**: Railway automatically injects the `$PORT` variable; your app reads it correctly

### **"ModuleNotFoundError: No module named 'PyPDF2'"**

- **Fix**: Already added to `requirements.txt`; Railway will install on deploy

### **GitHub Push Still Failing**

- Run `git status` and check for uncommitted changes
- Ensure you're in the correct directory
- Try: `git pull origin main` first, then push

---

## 🔄 Local Development vs. Production

### **Running Locally**

```bash
cd chatbot_hosting_files
python app.py
```

Visit: `http://localhost:5000`

### **Local CLI (chatbot.py)**

```bash
cd chatbot_hosting_files
python chatbot.py
```

This remains local-only and is **NOT deployed** to Railway.

---

## 📁 File Structure (Deployment)

```
chatbot_hosting_files/
├── app.py                 ← Web app (DEPLOYED)
├── chatbot.py            ← CLI app (local only)
├── Procfile              ← Railway config
├── requirements.txt      ← Python deps (now fixed)
├── runtime.txt           ← Python version
├── .env                  ← Local secrets (don't commit)
├── templates/
│   └── index.html        ← Web UI
├── static/
│   └── design-system.css ← Styles
└── data/                 ← Chat history (on Railway: /data)
    ├── chats/
    └── notes/
```

---

## 🔐 Important Security Notes

1. **Never commit `.env`** — Railway Variables are used instead
2. **GROQ_API_KEY is secret** — don't share in GitHub
3. **Persistent storage** — Railway provides `/data` directory for chat history

---

## ✨ Next Steps

1. **Commit & push** the fixes
2. **Add Railway Variables** (GROQ_API_KEY)
3. **Deploy** (automatic on push)
4. **Test** your web app at the Railway URL

---

## 💡 Pro Tips

- Use `railway logs` CLI to debug issues
- Set `FLASK_DEBUG=1` temporarily for development on Railway (not recommended for production)
- Monitor API usage in [console.groq.com](https://console.groq.com)

---

**Your app is now production-ready!** 🎉
