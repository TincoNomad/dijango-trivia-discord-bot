# Generated by Django 5.1.2 on 2024-12-31 22:02

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HealthCheck",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("status", models.CharField(max_length=20)),
                ("details", models.JSONField()),
            ],
            options={
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="ErrorLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("error_type", models.CharField(max_length=100)),
                ("error_message", models.TextField()),
                ("traceback", models.TextField()),
                ("path", models.CharField(max_length=255)),
                ("method", models.CharField(max_length=10)),
                ("user_id", models.CharField(max_length=255, null=True)),
                ("request_data", models.JSONField(blank=True, null=True)),
                ("url", models.URLField(max_length=255)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["timestamp"],
                        name="monitoring__timesta_c4071d_idx",
                    ),
                    models.Index(
                        fields=["error_type"],
                        name="monitoring__error_t_3bdb0c_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="RequestLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("path", models.CharField(max_length=255)),
                ("method", models.CharField(max_length=10)),
                ("response_time", models.FloatField()),
                ("status_code", models.SmallIntegerField()),
                ("user_id", models.CharField(max_length=255, null=True)),
                ("ip_address", models.GenericIPAddressField(null=True)),
                ("request_data", models.JSONField(blank=True, null=True)),
                ("response_data", models.JSONField(blank=True, null=True)),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["timestamp"],
                        name="monitoring__timesta_adb931_idx",
                    ),
                    models.Index(
                        fields=["path"], name="monitoring__path_e6b9f2_idx"
                    ),
                    models.Index(
                        fields=["status_code"],
                        name="monitoring__status__38f175_idx",
                    ),
                ],
            },
        ),
    ]
