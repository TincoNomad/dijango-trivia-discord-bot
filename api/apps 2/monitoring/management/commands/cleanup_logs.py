"""
Log Cleanup Management Command

This command handles the automated cleanup of old request and error logs
based on the retention settings defined in Django settings.

Features:
- Batch processing to avoid memory overload
- Separate retention periods for request and error logs
- Success message with deletion counts

Usage:
    python manage.py cleanup_logs
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.apps.monitoring.models import ErrorLog, RequestLog


class Command(BaseCommand):
    """
    Django management command to clean up old monitoring logs.

    This command removes RequestLog and ErrorLog entries that are older
    than the configured retention periods. It processes deletions in
    batches to prevent memory issues with large datasets.
    """

    help = "Cleanup old logs based on retention settings"

    def handle(self, *args, **options):
        """
        Execute the log cleanup command.

        This method:
        1. Calculates deletion thresholds based on retention settings
        2. Deletes old request logs in batches
        3. Deletes old error logs in batches
        4. Reports the number of deleted entries

        Returns:
            None
        """
        # Get retention settings from configuration
        request_retention = settings.MONITORING["REQUEST_LOG_RETENTION_DAYS"]
        error_retention = settings.MONITORING["ERROR_LOG_RETENTION_DAYS"]

        # Calculate threshold dates for deletion
        request_threshold = timezone.now() - timedelta(days=request_retention)
        error_threshold = timezone.now() - timedelta(days=error_retention)

        # Configure batch size for processing
        batch_size = 1000

        # Process request logs deletion
        deleted_requests = 0
        while RequestLog.objects.filter(timestamp__lt=request_threshold).exists():
            # Get batch of IDs to delete
            ids = RequestLog.objects.filter(
                timestamp__lt=request_threshold
            ).values_list("id", flat=True)[:batch_size]

            # Delete batch and update count
            deleted_count, _ = RequestLog.objects.filter(id__in=list(ids)).delete()
            deleted_requests += deleted_count

        # Process error logs deletion
        deleted_errors = 0
        while ErrorLog.objects.filter(timestamp__lt=error_threshold).exists():
            # Get batch of IDs to delete
            ids = ErrorLog.objects.filter(timestamp__lt=error_threshold).values_list(
                "id", flat=True
            )[:batch_size]

            # Delete batch and update count
            deleted_count, _ = ErrorLog.objects.filter(id__in=list(ids)).delete()
            deleted_errors += deleted_count

        # Report success message
        self.stdout.write(
            self.style.SUCCESS(
                f"""Successfully deleted {deleted_requests}
                request logs and {deleted_errors} error logs"""
            )
        )
