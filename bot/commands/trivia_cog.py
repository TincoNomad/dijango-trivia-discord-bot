"""
Discord Cog for handling trivia game commands.

This cog provides command handlers for all trivia-related functionality including:
- Starting/stopping games
- Creating/updating trivias
- Showing scores and listings
"""

from discord.ext import commands
from .trivia_commands import TriviaCommands

class TriviaCog(commands.Cog):
    """
    Cog that handles all trivia-related commands and events.
    
    Attributes:
        bot (commands.Bot): The Discord bot instance
        trivia_commands (TriviaCommands): Handler for trivia command logic
    """

    def __init__(self, bot: commands.Bot):
        """
        Initialize the TriviaCog.

        Args:
            bot (commands.Bot): The Discord bot instance
        """
        self.bot = bot
        self.trivia_commands = TriviaCommands(bot)

    # Command handlers with descriptive docstrings
    @commands.command()
    async def trivia(self, ctx: commands.Context):
        """Start a new trivia game session."""
        await self.trivia_commands.handle_trivia(ctx.message)

    @commands.command()
    async def list_trivia(self, ctx: commands.Context):
        """Show available trivias"""
        await self.trivia_commands.handle_list_trivias(ctx.message)

    @commands.command()
    async def score(self, ctx: commands.Context):
        """Show current score"""
        await self.trivia_commands.handle_score(ctx.message)

    @commands.command()
    async def stop_game(self, ctx: commands.Context):
        """Stop current game"""
        await self.trivia_commands.handle_stop_game(ctx.message)

    @commands.command()
    async def create_trivia(self, ctx: commands.Context):
        """Create a new trivia game"""
        await self.trivia_commands.handle_create_trivia(ctx.message)

    @commands.command()
    async def update_trivia(self, ctx: commands.Context):
        """Update an existing trivia"""
        await self.trivia_commands.handle_update_trivia(ctx.message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❌ Command not found. Available commands:\n" +
                         "`$trivia` - Start a game\n" +
                         "`$list_trivia` - Show available trivias\n" +
                         "`$score` - Show current score\n" +
                         "`$stop_game` - Stop current game\n" +
                         "`$create_trivia` - Create new trivia\n" +
                         "`$update_trivia` - Update existing trivia")
        else:
            await ctx.send("❌ An error occurred while processing your command.")