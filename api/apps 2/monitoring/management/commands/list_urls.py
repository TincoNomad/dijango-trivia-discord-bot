"""
URL Listing Management Command

This command provides a comprehensive listing of all URLs in the Django application,
organized by type (Django admin, API endpoints, and formatted URLs).

Features:
- Categorized URL listing
- Duplicate URL detection
- Colored output for better readability
- View and name information for each URL

Usage:
    python manage.py list_urls
"""

from django.core.management.base import BaseCommand
from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver


class Command(BaseCommand):
    """
    Django management command to display all available URLs in the application.

    This command categorizes and displays URLs into three main groups:
    1. Default Django URLs (admin, etc.)
    2. API URLs (JSON endpoints)
    3. URLs with specific format patterns
    """

    help = "Shows all available URLs in the application, separated by type"

    def handle(self, *args, **options):
        """
        Execute the URL listing command.

        This method displays three sections of URLs:
        1. Default Django administrative URLs
        2. API endpoints (JSON format)
        3. URLs with specific format patterns

        Returns:
            None
        """
        self.stdout.write(self.style.SUCCESS("\nDefault Django URLs:"))
        self.stdout.write(self.style.SUCCESS("------------------------"))
        self._list_urls(get_resolver(), url_type="django")

        self.stdout.write(self.style.SUCCESS("\nAPI URLs (JSON format):"))
        self.stdout.write(self.style.SUCCESS("------------------------"))
        self._list_urls(get_resolver(), url_type="api")

        self.stdout.write(self.style.SUCCESS("\nURLs with specific format:"))
        self.stdout.write(self.style.SUCCESS("---------------------------"))
        self._list_urls(get_resolver(), url_type="format")

    def _list_urls(self, resolver, prefix="", url_type="django"):
        """
        Recursively list URLs of a specific type from the URL resolver.

        Args:
            resolver: The URL resolver to process
            prefix (str): Current URL prefix for nested patterns
            url_type (str): Type of URLs to display ('django', 'api', or 'format')

        Note:
            URLs are colored for better readability:
            - URLs in green
            - View names in yellow
            - Pattern names in blue
        """
        seen_urls = set()

        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                # Recursively process URL resolvers
                self._list_urls(
                    pattern,
                    prefix=prefix + str(pattern.pattern),
                    url_type=url_type,
                )
            elif isinstance(pattern, URLPattern):
                url = prefix + str(pattern.pattern)

                # Skip if URL was already displayed
                if url in seen_urls:
                    continue

                # Classify URL by type
                is_django = url.startswith("admin/") or url.startswith("static/")
                is_format = ".(?P<format>" in url
                is_api = url.startswith("api/") and not is_format

                should_display = (
                    (url_type == "django" and is_django)
                    or (url_type == "api" and is_api)
                    or (url_type == "format" and is_format)
                )

                if should_display:
                    # Format output with colors
                    name = f"[name='{pattern.name}']"
                    view_name = (
                        pattern.callback.__name__
                        if hasattr(pattern.callback, "__name__")
                        else str(pattern.callback)
                    )

                    formatted_url = self.style.HTTP_SUCCESS(f"  {url}")
                    formatted_view = self.style.WARNING(f" -> {view_name}")
                    formatted_name = self.style.HTTP_INFO(name)

                    self.stdout.write(
                        f"{formatted_url}{formatted_view} {formatted_name}"
                    )
                    seen_urls.add(url)
