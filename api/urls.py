"""
API URL Configuration Module

This module defines the URL routing for the entire Django application.
It includes routes for:
- Admin interface
- API endpoints using DRF ViewSets
- Authentication endpoints
- Static file serving (development only)

The URLs are configured using Django's URL patterns and DRF's routers.
All API endpoints are prefixed with '/api/'.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, re_path
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.routers import DefaultRouter

from .apps.score.viewsets import LeaderBoardViewSet, ScoreViewSet, TriviaWinnerViewSet
from .apps.trivia.views import GetQuestions
from .apps.trivia.viewsets import ThemeViewSet, TriviaViewSet
from .apps.users.views import (
    CreateUserView,
    LoginView,
    LogoutView,
    RegisterView,
    SetupCredentialsView,
)
from .apps.users.viewsets import UserViewSet


# Configure router to make trailing slashes optional
class OptionalSlashRouter(DefaultRouter):
    """
    Custom router that makes trailing slashes optional in URLs.

    This allows both '/api/trivias' and '/api/trivias/' to work.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = "/?"


# Initialize router and register viewsets
router = OptionalSlashRouter()

# Game-related endpoints
router.register(r"trivias", TriviaViewSet, basename="trivia")  # Trivia management
router.register(r"themes", ThemeViewSet, basename="theme")  # Theme management
router.register(r"score", ScoreViewSet, basename="score")  # Score tracking
router.register(r"winners", TriviaWinnerViewSet, basename="winner")  # Winner management

# User-related endpoints
router.register(r"users", UserViewSet, basename="user")  # User management
router.register(
    r"leaderboards", LeaderBoardViewSet, basename="leaderboard"
)  # Leaderboards


# Agregar esta clase
class CSRFView(View):
    @ensure_csrf_cookie
    def get(self, request):
        return HttpResponse()


# URL patterns configuration
urlpatterns = [
    # Admin interface
    re_path(r"^admin/?", admin.site.urls),
    # Health check endpoint
    re_path(r"^api/", include("api.apps.monitoring.urls")),
    # API router URLs
    re_path(r"^api/", include(router.urls)),
    # Authentication endpoints
    re_path(r"^api/register/?", RegisterView.as_view(), name="register"),
    re_path(r"^api/login/?", LoginView.as_view(), name="login"),
    re_path(r"^api/logout/?", LogoutView.as_view(), name="logout"),
    re_path(r"^api/create-user/?", CreateUserView.as_view(), name="create-user"),
    re_path(
        r"^api/update-credentials/?",
        SetupCredentialsView.as_view(),
        name="update-credentials",
    ),
    # Agregar esta línea
    re_path(r"^api/csrf/?$", CSRFView.as_view(), name="csrf"),
    # Agregar la ruta para questions
    re_path(
        r"^api/questions/(?P<trivia_id>[^/.]+)/?$",
        GetQuestions.as_view(),
        name="get-questions",
    ),
]

# Static/Media files serving in development
if settings.DEBUG:
    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
