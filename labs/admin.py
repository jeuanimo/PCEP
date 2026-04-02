"""Admin for the labs app — coding challenges and student submissions."""

from django.contrib import admin

from core.admin_utils import coloured_score
from .models import CodingAttempt, CodingChallenge


# ── CodingChallenge ────────────────────────────────────────────────────────

@admin.register(CodingChallenge)
class CodingChallengeAdmin(admin.ModelAdmin):
    """Challenge authoring view.

    The solution_code field is placed in a collapsible 'Solution (hidden)'
    section so it doesn't accidentally appear on screen during screen-sharing
    or classroom demos.
    """

    list_display = (
        "title", "topic", "domain", "difficulty", "order",
        "attempt_count", "solve_rate", "is_active",
    )
    list_display_links = ("title",)
    list_editable = ("is_active",)
    list_filter = ("domain", "topic", "difficulty", "is_active")
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("topic",)
    readonly_fields = ("domain", "created_at", "updated_at")
    ordering = ("topic__domain__order", "order")

    fieldsets = (
        (None, {
            "fields": ("topic", "domain", "order", "title", "slug", "difficulty"),
            "description": "'domain' is set automatically from the chosen topic.",
        }),
        ("Problem statement", {
            "fields": ("description", "starter_code"),
        }),
        ("Test harness", {
            "fields": ("expected_output", "test_input"),
            "description": (
                "expected_output must exactly match stdout (including newlines). "
                "test_input is fed line-by-line to input() calls."
            ),
        }),
        ("Hints", {
            "fields": ("hint_1", "hint_2", "hint_3"),
            "description": "Reveal progressively — hint_1 is the gentlest nudge.",
        }),
        ("Solution (hidden from students)", {
            "fields": ("solution_code", "solution_explanation", "max_attempts_before_reveal"),
            "classes": ("collapse",),
            "description": (
                "Reference solution — never exposed to students. "
                "Explanation is revealed after the student solves it or "
                "exceeds max failed attempts."
            ),
        }),
        ("Status", {
            "fields": ("is_active", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Attempts")
    def attempt_count(self, obj):
        return obj.attempts.count()

    @admin.display(description="Solve rate")
    def solve_rate(self, obj):
        total = obj.attempts.count()
        if not total:
            return "—"
        pct = obj.attempts.filter(is_correct=True).count() / total * 100
        return coloured_score(pct)


# ── CodingAttempt ──────────────────────────────────────────────────────────

@admin.register(CodingAttempt)
class CodingAttemptAdmin(admin.ModelAdmin):
    """Submission audit log.

    Instructors can see which students attempted each challenge and whether
    they succeeded.  The submitted code is visible for review.  No adding or
    editing — submissions come from the app.
    """

    list_display = (
        "user", "challenge", "is_correct", "hints_used",
        "time_taken_seconds", "submitted_at",
    )
    list_filter = ("is_correct", "challenge__domain", "challenge__topic", "challenge__difficulty")
    search_fields = ("user__username", "challenge__title")
    readonly_fields = (
        "user", "challenge", "submitted_code", "actual_output",
        "error_message", "is_correct", "hints_used", "time_taken_seconds",
        "submitted_at",
    )
    date_hierarchy = "submitted_at"

    fieldsets = (
        (None, {"fields": ("user", "challenge")}),
        ("Submission", {"fields": ("submitted_code", "actual_output", "error_message")}),
        ("Outcome", {"fields": ("is_correct", "hints_used", "time_taken_seconds", "submitted_at")}),
    )

    def has_add_permission(self, request):
        return False
