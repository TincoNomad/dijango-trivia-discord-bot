"""
Django Base Settings Module

This module contains the core Django settings used across all environments.
It includes configurations for:
- Database connections
- Installed applications
- Middleware
- Authentication
- Static files
- REST Framework
- JWT Authentication
- Security settings

The settings can be overridden by environment-specific files (dev.py, prod.py).

Note:
    Secret values and environment-specific settings are loaded from env.py

Celery Configuration:
--------------------
Celery is configured but inactive. To activate:

1. Start Redis server:
   $ brew services start redis

2. Start Celery worker:
   $ celery -A api worker -l info

3. For periodic tasks, start Celery beat:
   $ celery -A api beat -l info

Note:
    - Current broker URL: redis://localhost:6379/0
    - Tasks location: api/tasks/
    - Ensure Redis is installed and running before activation
"""

import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import List
from env import env

# Project setup
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Base directory configuration
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG", default=False)
ENVIRONMENT = env("ENVIRONMENT", default="production")
ALLOWED_HOSTS: List[str] = []

# Allowed hosts configuration based on environment
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="").split(",")
if DEBUG:
    ALLOWED_HOSTS.extend(["localhost", "127.0.0.1", "web"])

# HTTPS Security Configuration
# These settings will be automatically adjusted based on the environment
# In development (DEBUG=True): These will be overridden to be more permissive
# In production (DEBUG=False): These strict security settings will be used
SECURE_SSL_REDIRECT = not DEBUG  # c Only force HTTPS in production
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https" if not DEBUG else "http",
)
SESSION_COOKIE_SECUREl = not DEBUG  # Only require HTTPS cookies in production
CSRF_COOKIE_SECURE = not DEBUG  # Only require HTTPS CSRF in production
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0  # HSTS only in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG  # Include subdomains only in production
SECURE_HSTS_PRELOAD = not DEBUG  # Preload only in production

# Base URL Configuration
# This will be overridden in environment-specific settings
BASE_URL = env(
    "API_BASE_URL",
    default="https://your-production-domain.com" if not DEBUG else "http://web:8000",
)

# Application configuration
INSTALLED_APPS = [
    # Custom applications for project functionality
    "api.apps.users.apps.UsersConfig",  # User management
    "api.apps.trivia.apps.TriviaConfig",  # Trivia game logic
    "api.apps.score.apps.ScoreConfig",  # Score tracking
    "api.apps.monitoring.apps.MonitoringConfig",  # System monitoring
    # Django built-in applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party applications
    "rest_framework",  # REST API framework
    "whitenoise.runserver_nostatic",  # Static file serving
    "rest_framework_simplejwt",  # JWT authentication
]

# Middleware configuration for request/response processing
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Monitoring middleware
    "api.apps.monitoring.middleware.MonitoringMiddleware",
    # WhiteNoise for static file serving
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "OPTIONS": {
            "sslmode": "require",  # Required for Neon.tech
        } if not DEBUG else {}
    }
}

# Redis Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://redis:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PARSER_CLASS": "redis.connection.DefaultParser",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 100,
        },
    }
}

# Cache time to live is 15 minutes by default
CACHE_TTL = env("CACHE_TTL", default=60 * 15)

# Cache key prefix to avoid collisions
CACHE_KEY_PREFIX = env("CACHE_KEY_PREFIX", default="trivia_api")

# JWT Authentication settings
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("SIGNING_KEY"),
    "VERIFYING_KEY": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "api.apps.users.models.CustomUser",
}

# Root URL configuration
ROOT_URLCONF = "api.urls"

# Template configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI application path
WSGI_APPLICATION = "api.wsgi.application"

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization settings
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Available languages
LANGUAGES = [
    ("en", "English"),
    ("es", "Spanish"),
]

# Translation files location
LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]

# Static files configuration
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR.parent, "staticfiles")

# WhiteNoise Configuration
WHITENOISE_USE_FINDERS = True
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Additional directory for static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

APPEND_SLASH = False

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/hour",
        "user": "120/hour",
    },
}

AUTH_USER_MODEL = "users.CustomUser"

# Monitoring settings
MONITORING = {
    "REQUEST_LOG_RETENTION_DAYS": 30,
    "ERROR_LOG_RETENTION_DAYS": 90,
}

if DEBUG:
    MONITORING["REQUEST_LOG_RETENTION_DAYS"] = 7
    MONITORING["ERROR_LOG_RETENTION_DAYS"] = 30

# CSRF Configuration
CSRF_COOKIE_NAME = "csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"
CSRF_COOKIE_SECURE = False  # Should be True in production
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SAMESITE = "Lax"

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://your-discord-bot-domain.com",
]
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PATCH",
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Add security headers middleware
MIDDLEWARE.append("django.middleware.security.SecurityMiddleware")

# CSP (Content Security Policy)
CSP_DEFAULT_SRC = ("'none'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_CONNECT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'",)

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"

# Migrations Configuration
MIGRATIONS_CONFIG = {
    "logging": {
        "enabled": env("MIGRATIONS_LOGGING_ENABLED", default=True),
        "level": env("MIGRATIONS_LOGGING_LEVEL", default="INFO"),
    },
    "validation": {
        "check_db_connection": env("MIGRATIONS_VALIDATION_CHECK_DB", default=True),
        "check_dependencies": env("MIGRATIONS_VALIDATION_CHECK_DEPS", default=True),
    },
    "performance": {
        "batch_size": env("MIGRATIONS_PERFORMANCE_BATCH_SIZE", default=1000),
        "use_transactions": env(
            "MIGRATIONS_PERFORMANCE_USE_TRANSACTIONS", default=True
        ),
    },
}

# Celery Configuration (Inactive but ready)
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Email backend configuration based on environment
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"
    if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend"
)
