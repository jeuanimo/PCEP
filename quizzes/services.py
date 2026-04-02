"""
Quiz business logic — kept separate from views so it can be tested independently.

Key functions
─────────────
  pick_weighted_questions(total)  weighted exam / mixed-mode sampling
  pick_domain_questions(domain)   single-domain drill
  pick_topic_questions(topic)     single-topic drill
  analyse_weak_areas(answers)     per-domain result breakdown
  score_text_answer(question, raw_text)  flexible text comparison

Weighted selection algorithm
─────────────────────────────
For exam / mixed mode the official PCEP-30-02 blueprint weights are used:

  Domain 1 – Fundamentals          18 %  →  ~7 of 40 questions
  Domain 2 – Control Flow          29 %  → ~12 of 40 questions
  Domain 3 – Data Collections      25 %  → ~10 of 40 questions
  Domain 4 – Functions/Exceptions  28 %  → ~11 of 40 questions

Steps:
  1. For each domain compute quota = round(total × weight).
  2. Shuffle that domain's active question pool and take the first `quota`.
  3. If a domain's pool is smaller than its quota, take everything available.
  4. After all domains are sampled, trim the combined list to exactly `total`
     (rounding can push 1–2 questions over) and shuffle once more so
     questions from different domains are interleaved.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from learning.models import Domain, Topic
    from .models import Question, UserAnswer


# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_WEIGHTS: dict[int, float] = {
    1: 0.18,
    2: 0.29,
    3: 0.25,
    4: 0.28,
}

TOPIC_QUIZ_CAP    = 10   # max questions for a topic drill
DOMAIN_QUIZ_CAP   = 15   # max questions for a domain drill
MIXED_QUIZ_TOTAL  = 20   # default for mixed mode (weighted, not full exam)
EXAM_TOTAL        = 40   # official PCEP question count


# ── Question pickers ───────────────────────────────────────────────────────

def pick_weighted_questions(total: int = EXAM_TOTAL) -> list["Question"]:
    """Return `total` questions sampled proportionally across domains.

    Uses PCEP_DOMAIN_WEIGHTS from settings (falls back to DEFAULT_WEIGHTS).
    Each domain's quota is determined by its weight.  Questions are drawn
    randomly from each domain's pool, then the combined set is shuffled.

    Args:
        total: How many questions to return (40 for exam, 20 for mixed mode).

    Returns:
        A shuffled list of Question instances with choices prefetched.
    """
    from learning.models import Domain
    from .models import Question as Q

    weights: dict[int, float] = getattr(settings, "PCEP_DOMAIN_WEIGHTS", DEFAULT_WEIGHTS)
    selected: list["Question"] = []

    for domain in Domain.objects.filter(is_active=True).order_by("order"):
        weight = weights.get(domain.order, 1 / 4)
        quota  = max(1, round(total * weight))

        pool = list(
            Q.objects.filter(topic__domain=domain, is_active=True)
            .prefetch_related("choices")
            .select_related("topic__domain")
        )
        random.shuffle(pool)
        selected.extend(pool[:quota])

    # Trim to exact target (rounding may give total ± 1) then shuffle
    random.shuffle(selected)
    return selected[:total]


def pick_domain_questions(domain: "Domain", count: int = DOMAIN_QUIZ_CAP) -> list["Question"]:
    """Return up to `count` randomly sampled questions from a single domain."""
    from .models import Question as Q

    pool = list(
        Q.objects.filter(topic__domain=domain, is_active=True)
        .prefetch_related("choices")
        .select_related("topic__domain")
    )
    random.shuffle(pool)
    return pool[:count]


def pick_topic_questions(topic: "Topic", count: int = TOPIC_QUIZ_CAP) -> list["Question"]:
    """Return up to `count` randomly sampled questions from a single topic."""
    pool = list(
        topic.questions.filter(is_active=True)
        .prefetch_related("choices")
        .select_related("topic__domain")
    )
    random.shuffle(pool)
    return pool[:count]


# ── Answer scoring ─────────────────────────────────────────────────────────

def score_text_answer(question: "Question", raw: str) -> bool:
    """Return True if `raw` matches any correct answer for a text-entry question.

    Matching rules (applied in order until one succeeds):
      1. Exact match after strip + lower-case (catches minor capitalisation)
      2. Correct answer is a subset of the user's answer (for multi-word fill-ins)
      3. User answer is a subset of the correct answer (partial credit — disabled
         in exam mode; kept here for review / practice modes)

    Only rules 1 and 2 are used; rule 3 is intentionally left out to avoid
    rewarding guesses.
    """
    correct_choice = question.choices.filter(is_correct=True).first()
    if not correct_choice:
        return False

    user_text    = raw.strip().lower()
    correct_text = correct_choice.text.strip().lower()

    # Rule 1: exact (case-insensitive)
    if user_text == correct_text:
        return True

    # Rule 2: correct answer appears literally inside the user's answer
    # (handles "The answer is print()" when correct is "print()")
    if correct_text and correct_text in user_text:
        return True

    return False


# ── Weak-area analysis ─────────────────────────────────────────────────────

def analyse_weak_areas(answers) -> list[dict]:
    """Produce a per-domain score breakdown from a collection of UserAnswer objects.

    Returns a list of dicts sorted by domain order:
      {
        "domain":       Domain instance,
        "correct":      int,
        "total":        int,
        "score":        float (0–100),
        "is_weak":      bool  (score < 70 — the PCEP passing threshold),
        "color_class":  str   (Bootstrap/custom CSS class for bar colour),
      }
    """
    bucket: dict[int, dict] = defaultdict(lambda: {"domain": None, "correct": 0, "total": 0})

    for ua in answers:
        d = ua.question.topic.domain
        bucket[d.pk]["domain"] = d
        bucket[d.pk]["total"]  += 1
        if ua.is_correct:
            bucket[d.pk]["correct"] += 1

    result = []
    for data in sorted(bucket.values(), key=lambda x: x["domain"].order):
        total   = data["total"]
        correct = data["correct"]
        score   = round(correct / total * 100, 1) if total else 0.0
        is_weak = score < 70

        if score >= 70:
            color_class = "bg-success"
        elif score >= 40:
            color_class = "bg-warning"
        else:
            color_class = "bg-danger"

        result.append({
            "domain":      data["domain"],
            "correct":     correct,
            "total":       total,
            "score":       score,
            "is_weak":     is_weak,
            "color_class": color_class,
        })

    return result


def analyse_topic_breakdown(answers) -> list[dict]:
    """Per-topic breakdown, filtered to topics where the user scored below 70 %.

    Returns a list sorted by score ascending (weakest first):
      {
        "topic":    Topic instance,
        "correct":  int,
        "total":    int,
        "score":    float,
      }
    """
    bucket: dict[int, dict] = defaultdict(lambda: {"topic": None, "correct": 0, "total": 0})

    for ua in answers:
        t = ua.question.topic
        bucket[t.pk]["topic"]  = t
        bucket[t.pk]["total"]  += 1
        if ua.is_correct:
            bucket[t.pk]["correct"] += 1

    result = []
    for data in bucket.values():
        total  = data["total"]
        score  = round(data["correct"] / total * 100, 1) if total else 0.0
        if score < 70:   # only include weak topics
            result.append({
                "topic":   data["topic"],
                "correct": data["correct"],
                "total":   total,
                "score":   score,
            })

    return sorted(result, key=lambda x: x["score"])
