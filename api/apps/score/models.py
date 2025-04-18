"""
Score Models Module

This module defines the database models for the scoring system.
It includes models for:
- LeaderBoard: Manages Discord channel leaderboards
- Score: Tracks individual scores
- TriviaWinner: Records trivia game winners

All models include proper string representations and meta configurations.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _


class LeaderBoard(models.Model):
    """
    LeaderBoard model for managing Discord channel scores.

    Attributes:
        id (UUID): Unique identifier for the leaderboard
        discord_channel (str): Discord channel identifier
        created_by (User): Reference to the user who created the leaderboard
        created_at (datetime): Timestamp of creation
    """

    id: models.UUIDField = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    discord_channel: models.CharField = models.CharField(
        _("Discord Channel"), max_length=255, unique=True
    )
    created_by: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaderboards",
        verbose_name=_("Created By"),
    )
    created_at: models.DateTimeField = models.DateTimeField(
        _("Created"), auto_now_add=True
    )

    def __str__(self):
        return f"Leaderboard - {self.discord_channel}"

    class Meta:
        verbose_name = _("LeaderBoard")
        verbose_name_plural = _("LeaderBoards")


class Score(models.Model):
    """
    Score model for tracking individual scores.

    Attributes:
        name (str): Name of the participant
        points (int): Score points
        leaderboard (LeaderBoard): Associated leaderboard
        created_at (datetime): Timestamp of score creation
    """

    name: models.CharField = models.CharField(_("name"), max_length=255)
    points: models.IntegerField = models.IntegerField(_("points"))
    leaderboard: models.ForeignKey = models.ForeignKey(
        LeaderBoard,
        on_delete=models.CASCADE,
        related_name="scores",
        verbose_name=_("LeaderBoard"),
    )
    created_a: models.DateTimeField = models.DateTimeField(
        _("Created"), auto_now_add=True
    )

    class Meta:
        ordering = ["-points"]

    def __str__(self):
        return f"{self.name} - {self.points}"


class TriviaWinner(models.Model):
    """
    TriviaWinner model for recording trivia game winners.

    Attributes:
        name (str): Winner's name
        trivia_name (str): Name of the trivia game
        date_won (datetime): When the trivia was won
        score (str): Score achieved in the trivia
    """

    name: models.CharField = models.CharField(_("Winner Name"), max_length=255)
    trivia_name: models.CharField = models.CharField(_("Trivia Name"), max_length=255)
    date_won: models.DateTimeField = models.DateTimeField(
        _("Date Won"), auto_now_add=True
    )
    score: models.CharField = models.CharField(_("Score"), max_length=100)

    def __str__(self):
        return f"{self.name} - {self.trivia_name} - {self.date_won}"

    class Meta:
        ordering = ["-date_won"]
