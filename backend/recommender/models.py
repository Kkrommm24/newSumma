from django.db import models
from django.conf import settings
from news.models import NewsSummary, NewsArticle, Category
import uuid
import logging
from django.utils import timezone

# Create your models here.

logger = logging.getLogger(__name__)


class SummaryViewLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    summary_id = models.UUIDField()
    duration_seconds = models.PositiveIntegerField()
    viewed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = "Summary View Log"
        verbose_name_plural = "Summary View Logs"
        indexes = [
            models.Index(fields=['user_id', 'summary_id']),
            models.Index(fields=['viewed_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"View log {self.id}: User {self.user_id} viewed summary {self.summary_id} for {self.duration_seconds}s"


class SummaryClickLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    summary_id = models.UUIDField()
    clicked_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'summary_id']),
            models.Index(fields=['clicked_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Click log {self.id}: User {self.user_id} clicked summary {self.summary_id}"


class SummaryRanking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    summary_id = models.UUIDField()
    user_id = models.UUIDField()
    category_score = models.FloatField(default=0.0)
    search_history_score = models.FloatField(default=0.0)
    favorite_keywords_score = models.FloatField(default=0.0)
    total_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('summary_id', 'user_id')
        indexes = [
            models.Index(fields=['user_id', 'total_score']),
            models.Index(fields=['summary_id', 'user_id']),
        ]

    def __str__(self):
        return f"Ranking for {self.summary_id} - User: {self.user_id if self.user_id else 'Global'}"

    def calculate_total_score(self):
        try:
            self.total_score = (
                self.category_score * 0.5 +
                self.search_history_score * 0.3 +
                self.favorite_keywords_score * 0.2
            )
            self.save(update_fields=['total_score', 'updated_at'])
        except Exception as e:
            raise
