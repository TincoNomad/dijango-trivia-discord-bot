"""
Discord Bot Client

Manages Discord interactions and command routing.

Features:
- Command handling through Cogs
- Error management with logging
- Rate limit handling
- Game state coordination
"""

from discord.ext import commands
from .trivia_game import TriviaGame
from .api_client import RateLimitExceeded
from .utils.logging_bot import bot_logger
from .commands.trivia_cog import TriviaCog

class DiscordClient(commands.Bot):
    """
    Discord bot client with trivia game functionality.
    
    Features:
    - Automated game flow management
    - Rate limit handling with user feedback
    - Error logging and recovery
    - Command routing through Cogs
    
    Attributes:
        trivia_game (TriviaGame): Game mechanics handler
    """
    
    def __init__(self, command_prefix: str, **options):
        super().__init__(command_prefix=command_prefix, **options)
        self.trivia_game = TriviaGame()
        
    async def handle_rate_limit(self, ctx: commands.Context, error: RateLimitExceeded) -> None:
        """
        Handle rate limit errors from the API
        
        Args:
            ctx: Discord command context
            error: Rate limit exception with details
        """
        await ctx.send(
            f"⚠️ {error.message}\n"
            f"Please try again in {error.wait_seconds} seconds."
        )
        bot_logger.warning(f"Rate limit handled for user {ctx.author}: {error.message}")
        
    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """
        Global error handler for bot commands
        
        Args:
            ctx: Discord command context
            error: The error that occurred
        """
        if isinstance(error, RateLimitExceeded):
            await self.handle_rate_limit(ctx, error)
        else:
            bot_logger.error(f"Command error: {str(error)}")
            await ctx.send("An error occurred while processing your command. Please try again later.")
            
    async def setup_hook(self) -> None:
        """Initialize bot components and load commands"""
        try:
            await self.trivia_game.initialize()
            await self.add_cog(TriviaCog(self))
            bot_logger.info("Bot initialized successfully")
        except RateLimitExceeded as e:
            bot_logger.warning(f"Rate limit during initialization: {e.message}")
            # The bot will still start, but initialization will be retried later
        except Exception as e:
            bot_logger.error(f"Error during bot initialization: {e}")
            raise
