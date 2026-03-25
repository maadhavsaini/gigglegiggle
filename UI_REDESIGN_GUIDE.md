# Derei UI Redesign & Authentication Guide

## 🎯 Major Changes

Your Derei Assistant now has a complete UI overhaul with authentication, chat history management, and a modern three-column layout.

---

## ✅ What's New

### 1. **User Authentication System** 🔐

- Create accounts with username/email/password
- Login with session tokens
- Session persistence (saved to localStorage)
- Automatic logout protection

### 2. **Three-Column Layout**

**Left Sidebar (Chat History)**

- List of all your saved chats
- Click to load any previous chat
- "+ New Chat" button to start fresh
- Account & Logout buttons

**Center (Chat Area)**

- Messages display with timestamps
- Vertical textarea input that expands upward
- Auto-scroll to latest messages
- File attachment support

**Right Sidebar (Model Selector)**

- AI model selection dropdown
- Model capability descriptions
- Voice input/output toggle buttons

### 3. **Chat History Persistence** 💾

- Every chat is saved to your account
- Chat history includes:
  - Chat title (auto-generated with date/time)
  - All messages (user + AI)
  - Timestamps for each message
  - Message count
- Browse old chats anytime
- Delete chats you don't need

### 4. **Responsive Input** ⌨️

- Textarea expands upward as you type (up to 120px limit)
- After max height, scrolls vertically instead of expanding
- Ctrl+Enter (or Cmd+Enter on Mac) to send
- Attach files while typing

### 5. **Login Screen** 🔑

- Clean, centered login form
- Switch between "Login" and "Sign Up" modes
- Error messages for validation failures
- Auto-login after account creation

---

## 🚀 How to Use

### **First Time: Create Account**

1. Load the app
2. Click **"Sign Up"**
3. Enter username, email, password (min 6 chars)
4. Click **"Create Account"**
5. Auto-redirected to chat screen

### **Returning Users: Login**

1. Load the app
2. Enter username & password
3. Click **"Login"**
4. Your previous chats load in the left sidebar

### **Start Chatting**

1. Click **"+ New Chat"** to start a fresh conversation
2. Select an AI model from the right sidebar
3. Type your message in the center
4. Hit **Send** or **Ctrl+Enter**
5. Messages auto-save to your chat history

### **Browse Past Chats**

1. Look at the left sidebar with all your chats
2. Click any chat to load its full history
3. Continue the conversation or just read

### **Manage Your Account**

1. Click **"Account"** button in bottom-left
2. See your profile info (username, email, chat count)
3. Click **"Logout"** to exit safely

---

## 📁 Architecture

### Backend Changes

**New File: `auth.py`**

```python
UserManager()      # Handle registration, login, sessions
ChatManager()      # Create, load, save chats
```

**New Endpoints:**

```
POST   /api/auth/register      # Create new user
POST   /api/auth/login         # Login + get session token
POST   /api/auth/logout        # Logout
GET    /api/auth/verify        # Check session validity

GET    /api/chats              # List all user's chats
POST   /api/chats              # Create new chat
GET    /api/chats/<id>         # Load specific chat
DELETE /api/chats/<id>         # Delete a chat
POST   /api/chats/<id>/messages # Add message to chat
```

### Data Structure

**Users File** (`data/users.json`):

```json
{
  "username1": {
    "email": "user@example.com",
    "password": "hashed_with_salt",
    "created_at": "2026-03-25T...",
    "chats": ["chat_id_1", "chat_id_2"]
  }
}
```

**Sessions File** (`data/sessions.json`):

```json
{
  "session_token_hash": {
    "username": "username1",
    "created_at": "2026-03-25T..."
  }
}
```

**User Chats** (`data/user_chats/username_chat_id.json`):

```json
{
  "id": "abc123",
  "username": "username1",
  "title": "Chat from March 25, 2026",
  "created_at": "2026-03-25T...",
  "updated_at": "2026-03-25T...",
  "messages": [
    {
      "role": "user",
      "content": "What is photosynthesis?",
      "timestamp": "2026-03-25T..."
    },
    {
      "role": "assistant",
      "content": "Photosynthesis is...",
      "timestamp": "2026-03-25T..."
    }
  ]
}
```

### Frontend Structure

**New File: `templates/index_new.html`**

- HTML markup for new 3-column layout
- Embedded JavaScript for auth flow
- Chat management
- Message display

**Auth Flow:**

1. Page loads → Check `sessionToken` in localStorage
2. If token exists → Verify with `/api/auth/verify`
3. If valid → Show main app + load chats
4. If invalid → Show login screen
5. Login → Save token → Load chats → Show app

---

## 🔐 Security Notes

1. **Passwords** are hashed with PBKDF2-SHA256 + salt
2. **Session tokens** are cryptographically random 64-char hex strings
3. **Local storage** stores only the session token (never passwords)
4. **Authentication headers** use `Authorization: Bearer {token}`
5. **All endpoints** (except `/api/auth/login`, `/api/auth/register`) require valid session

---

## 🚨 Current Limitations

**Phase 1** (Just Completed):

- ✅ Authentication system
- ✅ Chat history management
- ✅ Basic chat layout
- ❌ AI responses not integrated yet
- ❌ Voice I/O not implemented
- ❌ Model selection UI incomplete
- ❌ File attachments UI incomplete
- ❌ Search, News, Todo, Timer, Notes not ported yet

**These features will be added in Phase 2**

---

## 🔄 Next Steps

### Phase 2: AI Integration

1. Update `/api/chat` endpoint to integrate with new auth
2. Add AI response handling in frontend
3. Auto-save AI responses to chat history
4. Implement model switching

### Phase 3: Features Recovery

1. Port Search feature with auth
2. Port News feature with persistent caching
3. Port Todo, Timer, Notes
4. Port Medical & DECA features

### Phase 4: Polish

1. Voice I/O implementation
2. File attachment improvements
3. Markdown rendering
4. Real-time sync improvements

---

## 📝 Testing Checklist

- [ ] Create new account
- [ ] Login works
- [ ] Create new chat
- [ ] Load existing chat from sidebar
- [ ] Logout works
- [ ] Session persists on page refresh
- [ ] Invalid token redirects to login
- [ ] Chat history displays correctly
- [ ] Message timestamps show

---

## 💡 Tips for Development

**Viewing Backend Data:**

```bash
cat chatbot_hosting_files/data/users.json
cat chatbot_hosting_files/data/sessions.json
cat chatbot_hosting_files/data/user_chats/*.json
```

**Testing Auth Locally:**

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "testpass123"}'

curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

**Testing Protected Endpoints:**

```bash
curl http://localhost:5000/api/chats \
  -H "Authorization: Bearer {session_token}"
```

---

## 🐛 Troubleshooting

**Problem: "Login failed" error**

- Check username/password spelling
- Ensure account was created first (check `data/users.json`)
- Clear browser cache and retry

**Problem: Sessions not persisting**

- Check browser allows localStorage
- Check that `sessionToken` is saved in DevTools → Application → Local Storage
- Clear localStorage and logout/login again

**Problem: Chat not appearing in sidebar**

- Refresh the page
- Check `data/user_chats/` folder for chat files
- Verify the chat file name matches `{username}_{chat_id}.json`

---

## 📞 Questions?

Refer back to:

- [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for Railway deployment
- [README.md](../README.md) for project overview
- [DISCORD_BOT_SETUP.md](../DISCORD_BOT_SETUP.md) for bot setup

---

**Your Derei Assistant now has user accounts and persistent chat history!** 🎉
Next: AI responses integration in Phase 2
