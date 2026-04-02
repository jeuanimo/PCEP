"""Admin for the accounts app — user profiles and exam planning."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from core.admin_utils import coloured_score, score_colour
from .models import UserProfile

User = get_user_model()


# ── UserProfile inline on the User page ────────────────────────────────────

class UserProfileInline(admin.StackedInline):
    """Embed the profile directly on the built-in User change page.

    This means an admin only needs to visit one URL to see both the login
    credentials AND the study metadata for any user.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = "PCEP Study Profile"
    fk_name = "user"
    fields = (
        "bio", "avatar", "target_exam_date",
        "study_streak", "longest_streak", "last_study_date",
        "exam_readiness_score", "last_studied_topic",
    )
    readonly_fields = (
        "study_streak", "longest_streak", "last_study_date", "exam_readiness_score",
    )


class CustomUserAdmin(BaseUserAdmin):
    """Extend the default User admin to include the profile inline."""
    inlines = (UserProfileInline,)
    list_display = (
        "username", "email", "first_name", "last_name",
        "is_staff", "date_joined", "readiness_score",
    )

    @admin.display(description="Readiness")
    def readiness_score(self, obj):
        try:
            return coloured_score(obj.profile.exam_readiness_score)
        except UserProfile.DoesNotExist:
            return "—"


# Re-register User with the extended admin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ── Standalone UserProfile admin ────────────────────────────────────────────

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Standalone profile list — useful for filtering by readiness or streak."""

    list_display = (
        "user", "readiness_badge", "study_streak", "longest_streak",
        "last_study_date", "target_exam_date", "days_until_label",
    )
    list_filter = ("last_study_date", "target_exam_date")
    search_fields = ("user__username", "user__email")
    readonly_fields = (
        "study_streak", "longest_streak", "last_study_date",
        "exam_readiness_score", "created_at", "updated_at",
    )
    autocomplete_fields = ("last_studied_topic",)

    fieldsets = (
        (None, {"fields": ("user", "bio", "avatar")}),
        ("Exam planning", {
            "fields": ("target_exam_date", "exam_readiness_score"),
        }),
        ("Streak (read-only — maintained by the app)", {
            "fields": ("study_streak", "longest_streak", "last_study_date"),
        }),
        ("Last activity", {
            "fields": ("last_studied_topic",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Readiness")
    def readiness_badge(self, obj):
        return coloured_score(obj.exam_readiness_score)

    @admin.display(description="Days to exam")
    def days_until_label(self, obj):
        from django.utils.html import format_html
        days = obj.days_until_exam
        if days is None:
            return "—"
        if days == 0:
            return format_html('<span style="color:#dc3545;font-weight:600">Today!</span>')
        if days <= 7:
            return format_html('<span style="color:#dc3545">{} days</span>', days)
        if days <= 30:
            return format_html('<span style="color:#ffc107">{} days</span>', days)
        return f"{days} days"
