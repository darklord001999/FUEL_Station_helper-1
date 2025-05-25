import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive # For Replit/Render to keep the bot alive

# --- 1. Set up your bot with intents ---
# Intents are crucial for telling Discord what events your bot wants to receive.
intents = discord.Intents.default()
intents.members = True # Enable the server members intent
intents.message_content = True # Enable the message content intent (needed for reading commands)

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    # You can set the bot's status here
    await bot.change_presence(activity=discord.Game(name="Managing Fuel Stations"))

@bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# --- Command: About/Info ---
@bot.command(name='about', help='Provides information about the bot.')
async def about(ctx):
    embed = discord.Embed(
        title="ACRP Fuel Station Bot",
        description=(
            "Your dedicated assistant for the ACRP Fuel Stations, maintained by ungradua.\n\n"
            "**Purpose:** This bot helps manage information related to station status, and provides "
            "utility functions for the ACRP Fuel Station operations.\n\n"
            "**Developed by:** [ungradua]\n"
            "**Version:** 1.0.0\n"
            "**Last Updated:** 1 june 2025" # Update this date regularly
        ),
        color=discord.Color.gold() # You can choose any color
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar.url) # Uses bot's own avatar
    embed.set_footer(text=f"Serving {len(bot.guilds)} servers | Use !help for commands")

    await ctx.send(embed=embed)

# main.py continues here:
if __name__ == "__main__":
    # This will run a simple web server in the background
    keep_alive() 
    # Get the bot token from environment variables
    bot_token = os.environ.get('DISCORD_BOT_TOKEN')
    if bot_token:
        bot.run(bot_token)
    else:
        print("Error: DISCORD_BOT_TOKEN environment variable not set. Please add it to Replit secrets.")