import asyncio
import time
from typing import Any, Dict, List, Optional

import aiohttp
from typing_extensions import Self

from api.settings import (
    BASE_URL,
    FILTER_URL,
    LEADERBOARD_URL,
    QUESTIONS_URL,
    SCORES_URL,
    TRIVIA_URL,
)

from .utils.logging_bot import bot_logger
from .utils.rate_limits import (
    RateLimitExceeded,
    handle_rate_limit_response,
    handle_rate_limit_retry,
)

"""
API Client for Trivia Bot

Handles all API interactions with rate limiting and error handling.

Features:
- CRUD operations for trivias
- Score management
- Leaderboard tracking
- Theme management
- Rate limit handling
"""


class TriviaAPIClient:
    """
    Manages API interactions with rate limiting and retries.

    Features:
    - Automatic rate limit tracking
    - Request retries with exponential backoff
    - CSRF token management
    - SSL verification toggle for development

    Attributes:
        session (Optional[aiohttp.ClientSession]): Active API session
        csrf_token (Optional[str]): Current CSRF token
        base_url (str): API base URL
        ssl_verify (bool): Whether to verify SSL certificates
        rate_limits (Dict[str, float]): Rate limit expiry times by endpoint
    """

    def __init__(self) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.csrf_token: Optional[str] = None
        self.base_url = BASE_URL
        self.ssl_verify = not BASE_URL.startswith("http://")  # Only verify SSL in HTTPS
        self.rate_limits: Dict[str, float] = {}  # endpoint -> expiry time

    async def __aenter__(self) -> Self:
        if self.ssl_verify:
            self.session = aiohttp.ClientSession()
        else:
            bot_logger.warning(
                "SSL verification disabled - Development environment detected"
            )
            self.session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(verify_ssl=False)
            )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any],
    ) -> None:
        if self.session:
            await self.session.close()

    def _track_rate_limit(self, endpoint: str, wait_seconds: int, message: str) -> None:
        """Track rate limit for endpoint"""
        expiry = time.time() + wait_seconds
        self.rate_limits[endpoint] = expiry
        bot_logger.warning(
            f"Rate limit for {endpoint}: {message}. "
            f"Expires in {wait_seconds}s at {time.ctime(expiry)}"
        )

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
    ) -> Any:
        """Enhanced GET with rate limit tracking"""
        if url in self.rate_limits and time.time() < self.rate_limits[url]:
            wait_time = int(self.rate_limits[url] - time.time())
            bot_logger.info(f"Rate limit active for {url}. Waiting {wait_time}s")
            raise RateLimitExceeded(wait_time, "Rate limit still active")

        if self.session is None:
            await self.__aenter__()

        if self.session is None:
            raise RuntimeError("Failed to initialize session")

        async def _make_request():
            async with self.session.get(url, params=params) as response:
                response_data = await response.json()
                if response.status == 429:
                    await handle_rate_limit_response(response, response_data)
                response.raise_for_status()
                return response_data

        try:
            return await handle_rate_limit_retry(_make_request, retry_count=retry_count)
        except RateLimitExceeded as e:
            self._track_rate_limit(url, e.wait_seconds, e.message)
            raise

    async def post(
        self,
        url: str,
        data: Dict[str, Any],
        use_csrf: bool = True,
        retry_count: int = 3,
    ) -> Any:
        """Generic method for making POST requests with rate limit handling"""
        if self.session is None:
            await self.__aenter__()

        if self.session is None:
            raise RuntimeError("Failed to initialize session")

        for attempt in range(retry_count):
            try:
                headers = {"Content-Type": "application/json"}
                if use_csrf:
                    csrf_token = await self.get_csrf_token()
                    if csrf_token is None:
                        raise ValueError("Could not obtain CSRF token")
                    headers["X-CSRFToken"] = csrf_token

                bot_logger.info(f"Making POST request to {url}")
                bot_logger.debug(f"Request data: {data}")
                bot_logger.debug(f"Headers: {headers}")

                async with self.session.post(
                    url, json=data, headers=headers
                ) as response:
                    response_data = await response.json()

                    if response.status == 429:  # Rate limit exceeded
                        await handle_rate_limit_response(response, response_data)

                    response.raise_for_status()
                    return response_data

            except RateLimitExceeded as e:
                if attempt < retry_count - 1:
                    wait_time = e.wait_seconds
                    bot_logger.info(f"Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            except Exception as e:
                bot_logger.error(f"Error in POST request to {url}: {str(e)}")
                raise

    async def get_csrf_token(self) -> Optional[str]:
        """Gets the CSRF token from the server"""
        if self.session is None:
            await self.__aenter__()

        if self.session is None:
            raise RuntimeError("Failed to initialize session")

        try:
            async with self.session.get(SCORES_URL) as response:
                csrf_cookie = response.cookies.get("csrftoken")
                if csrf_cookie is None:
                    bot_logger.error("CSRF token not found in cookies")
                    return None

                self.csrf_token = csrf_cookie.value
                return self.csrf_token
        except Exception as e:
            bot_logger.error(f"Error obtaining CSRF token: {e}")
            return None

    async def fetch_trivia_questions(self) -> List[Dict[str, Any]]:
        """Gets trivia questions from the API"""
        return await self.get(QUESTIONS_URL)

    async def get_filtered_trivias(
        self, theme: str, difficulty: int
    ) -> List[Dict[str, Any]]:
        """Gets filtered trivia questions by theme and difficulty"""
        try:
            params = {"theme": theme, "difficulty": difficulty}
            bot_logger.info(f"Requesting filtered trivias with params: {params}")
            return await self.get(FILTER_URL, params=params)
        except aiohttp.ClientResponseError as e:
            if e.status in [401, 403]:
                bot_logger.error("Unauthorized access to filtered trivias endpoint")
                raise ValueError("Unauthorized access")
            bot_logger.error(f"Error getting filtered trivias: {e}")
            raise
        except Exception as e:
            bot_logger.error(f"Error getting filtered trivias: {e}")
            raise

    async def get_leaderboard(self, discord_channel: str) -> Dict[str, Any]:
        """Gets the score table for a specific discord channel

        Args:
            discord_channel (str): The discord channel identifier

        Returns:
            Dict[str, Any]: A dictionary containing the leaderboard data with scores

        Raises:
            ValueError: If the channel is not found
            Exception: For other API errors
        """
        try:
            bot_logger.info(f"Requesting leaderboard for channel: {discord_channel}")
            params = {"channel": discord_channel}
            response = await self.get(LEADERBOARD_URL, params)
            bot_logger.debug(f"Leaderboard response: {response}")
            return response
        except Exception as e:
            bot_logger.error(
                f"Error getting leaderboard for channel {discord_channel}: {e}"
            )
            raise

    async def update_score(self, name: str, points: int, discord_channel: str):
        """Updates the score using CSRF token"""
        try:
            data = {
                "name": name,
                "points": points,
                "discord_channel": discord_channel,
            }

            response = await self.post(f"{self.base_url}/api/score/", data)

            # Verify successful response
            if (
                "message" in response
                and response["message"] == "Score updated successfully"
            ):
                bot_logger.info(
                    f"Score updated successfully - User: {name}, "
                    f"Points: {points}, Channel: {discord_channel}"
                )
                return response["data"]

            # If the response is not in the expected format
            bot_logger.error(f"Unexpected response from server: {response}")
            raise ValueError("Unexpected error updating score")

        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                bot_logger.error(
                    f"User or channel not found: {name}, {discord_channel}"
                )
                raise ValueError("User or channel not found")
            elif e.status in [401, 403]:
                bot_logger.error("Authorization error updating score")
                raise ValueError("Authorization error")
            elif e.status == 400:
                bot_logger.error(f"Invalid data sent to server: {data}")
                raise ValueError("Invalid data for updating score")
            else:
                bot_logger.error(f"Server error updating score: {e}")
                raise
        except aiohttp.ClientError as e:
            bot_logger.error(f"Connection error updating score: {e}")
            raise ValueError("Connection error with the server")
        except Exception as e:
            bot_logger.error(f"Unexpected error updating score: {e}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def create_leaderboard(
        self, discord_channel: str, username: str
    ) -> Dict[str, Any]:
        """Creates a new leaderboard for the channel"""
        data = {"discord_channel": discord_channel, "username": username}
        return await self.post(LEADERBOARD_URL, data)

    async def get_user_trivias(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Gets trivias created by a specific user

        Args:
            params (Dict[str, str]): Query parameters including username

        Returns:
            List[Dict[str, Any]]: List of trivias created by the user

        Raises:
            Exception: If there is an error getting the trivias
        """
        try:
            bot_logger.info(f"Getting trivias for user with params: {params}")
            response = await self.get(TRIVIA_URL, params)
            bot_logger.debug(f"Got trivias response: {response}")
            return response
        except Exception as e:
            bot_logger.error(f"Error getting user trivias: {e}")
            raise

    async def update_trivia(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Updates a trivia question

        Args:
            data (Dict[str, Any]): Update data including trivia_id and username

        Returns:
            Dict[str, Any]: Updated trivia data

        Raises:
            Exception: If there is an error updating the trivia
        """
        try:
            trivia_id = data.pop("trivia_id")
            username = data.pop("username")

            # Handle theme update if present
            if "theme" in data:
                theme_name = data["theme"]
                # If it's not a UUID, try to get or create the theme
                if not isinstance(theme_name, str) or len(theme_name) != 36:
                    theme_data = await self.get_or_create_theme(theme_name)
                    data["theme"] = theme_data["id"]

            bot_logger.info(f"Updating trivia {trivia_id} with data: {data}")
            return await self.patch_trivia(trivia_id, data, username)

        except Exception as e:
            bot_logger.error(f"Error updating trivia: {e}")
            raise

    async def patch(self, url: str, data: Dict[str, Any]) -> Any:
        """Generic method for making PATCH requests"""
        if self.session is None:
            await self.__aenter__()

        if self.session is None:
            raise RuntimeError("Failed to initialize session")

        try:
            headers = {"Content-Type": "application/json"}

            bot_logger.info(f"Making PATCH request to {url}")
            bot_logger.debug(f"Request data: {data}")

            async with self.session.patch(url, json=data, headers=headers) as response:
                response_text = await response.text()
                bot_logger.debug(f"Response status: {response.status}")
                bot_logger.debug(f"Response text: {response_text}")

                response.raise_for_status()
                return await response.json()
        except Exception as e:
            bot_logger.error(f"Error in PATCH request to {url}: {str(e)}")
            raise

    async def patch_trivia(
        self, trivia_id: str, data: Dict[str, Any], username: str
    ) -> Dict[str, Any]:
        """Updates a trivia partially"""
        try:
            bot_logger.info(f"Sending PATCH request to update trivia {trivia_id}")
            bot_logger.debug(f"Update data: {data}")

            # Add username as query param
            url = f"{TRIVIA_URL}{trivia_id}/?username={username}"

            response = await self.patch(url, data)
            bot_logger.info(f"Successfully updated trivia {trivia_id}")
            bot_logger.debug(f"API response: {response}")
            return response
        except Exception as e:
            bot_logger.error(f"Error updating trivia {trivia_id}: {str(e)}")
            raise

    async def update_trivia_questions(
        self, trivia_id: str, questions_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Updates questions and answers for a trivia

        Args:
            trivia_id (str): ID of the trivia to update
            questions_data (List[Dict[str, Any]]): Questions and answers data to update

        Returns:
            Dict[str, Any]: Response from the API

        Raises:
            Exception: If there is an error updating the questions
        """
        try:
            data = {"questions": questions_data}
            bot_logger.info(f"Updating questions for trivia {trivia_id}")
            bot_logger.debug(f"Questions data: {questions_data}")

            response = await self.patch(
                f"{TRIVIA_URL}{trivia_id}/update_questions/", data
            )
            bot_logger.debug(f"Update questions response: {response}")
            return response
        except Exception as e:
            bot_logger.error(f"Error updating trivia questions: {e}")
            raise

    async def get_trivia_info(self, trivia_id: str) -> Dict[str, Any]:
        """Gets detailed information about a trivia"""
        try:
            url = f"{TRIVIA_URL}{trivia_id}/"
            return await self.get(url)
        except Exception as e:
            bot_logger.error(f"Error getting trivia info: {e}")
            raise

    async def get_trivia_questions(self, trivia_id: str) -> List[Dict[str, Any]]:
        """Gets questions for a specific trivia"""
        try:
            url = f"{BASE_URL}/api/questions/{trivia_id}/"
            return await self.get(url)
        except Exception as e:
            bot_logger.error(f"Error getting trivia questions: {e}")
            raise

    async def get_themes(self) -> List[Dict[str, Any]]:
        """Gets all available themes

        Returns:
            List[Dict[str, Any]]: List of themes with their IDs and names

        Raises:
            Exception: If there is an error getting the themes
        """
        try:
            url = f"{self.base_url}/api/themes/"
            return await self.get(url)
        except Exception as e:
            bot_logger.error(f"Error getting themes: {e}")
            raise

    async def create_theme(self, name: str) -> Dict[str, Any]:
        """Creates a new theme

        Args:
            name (str): Name of the new theme

        Returns:
            Dict[str, Any]: Created theme data

        Raises:
            Exception: If there is an error creating the theme
        """
        try:
            url = f"{self.base_url}/api/themes/"
            data = {"name": name}
            return await self.post(url, data)
        except Exception as e:
            bot_logger.error(f"Error creating theme: {e}")
            raise

    async def get_or_create_theme(self, theme_name: str) -> Dict[str, Any]:
        """Gets an existing theme by name or creates a new one

        Args:
            theme_name (str): Name of the theme to get or create

        Returns:
            Dict[str, Any]: Theme data

        Raises:
            Exception: If there is an error with the theme operation
        """
        try:
            # First try to find the theme
            themes = await self.get_themes()
            for theme in themes:
                if theme["name"].lower() == theme_name.lower():
                    return theme

            # If not found, create it
            return await self.create_theme(theme_name)
        except Exception as e:
            bot_logger.error(f"Error in get_or_create_theme: {e}")
            raise
