"""Learning app — domains, topics, lessons, and flashcards."""
from django.db import models


class Domain(models.Model):
    """One of the four PCEP-30-02 exam domains."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    # Integer percentage (18, 29, 25, 28) matching the official exam blueprint
    weight_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Official exam weight as a whole percentage, e.g. 29",
    )
    order = models.PositiveSmallIntegerField(default=0)
    icon = models.CharField(
        max_length=50, blank=True, help_text="Bootstrap Icons class, e.g. bi-cpu"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name_plural = "domains"

    def __str__(self) -> str:
        return f"{self.order}. {self.title} ({self.weight_percent}%)"

    @property
    def weight(self) -> float:
        """Decimal weight for use in weighted-score calculations (e.g. 0.29)."""
        return self.weight_percent / 100


class Topic(models.Model):
    """A specific sub-topic within a domain, mapped to a PCEP objective code."""

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="topics"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="easy"
    )
    pcep_objective = models.CharField(
        max_length=20,
        blank=True,
        help_text="Official PCEP objective code, e.g. 2.1.1",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["domain__order", "order"]
        unique_together = ("domain", "slug")
        verbose_name_plural = "topics"

    def __str__(self) -> str:
        return f"[{self.pcep_objective}] {self.name}" if self.pcep_objective else self.name

    @property
    def full_path(self) -> str:
        return f"{self.domain.title} → {self.name}"


class Lesson(models.Model):
    """Rich-text lesson content for a topic."""

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    content = models.TextField(help_text="Supports HTML")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("topic", "slug")

    def __str__(self) -> str:
        return f"{self.topic.name} — {self.title}"


class Flashcard(models.Model):
    """Flip-card for active recall practice on a topic."""

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="flashcards"
    )
    front = models.TextField(help_text="Question / prompt shown face-up")
    back = models.TextField(help_text="Answer revealed on flip")
    hint = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.front[:80]


class FlashcardRating(models.Model):
    """Per-user self-assessment rating for a single flashcard.

    Users rate each card Easy / Medium / Hard after seeing the answer.
    This drives the review priority — Hard cards surface more often.
    """

    RATING_CHOICES = [
        ("easy",   "Easy"),
        ("medium", "Medium"),
        ("hard",   "Hard"),
    ]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="flashcard_ratings",
    )
    flashcard = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rating = models.CharField(max_length=10, choices=RATING_CHOICES)
    rated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "flashcard")

    def __str__(self) -> str:
        return f"{self.user} — {self.flashcard.front[:40]} [{self.rating}]"
