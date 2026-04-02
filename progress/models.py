"""Progress app — topic mastery, study sessions, and readiness tracking."""
from django.db import models
from django.conf import settings


class TopicProgress(models.Model):
    """Per-user, per-topic mastery record updated after every quiz answer.

    ``confidence`` (0–100) drives the status label and the smart
    recommendation engine.  Use ``record_answer()`` to update it — never
    write ``confidence`` directly.
    """

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("learning", "Learning"),
        ("practicing", "Practicing"),
        ("mastered", "Mastered"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_progress",
    )
    topic = models.ForeignKey(
        "learning.Topic",
        on_delete=models.CASCADE,
        related_name="user_progress",
    )
    status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default="not_started"
    )
    confidence = models.PositiveSmallIntegerField(
        default=0, help_text="Mastery score 0–100"
    )
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    last_practiced = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "topic")
        ordering = ["topic__domain__order", "topic__order"]
        verbose_name_plural = "topic progress records"

    def __str__(self) -> str:
        return (
            f"{self.user.username} | {self.topic.name}: "
            f"{self.confidence}% ({self.get_status_display()})"
        )

    # ── computed ──────────────────────────────────────────────────────

    @property
    def total_attempts(self) -> int:
        return self.correct_count + self.incorrect_count

    @property
    def accuracy(self) -> float | None:
        """Percentage of correct answers; None if no attempts yet."""
        if not self.total_attempts:
            return None
        return round(self.correct_count / self.total_attempts * 100, 1)

    # ── mutation ──────────────────────────────────────────────────────

    def record_answer(self, is_correct: bool) -> None:
        """Update confidence and status after a quiz or lab answer.

        Algorithm:
        - Correct: confidence rises with diminishing returns near 100.
          bump = max(2, (100 - confidence) // 5)
        - Incorrect: confidence drops harder when high.
          drop = max(3, confidence // 8)
        """
        from django.utils import timezone

        if is_correct:
            self.correct_count += 1
            bump = max(2, (100 - self.confidence) // 5)
            self.confidence = min(100, self.confidence + bump)
        else:
            self.incorrect_count += 1
            drop = max(3, self.confidence // 8)
            self.confidence = max(0, self.confidence - drop)

        # Status thresholds
        if self.confidence >= 80:
            self.status = "mastered"
        elif self.confidence >= 40:
            self.status = "practicing"
        elif self.total_attempts > 0:
            self.status = "learning"

        self.last_practiced = timezone.now()
        self.save()


class StudySession(models.Model):
    """A timed study session for analytics and streak calculation."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_sessions",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    topics_studied = models.ManyToManyField(
        "learning.Topic",
        blank=True,
        related_name="study_sessions",
    )
    questions_answered = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.user.username} — {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_minutes(self) -> float | None:
        if self.ended_at:
            return round((self.ended_at - self.started_at).total_seconds() / 60, 1)
        return None

    def end(self) -> None:
        """Stamp the end time and save."""
        from django.utils import timezone
        self.ended_at = timezone.now()
        self.save(update_fields=["ended_at"])
