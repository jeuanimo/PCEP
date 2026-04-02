"""Accounts app — extended user profile with PCEP study metadata."""
from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """One-to-one extension of the built-in User model.

    Created automatically via the ``post_save`` signal in ``signals.py``
    whenever a new User is saved.  Access via ``request.user.profile``.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True,
        help_text="Optional profile picture",
    )

    # ── Streak tracking ───────────────────────────────────────────────
    study_streak = models.PositiveIntegerField(
        default=0, help_text="Current consecutive-day study streak"
    )
    longest_streak = models.PositiveIntegerField(
        default=0, help_text="All-time longest streak"
    )
    last_study_date = models.DateField(
        null=True, blank=True,
        help_text="Date of the most recent study activity",
    )

    # ── Last-activity pointer ─────────────────────────────────────────
    last_studied_topic = models.ForeignKey(
        "learning.Topic",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Most recently studied topic — used for 'Continue' button",
    )

    # ── Exam planning ─────────────────────────────────────────────────
    target_exam_date = models.DateField(
        null=True, blank=True,
        help_text="User's planned exam date — used to surface urgency cues",
    )

    # ── Computed readiness (updated by the progress engine) ───────────
    exam_readiness_score = models.FloatField(
        default=0.0,
        help_text="Weighted confidence score 0–100 across all four domains",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "user profile"

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"

    # ── Streak logic ──────────────────────────────────────────────────

    def update_streak(self) -> None:
        """Increment streak if studying today; reset if a day was missed.

        Call this once per day when the user submits any answer.
        """
        today = timezone.now().date()

        if self.last_study_date == today:
            return  # already counted today — nothing to do

        if self.last_study_date == today - timezone.timedelta(days=1):
            self.study_streak += 1
        else:
            # Gap of 2+ days — streak resets to 1
            self.study_streak = 1

        self.longest_streak = max(self.longest_streak, self.study_streak)
        self.last_study_date = today
        self.save(update_fields=["study_streak", "longest_streak", "last_study_date"])

    # ── Readiness helpers ─────────────────────────────────────────────

    def compute_readiness(self) -> float:
        """Recalculate and persist the weighted exam readiness score.

        Delegates to ``progress.services.readiness_score`` which is the
        single authoritative implementation.  Saves the result and returns it.
        """
        from progress.services import readiness_score

        self.exam_readiness_score = readiness_score(self.user)
        self.save(update_fields=["exam_readiness_score"])
        return self.exam_readiness_score

    @property
    def days_until_exam(self) -> int | None:
        """Days remaining until the target exam date; None if not set."""
        if not self.target_exam_date:
            return None
        delta = self.target_exam_date - timezone.now().date()
        return max(0, delta.days)
