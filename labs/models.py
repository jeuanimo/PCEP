"""Labs app — coding challenges evaluated by stdout comparison."""
from django.db import models
from django.conf import settings


class CodingChallenge(models.Model):
    """A hands-on coding exercise tied to a topic and (denormalized) domain.

    The ``domain`` field mirrors ``topic.domain`` for fast domain-level
    filtering without joins.  Set automatically by ``save()``.
    """

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    topic = models.ForeignKey(
        "learning.Topic", on_delete=models.CASCADE, related_name="coding_challenges"
    )
    domain = models.ForeignKey(
        "learning.Domain",
        on_delete=models.CASCADE,
        related_name="coding_challenges",
        null=True,
        blank=True,
        help_text="Auto-populated from topic.domain — do not set manually",
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(help_text="Problem statement shown to the user")
    starter_code = models.TextField(
        blank=True, help_text="Pre-filled skeleton shown in the editor"
    )
    expected_output = models.TextField(
        help_text="Exact stdout the solution must produce for test_input"
    )
    test_input = models.TextField(
        blank=True,
        help_text="Simulated stdin values fed to input(), one value per line",
    )
    hint_1 = models.TextField(blank=True)
    hint_2 = models.TextField(blank=True)
    hint_3 = models.TextField(blank=True)
    solution_code = models.TextField(
        blank=True, help_text="Reference solution — never exposed to the user"
    )
    solution_explanation = models.TextField(
        blank=True,
        help_text="Walkthrough shown after the user solves it (or after max failed attempts)",
    )
    max_attempts_before_reveal = models.PositiveSmallIntegerField(
        default=5,
        help_text="Show solution explanation after this many failed tries (0 = never auto-reveal)",
    )
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="easy"
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__domain__order", "order"]

    def __str__(self) -> str:
        return f"[{self.difficulty}] {self.title}"

    def save(self, *args, **kwargs):
        if self.topic_id and not self.domain_id:
            self.domain_id = self.topic.domain_id
        super().save(*args, **kwargs)


class CodingAttempt(models.Model):
    """One submission of code by a user for a CodingChallenge."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coding_attempts",
    )
    challenge = models.ForeignKey(
        CodingChallenge, on_delete=models.CASCADE, related_name="attempts"
    )
    submitted_code = models.TextField()
    actual_output = models.TextField(blank=True, help_text="Captured stdout from sandbox")
    error_message = models.TextField(
        blank=True,
        help_text="Error traceback if code raised an exception",
    )
    is_correct = models.BooleanField(default=False)
    hints_used = models.PositiveSmallIntegerField(default=0)
    time_taken_seconds = models.PositiveIntegerField(
        null=True, blank=True, help_text="Seconds from page load to submission"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self) -> str:
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.user.username} → {self.challenge.title}"
