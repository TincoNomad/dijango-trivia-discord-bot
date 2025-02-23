"""
AI Generator Test Module

This module contains test cases for:
- AI trivia generation
- AI response validation
- Error handling for AI generation
"""

from unittest.mock import AsyncMock, patch

import pytest
from django.urls import reverse

# from django.core.exceptions import ValidationError
# from rest_framework.exceptions import APIException
from rest_framework import status

# from ..services.ai_generator import TriviaAIGenerator


@pytest.mark.asyncio
class TestAIGenerator:
    """Test cases for AI-powered trivia generation"""

    @pytest.fixture
    def mock_openai_response(self):
        return {
            "choices": [
                {
                    "message": {
                        "content": (
                            "{"
                            '"question": "What is Python?", '
                            '"options": ['
                            '"A programming language", '
                            '"A snake", '
                            '"A bird", '
                            '"A car"'
                            "], "
                            '"correct_answer": "A programming language", '
                            '"explanation": "Python is a high-level programming language."'
                            "}"
                        )
                    }
                }
            ]
        }

    async def test_generate_question_valid(
        self, api_client_authenticated, mock_openai_response
    ):
        """Test successful AI question generation"""
        with patch("openai.Completion.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response

            url = reverse("trivia-generate-ai")
            response = await api_client_authenticated.post(
                url,
                {"theme": "Python", "difficulty": 1, "username": "testuser"},
                format="json",
            )

            assert response.status_code == status.HTTP_201_CREATED
            assert "questions" in response.data
            assert len(response.data["questions"]) > 0

    async def test_generate_question_invalid_theme(self, api_client_authenticated):
        """Test AI generation with invalid theme"""
        url = reverse("trivia-generate-ai")
        response = await api_client_authenticated.post(
            url, {"theme": "", "difficulty": 1, "username": "testuser"}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    async def test_generate_question_invalid_difficulty(self, api_client_authenticated):
        """Test AI generation with invalid difficulty"""
        url = reverse("trivia-generate-ai")
        response = await api_client_authenticated.post(
            url,
            {"theme": "Python", "difficulty": 5, "username": "testuser"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    @pytest.mark.django_db
    async def test_generate_and_save_trivia(
        self, api_client_authenticated, mock_openai_response, test_user
    ):
        """Test generating and saving AI trivia"""
        with patch("openai.Completion.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_openai_response

            url = reverse("trivia-generate-ai")
            response = await api_client_authenticated.post(
                url,
                {"theme": "Python", "difficulty": 1, "username": test_user.username},
                format="json",
            )

            assert response.status_code == status.HTTP_201_CREATED
            assert response.data["created_by"] == test_user.username
