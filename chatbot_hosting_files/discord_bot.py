"""
Derei Discord Bot
Allows users to chat with Derei AI directly from Discord
"""

import discord
from discord.ext import commands
from groq import Groq
from dotenv import load_dotenv
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN. Add it to .env or Railway Variables.")
if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY. Add it to .env or Railway Variables.")

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix="/", intents=intents)

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# Bot configuration
MAX_RESPONSE_LENGTH = 2000  # Discord message limit
SYSTEM_PROMPT = (
    "You are Derei, a student's study partner—think of me as that friend who knows their stuff. "
    "When I ask a lazy question, challenge me (gently). I learn by struggling. "
    "Explain the 'why,' not just the 'how.' Deep understanding > quick answers. "
    "If you don't know, say so. Confidence is earned, not faked. "
    "Be direct. No fluff, no corporate speak. Casual > formal. "
    "Use humor when it helps. Never talk down to me."
)

# User conversation history (stored per Discord user)
user_history = {}
MAX_HISTORY_LENGTH = 10


def get_user_history(user_id):
    """Get or create conversation history for a user"""
    if user_id not in user_history:
        user_history[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return user_history[user_id]


def trim_response(text, max_length=MAX_RESPONSE_LENGTH):
    """Trim response to Discord message limit"""
    if len(text) <= max_length:
        return text
    
    # Try to cut at a sentence boundary
    trimmed = text[:max_length - 100]
    last_period = trimmed.rfind(".")
    if last_period > max_length - 200:
        trimmed = text[:last_period + 1]
    
    return trimmed + "\n\n*(message truncated)*"


def ask_derei(user_id, message):
    """Send a message to Derei and get a response"""
    try:
        history = get_user_history(user_id)
        
        # Add user message to history
        history.append({"role": "user", "content": message})
        
        # Keep history manageable
        if len(history) > MAX_HISTORY_LENGTH + 1:
            # Keep system prompt + last N messages
            history = [history[0]] + history[-(MAX_HISTORY_LENGTH):]
            user_history[user_id] = history
        
        # Get response from Groq
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=history,
            max_tokens=1000,
            temperature=0.7,
        )
        
        reply = response.choices[0].message.content
        
        # Add assistant response to history
        history.append({"role": "assistant", "content": reply})
        
        return reply
    
    except Exception as e:
        logger.error(f"Error in ask_derei: {str(e)}")
        return f"❌ Error: {str(e)}\n\nTip: Make sure your Groq API key is valid."


@bot.event
async def on_ready():
    """Bot is ready"""
    logger.info(f"✅ Derei Discord Bot is online as {bot.user}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/ask <question>"
        )
    )


@bot.command(
    name="ask",
    description="Ask Derei AI a question"
)
async def ask_command(ctx, *, question: str):
    """
    /ask <question>
    Ask Derei a question and get an instant response
    """
    
    # Show that we're thinking
    async with ctx.typing():
        response = ask_derei(ctx.author.id, question)
        response = trim_response(response)
    
    # Create embed for nice formatting
    embed = discord.Embed(
        title="Derei Says:",
        description=response,
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Asked by {ctx.author.name}")
    
    await ctx.send(embed=embed)
    logger.info(f"{ctx.author} asked: {question[:50]}...")


@bot.command(
    name="clear",
    description="Clear your conversation history with Derei"
)
async def clear_command(ctx):
    """Clear conversation history"""
    if ctx.author.id in user_history:
        user_history[ctx.author.id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    embed = discord.Embed(
        title="History Cleared",
        description="Your conversation history with Derei has been reset.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
    logger.info(f"{ctx.author} cleared their history")


@bot.command(
    name="derei",
    description="Get info about Derei"
)
async def derei_info(ctx):
    """Show info about Derei bot"""
    embed = discord.Embed(
        title="🤖 Derei Discord Bot",
        description="Your AI study partner, now on Discord!",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="Available Commands",
        value="`/ask <question>` - Ask Derei anything\n`/clear` - Clear your history\n`/derei` - Show this message",
        inline=False
    )
    embed.add_field(
        name="How to Use",
        value="Type `/ask ` and write your question. Derei will respond with helpful, student-focused answers.",
        inline=False
    )
    embed.add_field(
        name="Topics",
        value="📚 DECA prep • 🔬 Medical terms • 💻 Programming • 📖 General learning • ✍️ Essay feedback • 🧮 Math help",
        inline=False
    )
    embed.add_field(
        name="Privacy",
        value="Your conversation history is stored only for this session and is deleted when the bot restarts.",
        inline=False
    )
    embed.set_footer(text="Made with Groq API | Study Smarter, Not Just Faster")
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="❌ Missing Arguments",
            description="Use `/ask <your question here>`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        # Silently ignore unknown commands
        pass
    else:
        logger.error(f"Command error: {str(error)}")
        embed = discord.Embed(
            title="❌ Error",
            description=f"Something went wrong: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)


# Run the bot
if __name__ == "__main__":
    logger.info("Starting Derei Discord Bot...")
    bot.run(DISCORD_TOKEN)
