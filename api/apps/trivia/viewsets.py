"""
Trivia ViewSets Module

This module provides API viewsets for trivia-related operations.
Includes viewsets for:
- Trivia CRUD operations
- Theme management
- Question updates
- Filtering and search

Features:
- Permission handling
- Transaction management
- Logging
- Error handling
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.utils import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from services.ai_generator import TriviaAIGenerator

from api.utils.cache_utils import cache_viewset_action
from api.utils.jwt_utils import get_user_id_by_username
from api.utils.logging_utils import log_exception, logger

from .models import Answer, Question, Theme, Trivia
from .serializers import (
    QuestionSerializer,
    ThemeSerializer,
    TriviaListSerializer,
    TriviaSerializer,
)

User = get_user_model()


class TriviaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing trivias.

    Features:
    - CRUD operations
    - Custom serializer selection
    - Permission-based access
    - Query filtering
    """

    def get_serializer_class(self):
        """Select appropriate serializer based on action"""
        if self.action == "list":
            return TriviaListSerializer
        return TriviaSerializer

    def get_permissions(self):
        """Define permissions based on action"""
        return []

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        Returns:
            QuerySet: Filtered trivia objects
        """
        user = self.request.user
        if user.is_authenticated:
            if user.role == "admin":
                logger.info(f"Admin access: {user.username} querying all trivias")
                return Trivia.objects.all()
            logger.info(f"User access: {user.username} querying allowed trivias")
            return Trivia.objects.filter(
                models.Q(is_public=True) | models.Q(is_public=False, created_by=user)
            )
        logger.info("Anonymous access: querying public trivias")
        return Trivia.objects.filter(is_public=True)

    def perform_create(self, serializer):
        """
        Create new trivia with creator information.

        Args:
            serializer: Validated trivia serializer

        Raises:
            ValidationError: If user not found or creation fails
        """
        username = serializer.validated_data.get("username")
        try:
            user = User.objects.get(username=username)
            trivia = serializer.save(created_by=user, is_public=True)
            logger.info(
                f"Trivia created successfully: ID={trivia.id}, "
                f"Creator={username}, Title={trivia.title}"
            )
        except User.DoesNotExist:
            logger.error(f"Attempt to create trivia with non-existent user: {username}")
            raise ValidationError("User not found")
        except Exception as e:
            logger.error(f"Error creating trivia: User={username}, " f"Error={str(e)}")
            raise

    @cache_viewset_action()
    @action(detail=False, methods=["get"])
    def get_trivia(self, request):
        """
        Get general trivia information without questions.
        Cached to improve performance for frequently accessed trivias.

        Cache Strategy:
        - TTL: 15 minutes
        - Key: Based on trivia_id parameter
        - Invalidated: On trivia update
        """
        trivia_id = request.query_params.get("id")
        if not trivia_id:
            return Response(
                {"error": "ID query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uuid.UUID(trivia_id)
        except ValueError:
            return Response(
                {"error": "Invalid UUID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            trivia = Trivia.objects.get(id=trivia_id)
            serializer = TriviaSerializer(trivia)
            return Response(serializer.data)
        except Trivia.DoesNotExist:
            return Response(
                {"error": "Trivia not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @cache_viewset_action()
    @action(detail=False, methods=["get"])
    def difficulty(self, request):
        """
        Get available difficulty options.
        Cached since difficulty options rarely change.

        Cache Strategy:
        - TTL: 15 minutes
        - Key: Static for all users
        - Invalidated: Only when difficulty choices change
        """
        try:
            difficulties = dict(Trivia.DIFFICULTY_CHOICES)
            return Response(difficulties, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting difficulty choices: {e}")
            return Response(
                {"error": "Error retrieving difficulty choices"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def list(self, request, *args, **kwargs):
        """
        List trivias with optional username filter.

        GET /api/trivias/?username=discord_user

        Returns:
            Response: List of trivias
        """
        username = request.query_params.get("username")

        if username:
            try:
                user_id = get_user_id_by_username(username)
                if not user_id:
                    return Response(
                        {"error": f"No user found with username: {username}"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                trivias = Trivia.objects.filter(created_by_id=user_id)
                serializer = TriviaListSerializer(trivias, many=True)
                return Response(serializer.data)

            except Exception as e:
                logger.error(f"Error getting trivias by user: {str(e)}")
                return Response(
                    {"error": "Internal server error"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="filter")
    def filter_trivias(self, request):
        """
        Filter trivias by theme and difficulty.

        Returns:
            Response: Filtered trivia list
            Response: Error message if parameters invalid
        """
        theme = request.query_params.get("theme")
        difficulty = request.query_params.get("difficulty")

        if not theme or not difficulty:
            logger.warning(
                f"Filtering attempt without required parameters: "
                f"theme={theme}, difficulty={difficulty}"
            )
            return Response(
                {"error": "The parameters 'theme' and 'difficulty' are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            difficulty = int(difficulty)
            uuid.UUID(theme)

            if not Theme.objects.filter(id=theme).exists():
                logger.warning(f"Filtering attempt with non-existent theme: {theme}")
                return Response(
                    {"error": "Theme not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            query = models.Q(theme=theme, difficulty=difficulty, is_public=True)
            filtered_trivias = Trivia.objects.filter(query).values("id", "title")

            logger.info(
                f"Successful filtering: theme={theme}, difficulty={difficulty}, "
                f"results={len(filtered_trivias)}"
            )

            simplified_response = [
                {"id": str(trivia["id"]), "title": trivia["title"]}
                for trivia in filtered_trivias
            ]

            return Response(simplified_response)
        except ValueError:
            logger.error(
                f"Invalid filter parameter format: "
                f"theme={theme}, difficulty={difficulty}"
            )
            return Response(
                {"error": "The 'difficulty' parameter must be a number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @log_exception
    def create(self, request, *args, **kwargs):
        """Create trivia with transaction handling"""
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except IntegrityError:
            raise DRFValidationError(
                detail="A trivia with this title already exists."
                "Please choose another title."
            )
        except ValidationError as e:
            raise DRFValidationError(detail=str(e))

    @action(detail=True, methods=["patch"])
    def update_questions(self, request, pk=None):
        """
        Update questions and answers for a trivia.

        PATCH /api/trivias/{trivia_id}/update_questions/

        Returns:
            Response: Success message if updated
            Response: Error message if update fails
        """
        try:
            trivia = self.get_object()
            questions_data = request.data.get("questions", [])

            for question_data in questions_data:
                question_id = question_data.get("id")
                if question_id:
                    question = Question.objects.get(id=question_id, trivia=trivia)
                    for key, value in question_data.items():
                        if key != "answers":
                            setattr(question, key, value)
                    question.save()

                    if "answers" in question_data:
                        for answer_data in question_data["answers"]:
                            answer_id = answer_data.get("id")
                            if answer_id:
                                answer = Answer.objects.get(
                                    id=answer_id, question=question
                                )
                                for key, value in answer_data.items():
                                    setattr(answer, key, value)
                                answer.save()

            return Response({"status": "questions updated"})
        except Question.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Answer.DoesNotExist:
            return Response(
                {"error": "Answer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error updating questions: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        """Log and handle trivia updates"""
        try:
            username = self.request.query_params.get("username")
            if not username:
                raise ValidationError("Username is required for updates")

            user_id = get_user_id_by_username(username)
            if not user_id:
                raise ValidationError(f"No user found with username: {username}")

            trivia = self.get_object()
            if trivia.created_by_id != user_id:
                raise ValidationError("You can only update your own trivias")

            serializer.save()
            logger.info(f"Trivia updated by user: {username}")
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            raise

    @action(detail=True, methods=["get"])
    def questions(self, request, pk=None):
        """Obtiene las preguntas y respuestas de una trivia específica"""
        trivia = self.get_object()
        questions = trivia.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    async def generate_ai(self, request):
        """
        Generate trivia using AI

        Args:
            theme (str): Topic for the trivia
            difficulty (int): Level 1-3
            username (str): Creator username

        Returns:
            Response: Created trivia data

        Raises:
            ValidationError: If parameters invalid
            APIException: If generation fails
        """
        theme = request.data.get("theme")
        difficulty = request.data.get("difficulty")
        username = request.data.get("username")

        # Validate required fields
        if not all([theme, difficulty, username]):
            return Response(
                {"error": "theme, difficulty and username are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Generate question using AI
            generator = TriviaAIGenerator()
            question = await generator.generate_question(
                theme=theme, difficulty=difficulty
            )

            # Prepare trivia data
            trivia_data = {
                "title": f"AI Generated: {theme}",
                "theme": theme,
                "difficulty": difficulty,
                "username": username,
                "questions": [question],
            }

            # Create and validate trivia
            serializer = TriviaSerializer(data=trivia_data)
            serializer.is_valid(raise_exception=True)

            # Create trivia with transaction
            with transaction.atomic():
                trivia = self.perform_create(serializer)
                logger.info(
                    f"AI-generated trivia created: ID={trivia.id}, "
                    f"Creator={username}, Theme={theme}"
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            logger.error(f"Validation error in AI generation: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in AI trivia generation: {str(e)}")
            return Response(
                {"error": "Failed to generate trivia"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ThemeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for theme management.
    Provides read-only access to themes.
    """

    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    @cache_viewset_action()
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
