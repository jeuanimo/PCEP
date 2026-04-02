import json
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView
from django_ratelimit.decorators import ratelimit

from .models import Domain, Topic, Lesson, Flashcard, FlashcardRating
from progress.models import TopicProgress


class DomainListView(ListView):
    """All four PCEP domains — the learning hub."""
    model = Domain
    template_name = "learning/domain_list.html"
    context_object_name = "domains"


class DomainDetailView(DetailView):
    """Single domain showing its topics and user mastery."""
    model = Domain
    template_name = "learning/domain_detail.html"
    context_object_name = "domain"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        topics = self.object.topics.all()
        topic_data = []
        for t in topics:
            tp = None
            if self.request.user.is_authenticated:
                tp = TopicProgress.objects.filter(
                    user=self.request.user, topic=t
                ).first()
            topic_data.append({"topic": t, "progress": tp})
        ctx["topic_data"] = topic_data
        return ctx


class TopicDetailView(DetailView):
    """Topic overview with links to lessons, flashcards, quizzes, labs."""
    model = Topic
    template_name = "learning/topic_detail.html"
    context_object_name = "topic"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["lessons"] = self.object.lessons.all()
        ctx["flashcard_count"] = self.object.flashcards.count()
        ctx["quiz_count"] = self.object.questions.count()
        ctx["lab_count"] = self.object.coding_challenges.count()
        if self.request.user.is_authenticated:
            ctx["progress"] = TopicProgress.objects.filter(
                user=self.request.user, topic=self.object
            ).first()
        return ctx


class LessonDetailView(LoginRequiredMixin, DetailView):
    """Read a lesson and mark the topic as studied."""
    model = Lesson
    template_name = "learning/lesson_detail.html"
    context_object_name = "lesson"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        topic = self.object.topic
        from progress.services import record_lesson_read
        record_lesson_read(request.user, topic)
        profile = getattr(request.user, "profile", None)
        if profile:
            profile.last_studied_topic = topic
            profile.save(update_fields=["last_studied_topic"])
            profile.update_streak()
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lessons = list(
            self.object.topic.lessons.filter(is_active=True).order_by("order")
        )
        idx = next((i for i, l in enumerate(lessons) if l.pk == self.object.pk), None)
        ctx["prev_lesson"] = lessons[idx - 1] if idx and idx > 0 else None
        ctx["next_lesson"] = lessons[idx + 1] if idx is not None and idx < len(lessons) - 1 else None
        ctx["lesson_number"] = (idx or 0) + 1
        ctx["lesson_total"] = len(lessons)
        return ctx


# ── Flashcard browse ───────────────────────────────────────────────────────

class FlashcardBrowseView(LoginRequiredMixin, TemplateView):
    """Browse all domains/topics that have flashcards, with per-topic rating summary."""
    template_name = "learning/flashcard_browse.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Build rating summary: {flashcard_id: rating}  and  {topic_id: counts}
        user_ratings = {
            r.flashcard_id: r.rating
            for r in FlashcardRating.objects.filter(user=self.request.user)
               .only("flashcard_id", "rating")
        }

        # Map flashcard_id → topic_id for counting
        fc_topic_map = {
            fc["id"]: fc["topic_id"]
            for fc in Flashcard.objects.filter(is_active=True).values("id", "topic_id")
        }
        topic_counts: dict = defaultdict(lambda: {"easy": 0, "medium": 0, "hard": 0, "rated": 0})
        for fc_id, rating in user_ratings.items():
            tid = fc_topic_map.get(fc_id)
            if tid:
                topic_counts[tid][rating] += 1
                topic_counts[tid]["rated"] += 1

        domains = []
        total_cards = 0
        total_rated = 0
        for domain in Domain.objects.filter(is_active=True).order_by("order"):
            topic_rows = []
            for topic in domain.topics.filter(is_active=True).order_by("order"):
                card_count = topic.flashcards.filter(is_active=True).count()
                if card_count == 0:
                    continue
                tc = topic_counts[topic.pk]
                topic_rows.append({
                    "topic":        topic,
                    "card_count":   card_count,
                    "rated_count":  tc["rated"],
                    "easy_count":   tc["easy"],
                    "medium_count": tc["medium"],
                    "hard_count":   tc["hard"],
                    "unrated_count": card_count - tc["rated"],
                    "pct_done": round(tc["rated"] / card_count * 100) if card_count else 0,
                })
                total_cards += card_count
                total_rated += tc["rated"]
            if topic_rows:
                domains.append({"domain": domain, "topics": topic_rows})

        ctx["domains"]      = domains
        ctx["total_cards"]  = total_cards
        ctx["total_rated"]  = total_rated
        return ctx


# ── Flashcard study deck ───────────────────────────────────────────────────

class FlashcardView(LoginRequiredMixin, TemplateView):
    """Flashcard study mode for a topic — includes saved ratings and AJAX rate URL."""
    template_name = "learning/flashcards.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        topic = get_object_or_404(Topic, pk=kwargs["topic_pk"])

        # Existing ratings for this user × topic
        user_ratings = {
            r.flashcard_id: r.rating
            for r in FlashcardRating.objects.filter(
                user=self.request.user, flashcard__topic=topic
            ).only("flashcard_id", "rating")
        }

        cards = list(
            topic.flashcards.filter(is_active=True)
            .order_by("order")
            .values("id", "front", "back", "hint")
        )
        for card in cards:
            card["rating"] = user_ratings.get(card["id"], "")

        # Rating summary for header badges
        easy   = sum(1 for r in user_ratings.values() if r == "easy")
        medium = sum(1 for r in user_ratings.values() if r == "medium")
        hard   = sum(1 for r in user_ratings.values() if r == "hard")

        ctx.update({
            "topic":         topic,
            "flashcards":    cards,
            "flashcards_json": json.dumps(cards),
            "rate_url":      reverse("learning:flashcard_rate"),
            "easy_count":    easy,
            "medium_count":  medium,
            "hard_count":    hard,
            "unrated_count": len(cards) - easy - medium - hard,
        })
        return ctx


# ── Flashcard AJAX rate endpoint ───────────────────────────────────────────

@method_decorator(
    ratelimit(key="user", rate="60/m", method="POST", block=True),
    name="post",
)
class FlashcardRateView(LoginRequiredMixin, View):
    """POST {flashcard_id, rating} → upsert FlashcardRating → JSON response."""

    def post(self, request):
        try:
            data      = json.loads(request.body)
            card_id   = int(data["flashcard_id"])
            rating    = data["rating"]
        except (KeyError, ValueError):
            return JsonResponse({"error": "bad request"}, status=400)

        if rating not in ("easy", "medium", "hard"):
            return JsonResponse({"error": "invalid rating"}, status=400)

        card = get_object_or_404(Flashcard, pk=card_id)
        FlashcardRating.objects.update_or_create(
            user=request.user,
            flashcard=card,
            defaults={"rating": rating},
        )
        return JsonResponse({"status": "ok", "rating": rating, "flashcard_id": card_id})
