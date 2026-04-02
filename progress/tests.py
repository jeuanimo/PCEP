"""Tests for progress app — TopicProgress.record_answer() and services."""
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from learning.models import Domain, Topic
from .models import TopicProgress
from . import services

User = get_user_model()


_TEST_PASSWORD = "test-only-not-real"  # noqa: S105


def _make_user(username="testuser"):
    return User.objects.create_user(username=username, password=_TEST_PASSWORD)


def _make_domain(order=1, weight=25):
    return Domain.objects.create(
        title=f"Domain {order}",
        slug=f"domain-{order}",
        order=order,
        weight_percent=weight,
        is_active=True,
    )


def _make_topic(domain, name="Variables", order=1):
    return Topic.objects.create(
        domain=domain,
        name=name,
        slug=name.lower().replace(" ", "-"),
        order=order,
        is_active=True,
    )


# ── TopicProgress.record_answer ────────────────────────────────────────────

class RecordAnswerTests(TestCase):

    def setUp(self):
        self.user = _make_user()
        self.domain = _make_domain()
        self.topic = _make_topic(self.domain)
        self.tp = TopicProgress.objects.create(user=self.user, topic=self.topic)

    def test_correct_answer_increases_confidence(self):
        before = self.tp.confidence
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertGreater(self.tp.confidence, before)

    def test_correct_answer_increments_correct_count(self):
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertEqual(self.tp.correct_count, 1)

    def test_incorrect_answer_decreases_confidence(self):
        self.tp.confidence = 50
        self.tp.save(update_fields=["confidence"])
        self.tp.record_answer(is_correct=False)
        self.tp.refresh_from_db()
        self.assertLess(self.tp.confidence, 50)

    def test_incorrect_answer_increments_incorrect_count(self):
        self.tp.record_answer(is_correct=False)
        self.tp.refresh_from_db()
        self.assertEqual(self.tp.incorrect_count, 1)

    def test_confidence_never_exceeds_100(self):
        self.tp.confidence = 99
        self.tp.save(update_fields=["confidence"])
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertLessEqual(self.tp.confidence, 100)

    def test_confidence_never_goes_below_0(self):
        self.tp.confidence = 0
        self.tp.save(update_fields=["confidence"])
        self.tp.record_answer(is_correct=False)
        self.tp.refresh_from_db()
        self.assertGreaterEqual(self.tp.confidence, 0)

    def test_status_becomes_mastered_at_80(self):
        self.tp.confidence = 79
        self.tp.save(update_fields=["confidence"])
        # Bump that gets us to ≥80: (100-79)//5 = 4, so 79+4 = 83
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertEqual(self.tp.status, "mastered")

    def test_status_becomes_practicing_at_40(self):
        self.tp.confidence = 30
        self.tp.status = "learning"
        self.tp.save(update_fields=["confidence", "status"])
        # bump = (100-30)//5 = 14, so 30+14 = 44
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertEqual(self.tp.status, "practicing")

    def test_last_practiced_is_updated(self):
        self.assertIsNone(self.tp.last_practiced)
        self.tp.record_answer(is_correct=True)
        self.tp.refresh_from_db()
        self.assertIsNotNone(self.tp.last_practiced)

    def test_accuracy_property(self):
        self.tp.correct_count = 3
        self.tp.incorrect_count = 1
        self.tp.save(update_fields=["correct_count", "incorrect_count"])
        self.assertEqual(self.tp.accuracy, 75.0)

    def test_accuracy_none_when_no_attempts(self):
        self.assertIsNone(self.tp.accuracy)


# ── services.readiness_score ───────────────────────────────────────────────

class ReadinessScoreTests(TestCase):

    def setUp(self):
        cache.clear()  # prevent cached values from previous tests bleeding through
        self.user = _make_user("reader")
        self.domain = _make_domain(order=1, weight=100)  # 100% weight for easy math
        self.topic = _make_topic(self.domain)

    def test_zero_when_no_progress(self):
        score = services.readiness_score(self.user)
        self.assertEqual(score, 0.0)

    def test_reflects_confidence(self):
        TopicProgress.objects.create(
            user=self.user, topic=self.topic, confidence=60
        )
        score = services.readiness_score(self.user)
        # domain has weight=1.0, one topic, confidence=60 → score=60
        self.assertAlmostEqual(score, 60.0, delta=1.0)

    def test_capped_at_100(self):
        TopicProgress.objects.create(
            user=self.user, topic=self.topic, confidence=100
        )
        score = services.readiness_score(self.user)
        self.assertLessEqual(score, 100.0)


# ── services.missed_question_count ─────────────────────────────────────────

class MissedQuestionCountTests(TestCase):

    def setUp(self):
        self.user = _make_user("missed")

    def test_zero_when_no_answers(self):
        self.assertEqual(services.missed_question_count(self.user), 0)


# ── services.invalidate_user_progress_cache ───────────────────────────────

class InvalidateCacheTests(TestCase):

    def test_invalidate_does_not_raise(self):
        user = _make_user("cacheuser")
        # Should not raise even if nothing was cached
        services.invalidate_user_progress_cache(user)
