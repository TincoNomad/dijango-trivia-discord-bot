"""
Logging configuration for the Discord bot.

Sets up rotating file handlers for different logging categories:
- Main bot operations
- Command execution
- Game interactions
"""

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_bot_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configure a rotating file logger.

    Args:
        name (str): Logger name
        log_file (str): Log file name
        level (int): Logging level

    Returns:
        logging.Logger: Configured logger instance
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    os.makedirs('logs/bot', exist_ok=True)
    
    handler = RotatingFileHandler(
        f'logs/bot/{log_file}',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    return logger

# Specialized loggers for different components
bot_logger = setup_bot_logger('discord_bot', 'bot.log')
command_logger = setup_bot_logger('bot_commands', 'commands.log')
game_logger = setup_bot_logger('game_interactions', 'game.log')
