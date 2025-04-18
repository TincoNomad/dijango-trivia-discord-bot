"""
Trivia Game Logic

Manages game mechanics and scoring.

Features:
- Question management
- Score calculation
- Theme and difficulty handling
- Game progression tracking
"""

from typing import Any, Dict, List, Optional, Tuple

from api.settings import TRIVIA_URL

from .api_client import RateLimitExceeded, TriviaAPIClient
from .utils.logging_bot import game_logger
from .utils.utils import get_difficulty_list, get_theme_list

POINTS_PER_CORRECT_ANSWER = 10


class TriviaGame:
    """
    Core game mechanics handler.

    Features:
    - Question retrieval and validation
    - Score tracking
    - Game flow control
    - Rate limit handling

    Attributes:
        api_client (TriviaAPIClient): API interaction handler
        game_data (List[Dict[str, Any]]): Active game data
        current_trivia (List[Dict[str, Any]]): Current trivia questions
        difficulty_choices (Dict[int, str]): Available difficulties
        theme_choices (Dict[int, Dict[str, Any]]): Available themes
    """

    def __init__(self) -> None:
        self.api_client = TriviaAPIClient()
        self.game_data: List[Dict[str, Any]] = []
        self.current_trivia: List[Dict[str, Any]] = []
        self.difficulty_choices: Dict[int, str] = {}
        self.difficulty_choice: Optional[int] = None
        self.theme_choices: Dict[int, Dict[str, Any]] = {}

    async def handle_rate_limit(self, e: RateLimitExceeded) -> str:
        """Format user-friendly rate limit messages"""
        wait_time = e.wait_seconds
        if wait_time > 60:
            minutes = wait_time // 60
            return (
                f"⏳ Please wait {minutes} minutes before trying again. "
                "The bot is cooling down."
            )
        return (
            f"⏳ Please wait {wait_time} seconds before trying again. "
            "The bot is cooling down."
        )

    async def initialize(self) -> None:
        """Initialize the trivia game by fetching necessary data"""
        try:
            self.game_data = await self.api_client.get(TRIVIA_URL)
            _, self.difficulty_choices = await get_difficulty_list()
            _, self.theme_choices = await get_theme_list()
            game_logger.info("Trivia game initialized successfully")
        except RateLimitExceeded as e:
            error_msg = await self.handle_rate_limit(e)
            game_logger.warning(f"Rate limit during initialization: {error_msg}")
            raise RateLimitExceeded(e.wait_seconds, error_msg, e.retry_after)
        except Exception as e:
            game_logger.error(f"Failed to initialize trivia game: {e}")
            raise

    async def get_available_options(self) -> Tuple[str, str]:
        """
        Returns the formatted lists of themes and difficulties available

        Returns:
            Tuple[str, str]: Theme list and difficulty list

        Raises:
            RateLimitExceeded: If API rate limit is exceeded
            Exception: For other errors
        """
        try:
            theme_list, theme_dict = await get_theme_list()
            self.theme_choices = theme_dict
            difficulty_list, _ = await get_difficulty_list()
            return theme_list, difficulty_list
        except RateLimitExceeded as e:
            error_msg = await self.handle_rate_limit(e)
            game_logger.warning(f"Rate limit getting options: {error_msg}")
            raise RateLimitExceeded(e.wait_seconds, error_msg, e.retry_after)
        except Exception as e:
            game_logger.error(f"Error getting game options: {e}")
            raise

    async def get_trivia(self, theme_id: str, difficulty_level: int) -> Tuple[str, int]:
        try:
            filtered_trivias = await self.api_client.get_filtered_trivias(
                theme_id, difficulty_level
            )
            game_logger.debug(f"Filtered trivias: {filtered_trivias}")

            if not filtered_trivias:
                return "No trivias available for this combination", 0

            trivia_list = "\n".join(
                f"{idx + 1}- {trivia['title']} {'🔗' if trivia.get('url') else ''}"
                for idx, trivia in enumerate(filtered_trivias)
            )

            return trivia_list, len(filtered_trivias)

        except RateLimitExceeded as e:
            error_msg = await self.handle_rate_limit(e)
            game_logger.warning(
                f"Rate limit hit for theme={theme_id}, difficulty={difficulty_level}: "
                "{error_msg}"
            )
            return error_msg, 0
        except Exception as e:
            game_logger.error(f"Error getting trivia: {e}")
            raise

    async def get_trivia_info(self, trivia_id: str) -> Dict[str, Any]:
        """Gets detailed information about a trivia"""
        try:
            return await self.api_client.get_trivia_info(trivia_id)
        except RateLimitExceeded as e:
            error_msg = await self.handle_rate_limit(e)
            game_logger.warning(f"Rate limit getting trivia info: {error_msg}")
            raise RateLimitExceeded(e.wait_seconds, error_msg, e.retry_after)
        except Exception as e:
            game_logger.error(f"Error getting trivia info: {e}")
            raise

    async def get_trivia_questions(self, trivia_id: str) -> List[Dict[str, Any]]:
        """Gets questions for a specific trivia"""
        try:
            questions = await self.api_client.get_trivia_questions(trivia_id)

            if not questions:
                game_logger.warning(f"No questions found for trivia {trivia_id}")
                return []

            game_logger.info(
                f"Retrieved {len(questions)} questions for trivia {trivia_id}"
            )
            return questions

        except RateLimitExceeded as e:
            error_msg = await self.handle_rate_limit(e)
            game_logger.warning(f"Rate limit getting questions: {error_msg}")
            raise RateLimitExceeded(e.wait_seconds, error_msg, e.retry_after)
        except Exception as e:
            game_logger.error(f"Error getting trivia questions: {e}")
            raise

    def get_question(
        self, questions: List[Dict], question_counter: int
    ) -> Tuple[str, int, int, List[str]]:
        try:
            if not questions or question_counter >= len(questions):
                game_logger.error(
                    f"No questions found or invalid counter: {question_counter}"
                )
                return "Error getting the question", 0, 0, []

            question = questions[question_counter]
            correct_answer = next(
                (i + 1 for i, a in enumerate(question["answers"]) if a["is_correct"]),
                0,
            )

            answer_options = [
                f"{i+1}. {answer['answer_title']}"
                for i, answer in enumerate(question["answers"])
            ]

            return (
                question["question_title"],
                correct_answer,
                question["points"],
                answer_options,
            )

        except Exception as e:
            game_logger.error(f"Error getting question: {e}")
            return "Error processing question data", 0, 0, []

    def get_link(self, selected_trivia: str) -> Optional[str]:
        """Gets the course URL for the selected trivia"""
        try:
            trivia = next(
                (
                    trivia
                    for trivia in self.current_trivia
                    if trivia["title"] == selected_trivia
                ),
                None,
            )
            if trivia:
                game_logger.debug(f"Found trivia: {trivia}")
                url = trivia.get("url")
                if url:
                    game_logger.debug(f"Found URL: {url}")
                    return url
                else:
                    game_logger.debug("No URL found in trivia data")
            else:
                game_logger.debug(f"No trivia found with title: {selected_trivia}")
            return None
        except Exception as e:
            game_logger.error(f"Error getting trivia link: {e}")
            return None

    async def set_difficulty(self, difficulty: int) -> None:
        """Sets the selected difficulty for the game"""
        if difficulty not in [1, 2, 3]:
            raise ValueError("Invalid difficulty")
        self.difficulty_choice = difficulty
        game_logger.debug(f"Difficulty set to: {difficulty}")
