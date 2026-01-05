"""
Bot Entry Point

Configures and launches the Discord bot with required intents.

Usage:
    python -m bot.main
"""

import os
import discord
from dotenv import load_dotenv
from bot.discord_client import DiscordClient

# Set up Discord bot connection
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with command prefix '$'
client = DiscordClient(command_prefix='$', intents=intents)

# Run the Discord bot
client.run(os.getenv('DISCORD_KEY')) #type: ignore