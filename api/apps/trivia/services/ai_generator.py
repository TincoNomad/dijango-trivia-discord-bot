import asyncio
import json
import logging
from typing import Dict

import openai
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class TriviaAIGenerator:
    """OpenAI integration service for trivia generation"""

    def __init__(self):
        try:
            self.model = settings.OPENAI_MODEL
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise APIException("Failed to initialize AI service")

    async def generate_question(self, theme: str, difficulty: int) -> Dict:
        """
        Generates a single trivia question

        Args:
            theme (str): Topic for the question
            difficulty (int): Level from 1-3

        Returns:
            Dict: Generated question data

        Raises:
            ValidationError: If parameters are invalid
            APIException: If generation fails
        """
        if not theme or not isinstance(theme, str):
            raise ValidationError("Theme must be a non-empty string")

        if not 1 <= difficulty <= 3:
            raise ValidationError("Difficulty must be between 1 and 3")

        try:
            prompt = self._build_prompt(theme, difficulty)
            return await self._generate_with_ai(prompt)
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            raise APIException("Failed to generate question")

    def _build_prompt(self, theme: str, difficulty: int) -> str:
        json_structure = {
            "question": "The question text",
            "options": ["option1", "option2", "option3", "option4"],
            "correct_answer": "The correct option text",
            "explanation": "Brief explanation of the answer",
        }
        return (
            f"Create a trivia question about {theme} with difficulty level {difficulty}/3.\n"
            f"The response must be a valid JSON with this exact structure: \n"
            f"{json.dumps(json_structure, indent=4)}\n"
            f"Ensure the correct_answer matches exactly one of the options."
        )

    async def _generate_with_ai(self, prompt: str) -> Dict:
        """
        Generate response using OpenAI

        Args:
            prompt (str): Formatted prompt for OpenAI

        Returns:
            Dict: Validated question data

        Raises:
            APIException: If API call fails
        """
        try:
            response = await asyncio.to_thread(
                openai.completions.create,
                model=self.model,
                prompt=prompt,
                temperature=0.7,
                max_tokens=300,
            )
            content = response.choices[0].text.strip()
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise APIException(f"AI generation failed: {str(e)}")

    def _parse_response(self, content: str) -> Dict:
        """
        Parse and validate AI response

        Args:
            content (str): JSON string from OpenAI

        Returns:
            Dict: Validated question data

        Raises:
            ValidationError: If format is invalid
            APIException: If JSON parsing fails
        """
        try:
            data = json.loads(content)
            required = ["question", "options", "correct_answer", "explanation"]

            if not all(key in data for key in required):
                raise ValidationError("Missing required fields in response")

            if len(data["options"]) != 4:
                raise ValidationError("Must provide exactly 4 options")

            if data["correct_answer"] not in data["options"]:
                raise ValidationError("Correct answer must be one of the options")

            return data
        except json.JSONDecodeError:
            raise APIException("Invalid JSON response from AI")
