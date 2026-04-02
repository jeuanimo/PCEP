"""Admin for the learning app — domains, topics, lessons, and flashcards."""

from django.contrib import admin

from .models import Domain, Flashcard, Lesson, Topic


# ── Inlines ────────────────────────────────────────────────────────────────

class LessonInline(admin.StackedInline):
    """One stacked block per lesson — suits the multi-field layout including
    a large content textarea.  StackedInline is easier to read than rows."""
    model = Lesson
    extra = 0
    fields = ("order", "title", "slug", "content", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    show_change_link = True


class FlashcardInline(admin.TabularInline):
    """Compact row-per-card table — front/back/hint are short enough to fit."""
    model = Flashcard
    extra = 0
    fields = ("order", "front", "back", "hint", "is_active")


# ── Domain ─────────────────────────────────────────────────────────────────

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Sorted by order so the list matches the PCEP-30-02 blueprint sequence."""

    list_display = ("order", "title", "weight_badge", "topic_count", "is_active")
    list_display_links = ("title",)
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("order",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("order", "title", "slug", "icon"),
        }),
        ("Exam blueprint", {
            "fields": ("weight_percent", "description"),
            "description": (
                "Official PCEP-30-02 weights: Domain 1 = 18 %, "
                "Domain 2 = 29 %, Domain 3 = 25 %, Domain 4 = 28 %."
            ),
        }),
        ("Metadata", {
            "fields": ("is_active", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Weight")
    def weight_badge(self, obj):
        return f"{obj.weight_percent} %"

    @admin.display(description="Topics")
    def topic_count(self, obj):
        return obj.topics.count()


# ── Topic ──────────────────────────────────────────────────────────────────

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """Inlines show lessons and flashcards so a content author never has to
    leave the topic page to add study material."""

    list_display = (
        "pcep_objective", "name", "domain_link", "difficulty",
        "lesson_count", "card_count", "question_count", "is_active",
    )
    list_display_links = ("name",)
    list_editable = ("is_active",)
    list_filter = ("domain", "difficulty", "is_active")
    search_fields = ("name", "slug", "pcep_objective", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("domain__order", "order")
    autocomplete_fields = ("domain",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [LessonInline, FlashcardInline]

    fieldsets = (
        (None, {
            "fields": ("domain", "order", "name", "slug"),
        }),
        ("PCEP details", {
            "fields": ("pcep_objective", "difficulty", "description"),
            "description": (
                "pcep_objective must match the official blueprint code, "
                "e.g. '2.1.1'.  Leave blank if not yet mapped."
            ),
        }),
        ("Metadata", {
            "fields": ("is_active", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Domain")
    def domain_link(self, obj):
        return str(obj.domain)

    @admin.display(description="Lessons")
    def lesson_count(self, obj):
        return obj.lessons.count()

    @admin.display(description="Cards")
    def card_count(self, obj):
        return obj.flashcards.count()

    @admin.display(description="Qs")
    def question_count(self, obj):
        return obj.questions.count()


# ── Lesson ─────────────────────────────────────────────────────────────────

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "order", "is_active", "updated_at")
    list_display_links = ("title",)
    list_editable = ("is_active",)
    list_filter = ("topic__domain", "is_active")
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("topic",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("topic", "order", "title", "slug")}),
        ("Content", {"fields": ("content",)}),
        ("Metadata", {
            "fields": ("is_active", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


# ── Flashcard ──────────────────────────────────────────────────────────────

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ("front_short", "topic", "order", "is_active")
    list_display_links = ("front_short",)
    list_editable = ("is_active",)
    list_filter = ("topic__domain", "topic", "is_active")
    search_fields = ("front", "back", "hint")
    autocomplete_fields = ("topic",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("topic", "order")}),
        ("Card content", {"fields": ("front", "back", "hint")}),
        ("Metadata", {
            "fields": ("is_active", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Front")
    def front_short(self, obj):
        return obj.front[:70] + ("…" if len(obj.front) > 70 else "")
