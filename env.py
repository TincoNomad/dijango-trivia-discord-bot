"""
Environment Configuration Module

Purpose:
    Manages environment variables and configuration settings
    for the Trivia application.

Features:
    - Environment detection
    - Debug configuration
    - Security key management
    - Database credentials
    - API settings

Author: Renzo Tincopa
Last Updated: 2024
"""

import os

import environ  # type: ignore

# Initialize environ with default values
env = environ.Env()

# Read the .env file from project root
environ.Env.read_env(os.path.join(os.path.dirname(__file__), ".env"))

# Environment detection
IS_PRODUCTION = not env("DEBUG", cast=bool)
IS_DEVELOPMENT = env("DEBUG", cast=bool)

# Validation
assert env("SECRET_KEY"), "SECRET_KEY must be set"
assert env("SIGNING_KEY"), "SIGNING_KEY must be set"

# OpenAI validation
assert env("OPENAI_API_KEY"), "OPENAI_API_KEY must be set"


# URL Configuration based on environment
def get_base_url() -> str:
    # Get URL from environment and ensure it's a string
    url: str = str(env("URL"))  # Force string type
    protocol: str = "https" if IS_PRODUCTION else "http"

    # Now Pylance knows url is definitely a string
    if isinstance(url, str) and "://" in url:
        url = url.split("://")[1]

    return f"{protocol}: //{url}"


BASE_URL = get_base_url()
