"""
Command handlers for trivia game functionality.

This module contains the core logic for processing trivia commands including:
- Game flow control
- Creation/update operations
- Score tracking
"""

from discord import Message, Client
from .trivia_player import TriviaPlayer
from .trivia_creator import TriviaCreator
from .trivia_updater import TriviaUpdater
from ..game_state import GameState, ProcessType


class TriviaCommands:
    """
    Handles processing and routing of trivia game commands.
    
    Attributes:
        game_state (GameState): Current game state tracker
        game_handler (TriviaPlayer): Handles active game logic
        trivia_creator (TriviaCreator): Handles trivia creation
        trivia_updater (TriviaUpdater): Handles trivia updates
    """

    def __init__(self, client: Client):
        # Initialize command handlers
        self.game_state = GameState()  # Tracks active games and processes
        self.game_handler = TriviaPlayer(client)  # Handles gameplay
        self.trivia_creator = TriviaCreator(client)  # Handles creation
        self.trivia_updater = TriviaUpdater(client, self.game_state)  # Handles updates
        
    async def handle_trivia(self, message: Message) -> None:
        """Route trivia game command to game handler"""
        await self.game_handler.handle_trivia(message)
        
    async def handle_create_trivia(self, message: Message) -> None:
        """Route trivia creation command to creator"""
        await self.trivia_creator.handle_create_trivia(message)
        
    async def handle_score(self, message: Message) -> None:
        """Route score command to game handler"""
        await self.game_handler.handle_score(message)
        
    async def handle_themes(self, message: Message) -> None:
        """Route themes command to game handler"""
        await self.game_handler.handle_themes(message)
        
    async def handle_game_response(self, message: Message) -> None:
        """Route game responses to game handler"""
        await self.game_handler.handle_game_response(message)
        
    async def handle_stop_game(self, message: Message) -> None:
        """Route stop game command to game handler"""
        await self.game_handler.handle_stop_game(message)
        
    async def handle_list_trivias(self, message: Message) -> None:
        """Route trivia listing command to game handler"""
        await self.game_handler.handle_list_trivias(message)
        
    async def handle_update_trivia(self, message: Message) -> None:
        """Route update trivia command to updater"""
        await self.trivia_updater.handle_update_trivia(message)
        
    async def handle_cancel(self, message: Message) -> None:
        """Handle cancel command to stop any active process"""
        user_id = str(message.author.id)
        user_state = self.game_state.get_user_state(user_id)
        
        if not user_state:
            await message.channel.send("❌ No active process to cancel.")
            return
            
        process_type = user_state.process_type
        self.game_state.end_process(user_id)
        
        if process_type == ProcessType.CREATE:
            await message.channel.send("✅ Trivia creation process cancelled.")
        elif process_type == ProcessType.UPDATE:
            await message.channel.send("✅ Trivia update process cancelled.")
        elif process_type == ProcessType.GAME:
            await self.handle_stop_game(message)
        else:
            await message.channel.send("✅ Process cancelled.")