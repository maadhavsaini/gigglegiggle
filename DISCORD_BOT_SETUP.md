# Discord Bot Setup Guide

## 🤖 Derei Discord Bot

Your Derei AI assistant is now available on Discord! Students can ask questions directly in Discord without leaving their server.

---

## ✅ Quick Setup (5 minutes)

### **Step 1: Create Discord Application**

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → Name it **"Derei"**
3. Go to **"Bot"** tab → Click **"Add Bot"**
4. Under **"TOKEN"**, click **"Copy"** to copy your bot token
5. **Save this token** — you'll need it next

### **Step 2: Configure Bot Permissions**

In the **Bot** tab, scroll down to **"Privileged Gateway Intents"** and **enable:**

- ✅ **Message Content Intent** (required to read messages)
- ✅ **Server Members Intent** (optional, for user info)

### **Step 3: Get OAuth2 Invite Link**

1. Go to **OAuth2** → **URL Generator**
2. Under **Scopes**, select: `bot`
3. Under **Permissions**, select:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Messages/View Channels
4. **Copy the generated URL** at the bottom
5. **Open that URL in your browser** and invite Derei to your Discord server

---

## 🔧 Configure Your Environment

### **Locally (during development)**

Create or update `.env` in `chatbot_hosting_files/`:

```env
DISCORD_TOKEN=your_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
```

### **Railway (production)**

In the Railway dashboard, add these **Variables**:

```
DISCORD_TOKEN=your_bot_token_here
```

(GROQ_API_KEY should already be set from earlier)

---

## 🚀 Run the Bot

### **Locally**

```bash
cd chatbot_hosting_files
pip install -r requirements.txt
python discord_bot.py
```

You should see:

```
✅ Derei Discord Bot is online as Derei#1234
```

### **Deploy to Railway (Optional - Separate Service)**

If you want to run the bot 24/7 on Railway:

1. In Railway dashboard, create a **new service** for this project
2. Set start command: `python chatbot_hosting_files/discord_bot.py`
3. Add `DISCORD_TOKEN` variable
4. Deploy

---

## 💬 Using the Bot

Once the bot is running in your Discord server, use these commands:

### `/ask <question>`

Ask Derei anything. The bot will respond:

```
/ask What is photosynthesis?
→ Derei replies with a full explanation
```

### `/ask How do I solve this DECA problem?`

Get help with case studies:

```
/ask Help me understand DECA's pricing strategy
→ Derei walks you through the framework
```

### `/ask Explain meiosis`

Medical/biology questions:

```
/ask What are the differences between mitosis and meiosis?
→ Detailed comparison
```

### `/clear`

Reset your conversation history:

```
/clear
→ Your chat history with Derei is wiped
```

### `/derei`

Get bot info:

```
/derei
→ Shows available commands and features
```

---

## 📊 Bot Features

✅ **Multi-turn conversations** — Derei remembers context within your session
✅ **Beautiful embeds** — Formatted responses with colors
✅ **Smart trimming** — Long responses fit Discord's 2000-character limit
✅ **Error handling** — Graceful failures with helpful tips
✅ **Privacy** — No persistent history storage (starts fresh on restart)
✅ **Low latency** — Uses Groq's fastest models

---

## 🔒 Security & Privacy Notes

1. **Never share your bot token** — Treat it like a password
2. **Keep GROQ_API_KEY secret** — Don't commit to GitHub
3. **History per session** — Resets when bot restarts; no database storage
4. **Rate limiting** — Groq API has built-in quotas; monitor at [console.groq.com](https://console.groq.com)

---

## ❌ Troubleshooting

### **Bot is offline / not responding**

```bash
# Check if bot is running
python discord_bot.py

# If you see an error about DISCORD_TOKEN
# → Make sure .env file exists and has the token
# → Or add DISCORD_TOKEN to Railway Variables
```

### **"Unauthorized" error**

- Check that your bot token is correct (copy from Developer Portal again)
- Make sure bot has permission to send messages in the channel

### **Bot says "Missing GROQ_API_KEY"**

- Add `GROQ_API_KEY` to `.env` (locally) or Railway Variables (production)
- Ensure it's a valid API key from [console.groq.com](https://console.groq.com)

### **Responses are slow**

- This is normal for Groq API (100-500ms depending on model load)
- If consistently >5s, check your internet connection or Groq status

### **Bot command isn't working**

- Make sure you use `/` (slash command), not just `ask`
- Try typing `/` to see available commands
- Derei must have "Send Messages" permission in that channel

---

## 🎯 Next Steps

1. ✅ Run `python discord_bot.py` locally
2. ✅ Test with `/ask "Hello Derei"` in Discord
3. ✅ Share your server link with friends to test
4. ✅ (Optional) Deploy bot to Railway for 24/7 uptime

---

## 📝 Advanced: Customizing the Bot

### **Change the system prompt**

Edit `discord_bot.py`, line ~35:

```python
SYSTEM_PROMPT = (
    "Your new custom instructions here..."
)
```

### **Add new commands**

Add to `discord_bot.py`:

```python
@bot.command(name="mycommand")
async def my_new_command(ctx, *, arg):
    """Description of command"""
    # Your code here
    await ctx.send("Response")
```

### **Change bot status/presence**

Line ~110 in `discord_bot.py`:

```python
await bot.change_presence(
    activity=discord.Activity(
        type=discord.ActivityType.playing,
        name="your custom status"
    )
)
```

---

## 🐛 Debug Mode

Set logging to DEBUG level in `discord_bot.py` to see detailed logs:

```python
logging.basicConfig(level=logging.DEBUG)
```

---

**Questions?** Check the main [README.md](../README.md) or [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)

**Happy studying on Discord!** 🚀
