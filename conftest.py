"""
Configuration file for pytest that sets up the Django test environment.

This file is automatically recognized by pytest and used to configure
the test environment before running tests.
"""

import os

import django
import pytest
from rest_framework.test import APIClient

from api.apps.score.models import LeaderBoard, Score
from api.apps.score.tests.factories import LeaderBoardFactory, ScoreFactory
from api.apps.trivia.models import Theme, Trivia
from api.apps.trivia.tests.factories import (
    AnswerFactory,
    InvalidTriviaFactory,
    MaxQuestionsTrivia,
    PrivateTriviaFactory,
    QuestionFactory,
    ThemeFactory,
    TriviaFactory,
    UserFactory,
)
from api.apps.users.models import CustomUser


def pytest_configure(config):
    """Configure test environment"""
    os.environ.setdefault("DJANGO_ENVIRONMENT", "development")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()


@pytest.fixture
def test_user(db):
    """Create a test user using UserFactory"""
    return UserFactory()


@pytest.fixture
def test_theme(db):
    """Create a test theme using ThemeFactory"""
    return ThemeFactory()


@pytest.fixture
def test_trivia(db, test_user):
    """Create a test trivia using TriviaFactory"""
    return TriviaFactory(created_by=test_user)


@pytest.fixture
def api_client():
    """Create a test API client"""
    return APIClient()


@pytest.fixture
def api_client_authenticated(api_client, test_user):
    """Create authenticated client with factory user"""
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def trivia_with_questions(db, test_user):
    """Create a trivia with questions using TriviaFactory"""
    return TriviaFactory.create_with_questions(created_by=test_user)


@pytest.fixture
def trivia_with_single_question(db, test_user):
    """Create a trivia with one question"""
    trivia = TriviaFactory(created_by=test_user)
    question = QuestionFactory(trivia=trivia)
    AnswerFactory.create_batch(2, question=question)
    return trivia


@pytest.fixture
def private_trivia(db, test_user):
    """Create a private trivia"""
    return PrivateTriviaFactory(created_by=test_user)


@pytest.fixture
def trivia_with_max_questions(db, test_user):
    """Create a trivia with maximum questions"""
    return MaxQuestionsTrivia(created_by=test_user)


@pytest.fixture
def trivia_with_max_answers(db, test_user):
    """Create a trivia with a question that has maximum answers"""
    trivia = TriviaFactory(created_by=test_user)
    question = QuestionFactory(trivia=trivia)
    AnswerFactory.create_batch(5, question=question)  # Crear 5 respuestas (máximo)
    return trivia


@pytest.fixture
def trivia_with_invalid_difficulty(db, test_user):
    """Create a trivia with invalid difficulty"""
    return InvalidTriviaFactory(created_by=test_user)


@pytest.fixture(autouse=True)
def clean_db():
    """Limpiar la base de datos antes de cada prueba"""
    Trivia.objects.all().delete()
    Theme.objects.all().delete()
    CustomUser.objects.exclude(username="admin").delete()


@pytest.fixture
def test_leaderboard(db, test_user):
    """Create a test leaderboard"""
    return LeaderBoardFactory(created_by=test_user)


@pytest.fixture
def test_score(db, test_leaderboard):
    """Create a test score"""
    return ScoreFactory(leaderboard=test_leaderboard)


@pytest.fixture
def leaderboard_with_scores(db, test_user):
    """Create a leaderboard with multiple scores"""
    leaderboard = LeaderBoardFactory(created_by=test_user)
    ScoreFactory.create_batch(size=15, leaderboard=leaderboard)
    return leaderboard


@pytest.fixture
def valid_score_data(test_leaderboard):
    """Fixture para datos válidos de score"""
    return {
        "name": "TestPlayer",
        "points": 100,
        "discord_channel": test_leaderboard.discord_channel,
    }


@pytest.fixture
def invalid_score_data():
    """Fixture para datos inválidos de score"""
    return {
        "name": "TestPlayer",
        "points": -100,
        "discord_channel": "invalid-channel",
    }


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Limpiar datos después de cada test"""
    yield
    Score.objects.all().delete()
    LeaderBoard.objects.all().delete()


@pytest.fixture
def mock_auth_backend(mocker):
    """Mock del backend de autenticación"""
    return mocker.patch("django.contrib.auth.backends.ModelBackend")


@pytest.fixture
def mock_email_service(mocker):
    """Mock del servicio de email"""
    return mocker.patch("django.core.mail.send_mail")
