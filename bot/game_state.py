from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ProcessType(Enum):
    NONE = "none"
    GAME = "game"
    CREATE = "create"
    UPDATE = "update"

@dataclass
class UserState:
    process_type: ProcessType = ProcessType.NONE
    channel_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

@dataclass
class PlayerGame:
    channel_id: int
    current_score: int
    current_question: int
    selected_trivia: Optional[str] = None
    total_questions: int = 5
    leaderboard_id: Optional[str] = None

"""
Game State Management

Tracks active games, processes and user states.

Features:
- Process tracking (games, creation, updates)
- User state management
- Game progress tracking
"""

class GameState:
    """
    Manages game and process states.
    
    Features:
    - User process tracking
    - Game session management
    - State validation
    
    Attributes:
        user_states (Dict[str, UserState]): Active user processes
        active_games (Dict[int, PlayerGame]): Running game sessions
        user_selections (Dict[int, Dict[str, Any]]): User choices
    """
    def __init__(self):
        self.user_states: Dict[str, UserState] = {}
        self.active_games: Dict[int, PlayerGame] = {}  
        self.user_selections: Dict[int, Dict[str, Any]] = {} 

    def start_process(self, user_id: str, process_type: ProcessType, channel_id: str) -> None:
        """Start a process for a user"""
        self.user_states[user_id] = UserState(
            process_type=process_type,
            channel_id=channel_id
        )
        
    def end_process(self, user_id: str) -> None:
        """End any active process for a user"""
        if user_id in self.user_states:
            del self.user_states[user_id]
            
    def get_user_state(self, user_id: str) -> Optional[UserState]:
        """Get the current state for a user"""
        return self.user_states.get(user_id)
        
    def has_active_process(self, user_id: str) -> bool:
        """Check if user has any active process"""
        return user_id in self.user_states
        
    def can_start_process(self, user_id: str, process_type: ProcessType) -> bool:
        """Check if user can start a new process"""
        current_state = self.get_user_state(user_id)
        return current_state is None or current_state.process_type == ProcessType.NONE
