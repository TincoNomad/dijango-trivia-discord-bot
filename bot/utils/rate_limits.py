"""
Rate limiting utilities for API interactions.

Provides:
- Rate limit exception handling
- Exponential backoff implementation
- Retry mechanisms for rate-limited requests
"""

import logging
from typing import Optional
import asyncio
from aiohttp import ClientResponse

# Configure logging
logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """
    Exception raised when API rate limits are hit.

    Attributes:
        wait_seconds (int): Seconds to wait before retry
        message (str): Error message
        retry_after (str): Raw retry-after header value
    """
    def __init__(self, wait_seconds: int, message: str, retry_after: Optional[str] = None):
        self.wait_seconds = wait_seconds
        self.message = message
        self.retry_after = retry_after
        super().__init__(message)

async def handle_rate_limit_response(response: ClientResponse, response_data: dict) -> None:
    """
    Process rate limit response from API.

    Args:
        response (ClientResponse): API response object
        response_data (dict): Parsed response data

    Raises:
        RateLimitExceeded: With retry information
    """
    retry_after = response.headers.get('Retry-After')
    wait_seconds = int(retry_after) if retry_after else 60
    message = response_data.get('message', 'Rate limit exceeded')
    
    logger.warning(f"Rate limit exceeded: {message}, Retry-After: {retry_after}")
    raise RateLimitExceeded(
        wait_seconds=wait_seconds,
        message=message,
        retry_after=retry_after
    )

def calculate_backoff_time(attempt: int, base_wait: int = 1) -> int:
    """Calculate exponential backoff time"""
    max_wait = 300  # 5 minutes maximum
    return min(max_wait, base_wait * (2 ** attempt))

async def handle_rate_limit_retry(func, *args, retry_count: int = 3, **kwargs):
    """Generic rate limit retry handler"""
    for attempt in range(retry_count):
        try:
            return await func(*args, **kwargs)
        except RateLimitExceeded as e:
            if attempt < retry_count - 1:
                backoff_time = calculate_backoff_time(attempt, e.wait_seconds)
                logger.info(f"Rate limit backoff: {backoff_time}s (Attempt {attempt + 1}/{retry_count})")
                await asyncio.sleep(backoff_time)
                continue
            raise