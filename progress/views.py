"""Progress app views — dashboard, per-topic progress, and review mode."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

from accounts.models import UserProfile
from labs.models import CodingAttempt
from learning.models import Domain, Topic
from quizzes.models import QuizAttempt, UserAnswer
from .models import TopicProgress
from . import services


# ── Dashboard ──────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    """The user's study command centre."""

    template_name = "progress/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # ── Core metrics ─────────────────────────────────────────────
        readiness = services.readiness_score(user)
        profile.exam_readiness_score = readiness
        profile.save(update_fields=["exam_readiness_score"])

        ctx["profile"] = profile
        ctx["exam_readiness"] = readiness
        ctx["streak"] = profile.study_streak

        # ── Domain mastery bars ──────────────────────────────────────
        ctx["domain_stats"] = services.domain_stats(user)

        # ── Recommendation ────────────────────────────────────────────
        ctx["recommendation"] = services.get_recommendation(user)

        # ── Recent quizzes (table) ────────────────────────────────────
        ctx["recent_quizzes"] = (
            QuizAttempt.objects.filter(user=user, finished_at__isnull=False)
            .select_related("topic", "domain")
            .order_by("-started_at")[:6]
        )

        # ── Activity feed ─────────────────────────────────────────────
        ctx["recent_activity"] = services.get_recent_activity(user, limit=8)

        # ── Labs ─────────────────────────────────────────────────────
        from labs.models import CodingChallenge
        ctx["total_labs"] = CodingChallenge.objects.filter(is_active=True).count()
        ctx["completed_labs"] = (
            CodingAttempt.objects.filter(user=user, is_correct=True)
            .values("challenge")
            .distinct()
            .count()
        )

        # ── Review queue size ─────────────────────────────────────────
        ctx["missed_count"] = services.missed_question_count(user)

        # ── Most-missed topics heatmap ────────────────────────────────
        ctx["missed_by_topic"] = (
            UserAnswer.objects.filter(user=user, is_correct=False)
            .values("question__topic__name", "question__topic__domain__title",
                    "question__topic__id")
            .annotate(miss_count=Count("id"))
            .order_by("-miss_count")[:9]
        )

        # ── Weakest started topics ────────────────────────────────────
        ctx["weakest_topics"] = (
            TopicProgress.objects.filter(user=user)
            .exclude(status="not_started")
            .select_related("topic__domain")
            .order_by("confidence")[:5]
        )

        # ── All topics with progress for the progress table ───────────
        all_topics = Topic.objects.filter(is_active=True).select_related("domain").order_by(
            "domain__order", "order"
        )
        topic_progress_map = {
            tp.topic_id: tp
            for tp in TopicProgress.objects.filter(user=user)
        }
        ctx["all_topic_rows"] = [
            {
                "topic": t,
                "progress": topic_progress_map.get(t.pk),
            }
            for t in all_topics
        ]

        return ctx


# ── Per-topic progress ─────────────────────────────────────────────────────

class TopicProgressView(LoginRequiredMixin, TemplateView):
    """Drill-down showing a user's history and stats for one topic."""

    template_name = "progress/topic_progress.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        topic = get_object_or_404(Topic, pk=self.kwargs["pk"], is_active=True)
        user = self.request.user

        tp, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)

        # Recent quiz answers for this topic
        recent_answers = (
            UserAnswer.objects.filter(user=user, question__topic=topic)
            .select_related("question")
            .prefetch_related("selected_choices", "question__choices")
            .order_by("-answered_at")[:10]
        )

        # Lab completion for this topic
        from labs.models import CodingChallenge, CodingAttempt
        labs = CodingChallenge.objects.filter(topic=topic, is_active=True)
        completed_lab_ids = set(
            CodingAttempt.objects.filter(
                user=user, challenge__topic=topic, is_correct=True
            ).values_list("challenge_id", flat=True)
        )

        ctx.update(
            {
                "topic": topic,
                "progress": tp,
                "recent_answers": recent_answers,
                "labs": labs,
                "completed_lab_ids": completed_lab_ids,
                "has_questions": topic.questions.filter(is_active=True).exists(),
            }
        )
        return ctx


# ── API endpoints ──────────────────────────────────────────────────────────

class RecommendationAPIView(LoginRequiredMixin, View):
    """JSON — recommended next topic for HTMX/JS updates."""

    def get(self, request):
        topic = services.get_recommendation(request.user)
        if topic:
            return JsonResponse(
                {
                    "topic_id": topic.id,
                    "topic_name": topic.name,
                    "domain_name": topic.domain.title,
                    "domain_order": topic.domain.order,
                }
            )
        return JsonResponse(
            {"topic_id": None, "message": "Start learning to get recommendations!"}
        )


class ReadinessAPIView(LoginRequiredMixin, View):
    """JSON — live readiness score."""

    def get(self, request):
        score = services.readiness_score(request.user)
        if score >= 80:
            label = "Exam Ready"
        elif score >= 65:
            label = "Nearly There"
        else:
            label = "Keep Studying"
        return JsonResponse({"score": score, "label": label})
