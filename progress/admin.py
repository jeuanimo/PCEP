"""Admin for the progress app — topic mastery records and study sessions."""

from django.contrib import admin
from django.utils.html import format_html

from core.admin_utils import score_colour
from .models import StudySession, TopicProgress


# ── TopicProgress ──────────────────────────────────────────────────────────

@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    """Per-user mastery snapshot — read-only; the app engine writes these.

    Useful for support (why does a student see topic X as 'Mastered'?) and
    for spotting trends (e.g. everyone is stuck on the same topic).
    """

    list_display = (
        "user", "topic", "domain_label", "confidence_bar",
        "status", "correct_count", "incorrect_count", "last_practiced",
    )
    list_filter = ("status", "topic__domain", "topic__difficulty")
    search_fields = ("user__username", "user__email", "topic__name", "topic__pcep_objective")
    readonly_fields = (
        "user", "topic", "status", "confidence",
        "correct_count", "incorrect_count", "last_practiced",
        "created_at", "updated_at",
    )
    ordering = ("topic__domain__order", "topic__order")
    date_hierarchy = "last_practiced"

    fieldsets = (
        (None, {"fields": ("user", "topic")}),
        ("Mastery", {"fields": ("confidence", "status")}),
        ("Answer counts", {"fields": ("correct_count", "incorrect_count")}),
        ("Timestamps", {
            "fields": ("last_practiced", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Domain")
    def domain_label(self, obj):
        return obj.topic.domain.title

    @admin.display(description="Confidence")
    def confidence_bar(self, obj):
        conf   = obj.confidence
        colour = score_colour(conf)
        return format_html(
            '<div style="background:#e9ecef;border-radius:4px;width:120px;height:10px">'
            '<div style="background:{};width:{}%;height:100%;border-radius:4px"></div>'
            '</div>'
            '<small style="color:{}">{}</small>',
            colour, conf, colour, conf,
        )


# ── StudySession ───────────────────────────────────────────────────────────

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    """Audit log for daily study sessions used in streak calculation."""

    list_display = (
        "user", "started_at", "ended_at", "duration_display",
        "questions_answered", "correct_answers",
    )
    list_filter = ("user",)
    search_fields = ("user__username", "user__email")
    filter_horizontal = ("topics_studied",)
    readonly_fields = ("started_at", "ended_at", "questions_answered", "correct_answers")
    date_hierarchy = "started_at"

    fieldsets = (
        (None, {"fields": ("user", "started_at", "ended_at")}),
        ("Activity", {"fields": ("questions_answered", "correct_answers", "topics_studied")}),
        ("Notes", {"fields": ("notes",)}),
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Duration")
    def duration_display(self, obj):
        mins = obj.duration_minutes
        if mins is None:
            return "In progress"
        return f"{mins} min"
