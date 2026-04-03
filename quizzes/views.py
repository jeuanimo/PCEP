"""Quiz views for PCEP Prep Coach.

URL → view map
──────────────
  /quiz/                              QuizHubView
  /quiz/topic/<pk>/                   TopicQuizView
  /quiz/domain/<pk>/                  DomainQuizView
  /quiz/mixed/                        MixedQuizView
  /quiz/exam/                         ExamModeView
  /quiz/submit/<attempt_pk>/          SubmitQuizView
  /quiz/results/<pk>/                 QuizResultsView
  /quiz/review/                       ReviewMistakesView
  /quiz/review/practice/              ReviewQuizView
"""
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, TemplateView, View

from learning.models import Domain, Topic
from progress.models import TopicProgress
from progress.services import get_review_questions, invalidate_user_progress_cache

from .forms import DomainQuizForm, TopicQuizForm
from .models import AnswerChoice, Question, QuizAttempt, UserAnswer
from .services import (
    EXAM_TOTAL,
    MIXED_QUIZ_TOTAL,
    analyse_topic_breakdown,
    analyse_weak_areas,
    pick_domain_questions,
    pick_topic_questions,
    pick_weighted_questions,
    score_text_answer,
)

QUIZ_TEMPLATE = "quizzes/quiz.html"


# ── Quiz hub ───────────────────────────────────────────────────────────────

class QuizHubView(LoginRequiredMixin, TemplateView):
    """Landing page — let the user pick their quiz mode and configure it."""
    template_name = "quizzes/quiz_hub.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["domains"] = Domain.objects.filter(is_active=True).order_by("order")
        ctx["topics"] = (
            Topic.objects.filter(is_active=True)
            .select_related("domain")
            .order_by("domain__order", "order")
        )
        ctx["domain_form"]     = DomainQuizForm()
        ctx["topic_form"]      = TopicQuizForm()
        ctx["recent_attempts"] = (
            QuizAttempt.objects.filter(user=self.request.user, finished_at__isnull=False)
            .select_related("topic", "domain")
            .order_by("-started_at")[:5]
        )
        return ctx


# ── Topic quiz ─────────────────────────────────────────────────────────────

class TopicQuizView(LoginRequiredMixin, TemplateView):
    """Focused drill on a single topic (up to 10 questions)."""
    template_name = QUIZ_TEMPLATE

    def get_context_data(self, **kwargs):
        ctx   = super().get_context_data(**kwargs)
        topic = get_object_or_404(Topic, pk=kwargs["topic_pk"])

        count     = min(int(self.request.GET.get("count", 10)), 20)
        questions = pick_topic_questions(topic, count)

        attempt = QuizAttempt.objects.create(
            user=self.request.user,
            mode="topic",
            topic=topic,
            total_questions=len(questions),
        )
        ctx.update({
            "topic":      topic,
            "questions":  questions,
            "attempt":    attempt,
            "mode_label": f"Topic Quiz — {topic.name}",
            "time_limit": None,
            "q_total":    len(questions),
        })
        return ctx


# ── Domain quiz ────────────────────────────────────────────────────────────

class DomainQuizView(LoginRequiredMixin, TemplateView):
    """Drill on all topics within one PCEP domain."""
    template_name = QUIZ_TEMPLATE

    def get_context_data(self, **kwargs):
        ctx    = super().get_context_data(**kwargs)
        domain = get_object_or_404(Domain, pk=kwargs["domain_pk"])

        count     = min(int(self.request.GET.get("count", 15)), 30)
        questions = pick_domain_questions(domain, count)

        attempt = QuizAttempt.objects.create(
            user=self.request.user,
            mode="domain",
            domain=domain,
            total_questions=len(questions),
        )
        ctx.update({
            "domain":     domain,
            "questions":  questions,
            "attempt":    attempt,
            "mode_label": f"Domain Quiz — {domain.title}",
            "time_limit": None,
            "q_total":    len(questions),
        })
        return ctx


# ── Mixed mode ─────────────────────────────────────────────────────────────

class MixedQuizView(LoginRequiredMixin, TemplateView):
    """Weighted 20-question mixed quiz — same blueprint proportions as the exam."""
    template_name = QUIZ_TEMPLATE

    def get_context_data(self, **kwargs):
        ctx       = super().get_context_data(**kwargs)
        questions = pick_weighted_questions(total=MIXED_QUIZ_TOTAL)

        attempt = QuizAttempt.objects.create(
            user=self.request.user,
            mode="mixed",
            total_questions=len(questions),
        )
        ctx.update({
            "questions":  questions,
            "attempt":    attempt,
            "mode_label": "Mixed Mode Quiz",
            "time_limit": None,
            "q_total":    len(questions),
        })
        return ctx


# ── Exam mode ──────────────────────────────────────────────────────────────

class ExamModeView(LoginRequiredMixin, TemplateView):
    """Full 40-question timed exam simulation, weighted by PCEP blueprint."""
    template_name = QUIZ_TEMPLATE

    def get_context_data(self, **kwargs):
        ctx        = super().get_context_data(**kwargs)
        questions  = pick_weighted_questions(total=EXAM_TOTAL)
        time_limit = 45 * 60  # 45 minutes in seconds

        attempt = QuizAttempt.objects.create(
            user=self.request.user,
            mode="exam",
            total_questions=len(questions),
            time_limit_seconds=time_limit,
        )
        ctx.update({
            "questions":  questions,
            "attempt":    attempt,
            "mode_label": "Full Exam Mode",
            "time_limit": time_limit,
            "q_total":    len(questions),
        })
        return ctx


# ── Submit & grade ─────────────────────────────────────────────────────────

class SubmitQuizView(LoginRequiredMixin, View):
    """Receive the POSTed form, score every answer, update progress records,
    and redirect to the results page."""

    def post(self, request, attempt_pk):
        attempt      = get_object_or_404(QuizAttempt, pk=attempt_pk, user=request.user)
        question_ids = request.POST.getlist("question_ids")
        correct      = 0

        for raw_qid in question_ids:
            try:
                question = Question.objects.prefetch_related("choices").get(pk=int(raw_qid))
            except (ValueError, Question.DoesNotExist):
                continue

            # Guard against double-submit creating duplicate rows
            ua, _created = UserAnswer.objects.get_or_create(
                attempt=attempt,
                question=question,
                defaults={"user": request.user},
            )

            if question.question_type in ("mc", "ms", "tf"):
                selected_ids = request.POST.getlist(f"q_{question.pk}")
                if _created:
                    ua.save()  # need PK before setting M2M
                ua.selected_choices.set(selected_ids)
                correct_ids = set(
                    question.choices.filter(is_correct=True).values_list("id", flat=True)
                )
                ua.is_correct = ({int(x) for x in selected_ids} == correct_ids)
            else:
                raw_text      = request.POST.get(f"q_{question.pk}_text", "").strip()
                ua.text_answer = raw_text
                ua.is_correct  = score_text_answer(question, raw_text)

            ua.save(update_fields=["is_correct", "text_answer"] if not _created else None)

            if ua.is_correct:
                correct += 1

            # Update TopicProgress confidence
            tp, _ = TopicProgress.objects.get_or_create(
                user=request.user, topic=question.topic
            )
            tp.record_answer(ua.is_correct)

        # Finalise the attempt in one save via the model method
        attempt.finalise(correct=correct, total=max(len(question_ids), 1))

        # Invalidate cached aggregates so the dashboard reflects this attempt
        invalidate_user_progress_cache(request.user)

        # Maintain study streak
        profile = getattr(request.user, "profile", None)
        if profile:
            profile.update_streak()

        return redirect("quizzes:quiz_results", pk=attempt.pk)


# ── Results ────────────────────────────────────────────────────────────────

class QuizResultsView(LoginRequiredMixin, DetailView):
    """Score summary, per-domain breakdown, weak-area callout, and answer review."""
    model               = QuizAttempt
    template_name       = "quizzes/quiz_results.html"
    context_object_name = "attempt"

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        answers = list(
            self.object.answers
            .select_related("question__topic__domain")
            .prefetch_related("selected_choices", "question__choices")
            .order_by("answered_at")
        )
        ctx["answers"]          = answers
        ctx["domain_breakdown"] = analyse_weak_areas(answers)
        ctx["weak_topics"]      = analyse_topic_breakdown(answers)
        return ctx


# ── Review mistakes ────────────────────────────────────────────────────────

class ReviewMistakesView(LoginRequiredMixin, TemplateView):
    """Missed questions grouped by domain → topic, with per-topic retry links."""
    template_name = "quizzes/review.html"

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user
        highlighted_qid = self.request.GET.get("question", "").strip()

        wrong_ids = set(
            UserAnswer.objects.filter(user=user, is_correct=False)
            .values_list("question_id", flat=True)
        )
        right_ids = set(
            UserAnswer.objects.filter(user=user, is_correct=True)
            .values_list("question_id", flat=True)
        )
        never_right_ids = wrong_ids - right_ids

        # Fetch all wrong answers for never-right questions, ordered for grouping
        all_missed = (
            UserAnswer.objects.filter(
                user=user,
                is_correct=False,
                question_id__in=never_right_ids,
            )
            .select_related("question__topic__domain")
            .prefetch_related("question__choices", "selected_choices")
            .order_by(
                "question__topic__domain__order",
                "question__topic__order",
                "-answered_at",
            )
        )

        # Keep only the most-recent wrong answer per question (SQLite-safe)
        seen: set = set()
        missed = []
        for ua in all_missed:
            if ua.question_id not in seen:
                seen.add(ua.question_id)
                missed.append(ua)

        # Group into domain → topic → [UserAnswer]
        domain_map: dict = defaultdict(lambda: defaultdict(list))
        for ua in missed:
            domain_map[ua.question.topic.domain][ua.question.topic].append(ua)

        grouped = []
        for domain in Domain.objects.filter(is_active=True).order_by("order"):
            if domain not in domain_map:
                continue
            topic_groups = []
            for topic in Topic.objects.filter(
                domain=domain, is_active=True
            ).order_by("order"):
                if topic not in domain_map[domain]:
                    continue
                answers = domain_map[domain][topic]
                topic_groups.append({
                    "topic":      topic,
                    "answers":    answers,
                    "miss_count": len(answers),
                })
            if topic_groups:
                grouped.append({"domain": domain, "topics": topic_groups})

        ctx["grouped"]      = grouped
        ctx["missed_count"] = len(never_right_ids)
        ctx["highlighted_qid"] = highlighted_qid
        return ctx


class ReviewQuizView(LoginRequiredMixin, TemplateView):
    """Interactive quiz built from the user's never-got-right questions."""
    template_name = QUIZ_TEMPLATE

    def get_context_data(self, **kwargs):
        ctx       = super().get_context_data(**kwargs)
        questions = get_review_questions(self.request.user, limit=20)

        if not questions:
            ctx["no_review_questions"] = True
            ctx["questions"]           = []
            return ctx

        attempt = QuizAttempt.objects.create(
            user=self.request.user,
            mode="review",
            total_questions=len(questions),
        )
        ctx.update({
            "questions":  questions,
            "attempt":    attempt,
            "mode_label": "Mistake Review",
            "time_limit": None,
            "q_total":    len(questions),
        })
        return ctx
