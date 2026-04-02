"""Quizzes app — questions, choices, attempts, and per-answer records."""
from django.db import models
from django.conf import settings


class Question(models.Model):
    """A quiz question tied to a topic and (denormalized) its domain.

    The ``domain`` field mirrors ``topic.domain`` so that domain-level
    queries (e.g. weighted exam mode) hit a single table instead of a JOIN.
    It is populated automatically via the ``pre_save`` signal in signals.py.
    """

    QUESTION_TYPES = [
        ("mc", "Multiple Choice"),
        ("ms", "Multi-Select"),
        ("tf", "True / False"),
        ("fib", "Fill in the Blank"),
        ("code_output", "Code Output Prediction"),
        ("short", "Short Answer / Explanation"),
    ]
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    topic = models.ForeignKey(
        "learning.Topic", on_delete=models.CASCADE, related_name="questions"
    )
    # Denormalized for fast domain-level filtering without joins
    domain = models.ForeignKey(
        "learning.Domain",
        on_delete=models.CASCADE,
        related_name="questions",
        null=True,
        blank=True,
        help_text="Auto-populated from topic.domain — do not set manually",
    )
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPES, default="mc")
    text = models.TextField(help_text="The question prompt shown to the user")
    code_snippet = models.TextField(
        blank=True, help_text="Optional Python code block displayed with the question"
    )
    explanation = models.TextField(
        blank=True, help_text="Shown to the user after they answer"
    )
    hint = models.TextField(blank=True, help_text="Optional nudge (costs a hint token)")
    difficulty = models.CharField(
        max_length=10, choices=DIFFICULTY_CHOICES, default="medium"
    )
    pcep_objective = models.CharField(
        max_length=20, blank=True,
        help_text="Objective code inherited from the topic, e.g. 2.2.1",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["topic__domain__order", "topic__order", "difficulty"]
        verbose_name_plural = "questions"

    def __str__(self) -> str:
        return f"[{self.get_question_type_display()}] {self.text[:80]}"

    @property
    def correct_choices(self):
        """Queryset of the correct AnswerChoice(s) for this question."""
        return self.choices.filter(is_correct=True)

    def save(self, *args, **kwargs):
        # Keep domain in sync with topic automatically
        if self.topic_id and not self.domain_id:
            self.domain_id = self.topic.domain_id
        super().save(*args, **kwargs)


class AnswerChoice(models.Model):
    """One possible answer option for a Question."""

    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    explanation = models.TextField(
        blank=True,
        help_text="Per-choice explanation shown after answering (why right or wrong)",
    )
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        marker = "✓" if self.is_correct else "✗"
        return f"{marker} {self.text[:60]}"


class QuizAttempt(models.Model):
    """A single quiz session — topic drill, domain quiz, or full exam."""

    MODE_CHOICES = [
        ("topic",  "Topic Quiz"),
        ("domain", "Domain Quiz"),
        ("mixed",  "Mixed Mode"),
        ("exam",   "Full Exam Mode"),
        ("review", "Mistake Review"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="topic")
    # Optional scope — set for topic/domain modes, null for exam mode
    topic = models.ForeignKey(
        "learning.Topic",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="quiz_attempts",
    )
    domain = models.ForeignKey(
        "learning.Domain",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="quiz_attempts",
    )
    score = models.FloatField(default=0.0, help_text="Percentage correct, 0–100")
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    is_passed = models.BooleanField(
        default=False,
        help_text="True when score >= 70% (PCEP passing threshold)",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    time_limit_seconds = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Wall-clock limit; null means no limit",
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        scope = self.topic or self.domain or "all"
        return f"{self.user.username} | {self.get_mode_display()} ({scope}) — {self.score:.0f}%"

    @property
    def incorrect_count(self) -> int:
        return self.total_questions - self.correct_count

    @property
    def duration_seconds(self):
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    def finalise(self, correct: int, total: int) -> None:
        """Compute score, set is_passed, stamp finished_at, and save.

        Call this once from SubmitQuizView instead of setting fields manually.
        """
        from django.utils import timezone

        self.correct_count  = correct
        self.total_questions = total
        self.score   = round(correct / total * 100, 1) if total else 0.0
        self.is_passed = self.score >= 70
        self.finished_at = timezone.now()
        self.save(update_fields=[
            "correct_count", "total_questions", "score", "is_passed", "finished_at"
        ])


class UserAnswer(models.Model):
    """The answer a user gave to one question within a QuizAttempt."""

    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="user_answers"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    # For mc / ms / tf — stores the chosen AnswerChoice(s)
    selected_choices = models.ManyToManyField(AnswerChoice, blank=True)
    # For fib / short — stores free-text response
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(default=False)
    time_taken_seconds = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Seconds spent on this question"
    )
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["answered_at"]
        # One answer per question per attempt
        unique_together = ("attempt", "question")

    def __str__(self) -> str:
        mark = "✓" if self.is_correct else "✗"
        return f"{mark} {self.user.username} → Q{self.question_id}"
