#!/usr/bin/env python
"""
Django's command-line utility for administrative tasks.

This module serves as the main entry point for Django management commands.
It sets up the Django environment and handles command execution.

Usage:
    python manage.py <command> [options]

Common commands:
    runserver - Starts the development server
    migrate - Applies database migrations
    createsuperuser - Creates a superuser account
"""
import os
import sys


def main():
    """
    Main function that runs administrative tasks.

    This function:
    1. Sets the Django settings module
    2. Imports and executes Django management commands
    3. Handles import errors with helpful messages

    Returns:
        None

    Raises:
        ImportError: If Django is not installed or PYTHONPATH is not set correctly
    """
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
