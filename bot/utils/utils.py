"""
Core utility functions for the trivia bot.

Provides helper functions for:
- Theme management
- Difficulty level handling
- API interaction utilities
"""

import logging
from ..api_client import TriviaAPIClient
from typing import Tuple, Dict, Any

# Constants for game configuration
TIMEOUT_DURATION = 30  # Seconds to wait for user input
MAX_QUESTIONS = 5     # Maximum questions per game
POINTS_PER_CORRECT_ANSWER = 10  # Points awarded per correct answer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_theme_list() -> Tuple[str, Dict[int, Dict[str, Any]]]:
    """
    Fetch and format available trivia themes.

    Returns:
        Tuple containing:
        - str: Formatted theme list for display
        - Dict: Theme mapping with IDs and names

    Raises:
        Exception: If theme retrieval fails
    """
    try:
        async with TriviaAPIClient() as client:
            themes = await client.get_themes()
            
            theme_dict = {i+1: {'id': theme['id'], 'name': theme['name']} 
                         for i, theme in enumerate(themes)}
            
            theme_list = "\n".join(
                f"{num}- {theme['name']}" 
                for num, theme in theme_dict.items()
            )
            
            return theme_list, theme_dict
    except Exception as e:
        logger.error(f"Error getting theme list: {e}")
        raise

async def get_difficulty_list() -> Tuple[str, Dict[int, str]]:
    """
    Fetch and format available difficulty levels.

    Returns:
        Tuple containing:
        - str: Formatted difficulty list for display
        - Dict: Difficulty level mapping

    Raises:
        Exception: If difficulty retrieval fails
    """
    try:
        async with TriviaAPIClient() as client:
            difficulties = await client.get_difficulties()
            
            difficulty_list = "\n".join(
                f"{level}- {name}" 
                for level, name in difficulties.items()
            )
            
            return difficulty_list, difficulties
    except Exception as e:
        logger.error(f"Error getting difficulty list: {e}")
        raise