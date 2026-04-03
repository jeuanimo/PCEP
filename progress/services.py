"""
Progress calculation helpers for PCEP Prep Coach.

All heavy business logic lives here so views stay thin and helpers
are independently testable without HTTP context.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.cache import cache
from django.db.models import Avg, Count, Sum
from django.urls import reverse

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from learning.models import Topic
    from labs.models import CodingChallenge


# ── Readiness score ────────────────────────────────────────────────────────

def _user_cache_key(prefix: str, user) -> str:
    return f"pcep:{prefix}:{user.pk}"


def invalidate_user_progress_cache(user) -> None:
    """Clear all cached progress aggregates for *user*.

    Call this after any event that changes TopicProgress (quiz submit, lab
    solve, lesson read) so the next dashboard load reflects fresh data.
    """
    cache.delete_many([
        _user_cache_key("readiness", user),
        _user_cache_key("domain_stats", user),
        _user_cache_key("missed_count", user),
    ])


def readiness_score(user: "AbstractUser") -> float:
    """Weighted exam readiness score (0–100).

    Formula
    -------
    readiness = Σ ( domain.weight × domain_avg_confidence )

    where domain_avg_confidence = total_confidence_of_started_topics
                                  ÷ count_of_ALL_active_topics_in_domain

    Crucially the denominator is ALL topics so completely unstarted
    domains pull the score down — this gives an honest readiness picture.

    Result is cached for 60 s per user (dashboard may call this multiple
    times; the cache avoids repeated aggregate queries).
    """
    ck = _user_cache_key("readiness", user)
    cached = cache.get(ck)
    if cached is not None:
        return cached

    from learning.models import Domain
    from .models import TopicProgress

    total = 0.0
    for domain in Domain.objects.filter(is_active=True).prefetch_related("topics"):
        topic_count = domain.topics.filter(is_active=True).count()
        if not topic_count:
            continue
        conf_sum = (
            TopicProgress.objects.filter(user=user, topic__domain=domain)
            .aggregate(s=Sum("confidence"))["s"] or 0
        )
        # Average over ALL topics, not just started ones
        avg_conf = conf_sum / topic_count
        total += avg_conf * domain.weight   # domain.weight returns 0-1 float
    result = round(min(total, 100), 1)
    cache.set(ck, result, timeout=60)
    return result


# ── Domain-level stats ─────────────────────────────────────────────────────

def domain_stats(user: "AbstractUser") -> list[dict]:
    """Return a stats dict for every active domain.

    Each dict contains:
        domain          Domain instance
        mastery         average confidence across ALL topics (0-100 int)
        topic_count     total active topics in domain
        studied_count   topics with at least one attempt
        mastered_count  topics with status='mastered'
        color_class     CSS class (bg-domain-1 … bg-domain-4)

    Result is cached for 60 s per user.
    """
    ck = _user_cache_key("domain_stats", user)
    cached = cache.get(ck)
    if cached is not None:
        return cached

    from learning.models import Domain
    from .models import TopicProgress

    stats = []
    for domain in Domain.objects.filter(is_active=True).prefetch_related("topics"):
        all_topics = list(domain.topics.filter(is_active=True).values_list("id", flat=True))
        topic_count = len(all_topics)
        if not topic_count:
            continue

        progresses = TopicProgress.objects.filter(user=user, topic_id__in=all_topics)
        conf_sum = progresses.aggregate(s=Sum("confidence"))["s"] or 0
        avg_conf = conf_sum / topic_count

        stats.append({
            "domain": domain,
            "mastery": round(avg_conf),
            "topic_count": topic_count,
            "studied_count": progresses.exclude(status="not_started").count(),
            "mastered_count": progresses.filter(status="mastered").count(),
            "color_class": f"bg-domain-{domain.order}",
        })
    cache.set(ck, stats, timeout=60)
    return stats


# ── Smart recommendation ───────────────────────────────────────────────────

def get_recommendation(user: "AbstractUser") -> "Topic | None":
    """Return the highest-priority topic for the user to study next.

    Priority formula
    ----------------
    priority = domain.weight_percent × (100 – domain_avg_confidence)

    This gives highest urgency to high-weight domains where mastery is low.
    Within the winning domain, pick the weakest unmastered topic.
    """
    from learning.models import Domain, Topic
    from .models import TopicProgress

    best_domain = None
    best_priority = -1.0

    for domain in Domain.objects.filter(is_active=True):
        topic_count = domain.topics.filter(is_active=True).count()
        if not topic_count:
            continue
        conf_sum = (
            TopicProgress.objects.filter(user=user, topic__domain=domain)
            .aggregate(s=Sum("confidence"))["s"] or 0
        )
        avg_conf = conf_sum / topic_count
        priority = domain.weight_percent * (100 - avg_conf)
        if priority > best_priority:
            best_priority = priority
            best_domain = domain

    if not best_domain:
        return None

    # Prefer the weakest un-mastered topic that has already been started
    tp = (
        TopicProgress.objects.filter(
            user=user, topic__domain=best_domain, topic__is_active=True
        )
        .exclude(status="mastered")
        .order_by("confidence")
        .select_related("topic")
        .first()
    )
    if tp:
        return tp.topic

    # Fall back to the first topic with no progress record at all
    started_ids = TopicProgress.objects.filter(
        user=user, topic__domain=best_domain
    ).values_list("topic_id", flat=True)
    return (
        best_domain.topics.filter(is_active=True)
        .exclude(id__in=started_ids)
        .first()
        or best_domain.topics.filter(is_active=True).first()
    )


# ── Activity feed ──────────────────────────────────────────────────────────

def get_recent_activity(user: "AbstractUser", limit: int = 8) -> list[dict]:
    """Combined chronological activity feed from quizzes and lab completions.

    Each item:
        type    'quiz' | 'lab'
        date    datetime
        label   human-readable description
        score   float | None (quiz score %)
        icon    Bootstrap Icons class
        color   Bootstrap contextual colour name
        url     detail/review URL
        passed  bool
    """
    from quizzes.models import QuizAttempt
    from labs.models import CodingAttempt

    items: list[dict] = []

    def _quiz_color(score: int) -> str:
        if score >= 70:
            return "success"
        if score >= 50:
            return "warning"
        return "danger"

    for qa in (
        QuizAttempt.objects.filter(user=user, finished_at__isnull=False)
        .select_related("topic", "domain")
        .order_by("-started_at")[: limit * 2]
    ):
        scope = ""
        if qa.topic:
            scope = f" – {qa.topic.name}"
        elif qa.domain:
            scope = f" – {qa.domain.title}"
        items.append(
            {
                "type": "quiz",
                "date": qa.started_at,
                "label": f"{qa.get_mode_display()}{scope}",
                "score": qa.score,
                "icon": "bi-pencil-square",
                "color": _quiz_color(qa.score),
                "url": reverse("quizzes:quiz_results", args=[qa.pk]),
                "passed": qa.is_passed,
            }
        )

    for ca in (
        CodingAttempt.objects.filter(user=user, is_correct=True)
        .select_related("challenge")
        .order_by("-submitted_at")[: limit]
    ):
        items.append(
            {
                "type": "lab",
                "date": ca.submitted_at,
                "label": f"Solved: {ca.challenge.title}",
                "score": None,
                "icon": "bi-terminal-fill",
                "color": "success",
                "url": reverse("labs:challenge_detail", args=[ca.challenge.pk]),
                "passed": True,
            }
        )

    items.sort(key=lambda x: x["date"], reverse=True)
    return items[:limit]


# ── Review queue ───────────────────────────────────────────────────────────

def missed_question_count(user: "AbstractUser") -> int:
    """Count questions where the user has never answered correctly.

    A question is "still missed" when the user got it wrong at least once
    AND has never gotten it right in any attempt.

    Result is cached for 60 s per user.
    """
    ck = _user_cache_key("missed_count", user)
    cached = cache.get(ck)
    if cached is not None:
        return cached

    from quizzes.models import UserAnswer

    wrong_ids = set(
        UserAnswer.objects.filter(user=user, is_correct=False).values_list(
            "question_id", flat=True
        )
    )
    right_ids = set(
        UserAnswer.objects.filter(user=user, is_correct=True).values_list(
            "question_id", flat=True
        )
    )
    result = len(wrong_ids - right_ids)
    cache.set(ck, result, timeout=60)
    return result


def get_review_questions(user: "AbstractUser", limit: int = 20):
    """Return a prioritised list of questions to review.

    Priority formula (higher = reviewed first)
    -------------------------------------------
    score = miss_count × (1 + topic_weakness_bonus)

    where:
      miss_count         = total wrong answers for that question
      topic_weakness_bonus = (100 − topic_confidence) / 100
                           so a question from a 0%-confidence topic
                           scores 2× vs one from a 100%-confidence topic.

    Hard-rated flashcard topics get an extra ×1.3 multiplier — the user
    explicitly flagged those cards as difficult, so the related quiz
    questions should surface more often too.
    """
    from quizzes.models import Question, UserAnswer
    from .models import TopicProgress
    from learning.models import FlashcardRating

    # ── Never-right question IDs ──────────────────────────────────────
    wrong_qs = UserAnswer.objects.filter(user=user, is_correct=False)
    right_ids = set(
        UserAnswer.objects.filter(user=user, is_correct=True)
        .values_list("question_id", flat=True)
    )

    # miss_count per question (never-right only)
    from django.db.models import Count as _Count
    miss_counts: dict[int, int] = {
        row["question_id"]: row["cnt"]
        for row in wrong_qs.values("question_id")
                           .annotate(cnt=_Count("id"))
        if row["question_id"] not in right_ids
    }

    if not miss_counts:
        # Fallback: any ever-wrong question, flat ordering
        fallback_ids = set(wrong_qs.values_list("question_id", flat=True))
        return list(
            Question.objects.filter(id__in=fallback_ids, is_active=True)
            .prefetch_related("choices")
            .select_related("topic__domain")[:limit]
        )

    # ── Topic confidence map ──────────────────────────────────────────
    topic_conf: dict[int, int] = {
        tp.topic_id: tp.confidence
        for tp in TopicProgress.objects.filter(user=user)
    }

    # ── Hard-rated flashcard topics (user self-assessed as hard) ──────
    hard_topic_ids: set[int] = set(
        FlashcardRating.objects.filter(user=user, rating="hard")
        .values_list("flashcard__topic_id", flat=True)
        .distinct()
    )

    # ── Fetch questions and score them ────────────────────────────────
    questions = list(
        Question.objects.filter(id__in=miss_counts.keys(), is_active=True)
        .prefetch_related("choices")
        .select_related("topic__domain")
    )

    def _score(q: "Question") -> float:
        mc   = miss_counts.get(q.pk, 1)
        conf = topic_conf.get(q.topic_id, 0)
        weakness_bonus = (100 - conf) / 100          # 0.0 – 1.0
        hard_multiplier = 1.3 if q.topic_id in hard_topic_ids else 1.0
        return mc * (1 + weakness_bonus) * hard_multiplier

    questions.sort(key=_score, reverse=True)
    return questions[:limit]


# ── Lesson / lab completion signals ───────────────────────────────────────

def record_lesson_read(user: "AbstractUser", topic: "Topic") -> None:
    """Boost TopicProgress when a user reads a lesson for the first time.

    Reading a lesson is not as strong a signal as answering a question,
    so we apply a modest one-time +10 confidence bump and move status
    from 'not_started' → 'learning'.
    """
    from .models import TopicProgress

    tp, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)
    if tp.status == "not_started":
        tp.confidence = min(100, tp.confidence + 10)
        tp.status = "learning"
        tp.save(update_fields=["confidence", "status", "updated_at"])


def record_lab_solved(user: "AbstractUser", challenge: "CodingChallenge") -> None:
    """Extra confidence boost when a user correctly solves a coding challenge.

    Labs are harder to complete than a single MCQ so we award an
    additional +5 on top of the standard record_answer() bump.
    """
    from .models import TopicProgress

    tp, _ = TopicProgress.objects.get_or_create(user=user, topic=challenge.topic)
    tp.record_answer(is_correct=True)        # +bump from algorithm
    tp.confidence = min(100, tp.confidence + 5)  # lab bonus
    tp.save(update_fields=["confidence", "updated_at"])


def recompute_topic_progress(user: "AbstractUser", topic: "Topic") -> None:
    """Rebuild TopicProgress for one topic from quiz/lab history.

    This is useful when a user resets lab attempts and we need confidence,
    counts, and status to reflect remaining activity accurately.
    """
    from quizzes.models import UserAnswer
    from labs.models import CodingAttempt
    from .models import TopicProgress

    events: list[tuple] = []

    quiz_events = UserAnswer.objects.filter(
        user=user,
        question__topic=topic,
    ).values_list("answered_at", "is_correct")
    for answered_at, is_correct in quiz_events:
        events.append((answered_at, bool(is_correct), False))

    lab_events = CodingAttempt.objects.filter(
        user=user,
        challenge__topic=topic,
    ).values_list("submitted_at", "is_correct")
    for submitted_at, is_correct in lab_events:
        events.append((submitted_at, bool(is_correct), True))

    events.sort(key=lambda item: item[0])

    confidence = 0
    correct_count = 0
    incorrect_count = 0
    last_practiced = None

    for timestamp, is_correct, is_lab_event in events:
        last_practiced = timestamp
        if is_correct:
            correct_count += 1
            bump = max(2, (100 - confidence) // 5)
            confidence = min(100, confidence + bump)
            if is_lab_event:
                confidence = min(100, confidence + 5)  # same bonus as record_lab_solved
        else:
            incorrect_count += 1
            drop = max(3, confidence // 8)
            confidence = max(0, confidence - drop)

    total_attempts = correct_count + incorrect_count
    if confidence >= 80:
        status = "mastered"
    elif confidence >= 40:
        status = "practicing"
    elif total_attempts > 0:
        status = "learning"
    else:
        status = "not_started"

    tp, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)
    tp.confidence = confidence
    tp.correct_count = correct_count
    tp.incorrect_count = incorrect_count
    tp.last_practiced = last_practiced
    tp.status = status
    tp.save(update_fields=[
        "confidence",
        "correct_count",
        "incorrect_count",
        "last_practiced",
        "status",
        "updated_at",
    ])
