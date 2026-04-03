"""Tests for quizzes.services — question picking and answer scoring."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from learning.models import Domain, Topic
from .models import AnswerChoice, Question, QuizAttempt, UserAnswer
from .services import (
    analyse_weak_areas,
    pick_domain_questions,
    pick_topic_questions,
    pick_weighted_questions,
    score_text_answer,
)


def _make_domain(order=1, weight=25):
    return Domain.objects.create(
        title=f"Domain {order}",
        slug=f"domain-{order}",
        order=order,
        weight_percent=weight,
        is_active=True,
    )


def _make_topic(domain, name="Vars", order=1):
    return Topic.objects.create(
        domain=domain,
        name=name,
        slug=name.lower().replace(" ", "-"),
        order=order,
        is_active=True,
    )


def _make_question(topic, text="Q?", qtype="mc"):
    q = Question.objects.create(
        topic=topic,
        domain=topic.domain,
        text=text,
        question_type=qtype,
        is_active=True,
    )
    AnswerChoice.objects.create(question=q, text="Correct", is_correct=True, order=1)
    AnswerChoice.objects.create(question=q, text="Wrong", is_correct=False, order=2)
    return q


# ── pick_topic_questions ───────────────────────────────────────────────────

class PickTopicQuestionsTests(TestCase):

    def setUp(self):
        self.domain = _make_domain()
        self.topic = _make_topic(self.domain)
        for i in range(5):
            _make_question(self.topic, text=f"Q{i}")

    def test_returns_at_most_count(self):
        qs = pick_topic_questions(self.topic, count=3)
        self.assertLessEqual(len(qs), 3)

    def test_returns_all_when_count_exceeds_pool(self):
        qs = pick_topic_questions(self.topic, count=20)
        self.assertEqual(len(qs), 5)

    def test_excludes_inactive_questions(self):
        inactive = _make_question(self.topic, text="Inactive")
        inactive.is_active = False
        inactive.save(update_fields=["is_active"])
        qs = pick_topic_questions(self.topic, count=20)
        ids = [q.pk for q in qs]
        self.assertNotIn(inactive.pk, ids)

    def test_returns_empty_for_topic_with_no_questions(self):
        empty_topic = _make_topic(self.domain, name="Empty", order=99)
        qs = pick_topic_questions(empty_topic)
        self.assertEqual(qs, [])


# ── pick_domain_questions ──────────────────────────────────────────────────

class PickDomainQuestionsTests(TestCase):

    def setUp(self):
        self.domain = _make_domain()
        self.topic = _make_topic(self.domain)
        for i in range(6):
            _make_question(self.topic, text=f"DQ{i}")

    def test_returns_at_most_count(self):
        qs = pick_domain_questions(self.domain, count=4)
        self.assertLessEqual(len(qs), 4)

    def test_returns_all_when_pool_smaller_than_count(self):
        qs = pick_domain_questions(self.domain, count=100)
        self.assertEqual(len(qs), 6)


# ── pick_weighted_questions ────────────────────────────────────────────────

class PickWeightedQuestionsTests(TestCase):

    def setUp(self):
        # Two domains with questions
        self.d1 = _make_domain(order=1, weight=50)
        self.d2 = _make_domain(order=2, weight=50)
        t1 = _make_topic(self.d1, "T1")
        t2 = _make_topic(self.d2, "T2")
        for i in range(10):
            _make_question(t1, text=f"D1Q{i}")
            _make_question(t2, text=f"D2Q{i}")

    def test_returns_at_most_total(self):
        qs = pick_weighted_questions(total=5)
        self.assertLessEqual(len(qs), 5)

    def test_returns_questions_from_multiple_domains(self):
        qs = pick_weighted_questions(total=10)
        domains = {q.domain_id for q in qs}
        self.assertGreater(len(domains), 1)


# ── score_text_answer ──────────────────────────────────────────────────────

class ScoreTextAnswerTests(TestCase):

    def setUp(self):
        domain = _make_domain()
        topic = _make_topic(domain)
        self.question = Question.objects.create(
            topic=topic,
            domain=domain,
            text="What is the print function?",
            question_type="fib",
            is_active=True,
        )
        AnswerChoice.objects.create(
            question=self.question, text="print()", is_correct=True, order=1
        )

    def test_exact_match(self):
        self.assertTrue(score_text_answer(self.question, "print()"))

    def test_case_insensitive_match(self):
        self.assertTrue(score_text_answer(self.question, "PRINT()"))

    def test_correct_answer_within_longer_answer(self):
        self.assertTrue(score_text_answer(self.question, "The answer is print()"))

    def test_wrong_answer(self):
        self.assertFalse(score_text_answer(self.question, "input()"))

    def test_empty_answer(self):
        self.assertFalse(score_text_answer(self.question, ""))

    def test_no_correct_choice_returns_false(self):
        domain = _make_domain(order=99, weight=1)
        topic = _make_topic(domain, "NoChoice", order=99)
        q = Question.objects.create(
            topic=topic, domain=domain, text="?", question_type="fib", is_active=True
        )
        self.assertFalse(score_text_answer(q, "anything"))


# ── analyse_weak_areas ─────────────────────────────────────────────────────

class AnalyseWeakAreasTests(TestCase):

    def test_empty_answers_returns_empty(self):
        self.assertEqual(analyse_weak_areas([]), [])


class SubmitQuizScoringTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="quizuser",
            password="testpass123",
        )
        self.client.force_login(self.user)
        self.domain = _make_domain()
        self.topic = _make_topic(self.domain)

    def test_multiple_choice_correct_answer_is_counted(self):
        question = _make_question(self.topic, text="Correct MC")
        correct_choice = question.choices.get(is_correct=True)
        attempt = QuizAttempt.objects.create(
            user=self.user,
            mode="topic",
            topic=self.topic,
            total_questions=1,
        )

        response = self.client.post(
            reverse("quizzes:submit_quiz", args=[attempt.pk]),
            {
                "question_ids": [str(question.pk)],
                f"q_{question.pk}": str(correct_choice.pk),
            },
        )

        attempt.refresh_from_db()
        answer = UserAnswer.objects.get(attempt=attempt, question=question)

        self.assertRedirects(response, reverse("quizzes:quiz_results", args=[attempt.pk]))
        self.assertTrue(answer.is_correct)
        self.assertEqual(attempt.correct_count, 1)
        self.assertEqual(attempt.total_questions, 1)
        self.assertEqual(attempt.score, 100.0)
        self.assertTrue(attempt.is_passed)

    def test_text_answer_correct_response_is_counted(self):
        question = Question.objects.create(
            topic=self.topic,
            domain=self.domain,
            text="Type the function",
            question_type="fib",
            is_active=True,
        )
        AnswerChoice.objects.create(
            question=question,
            text="print()",
            is_correct=True,
            order=1,
        )
        attempt = QuizAttempt.objects.create(
            user=self.user,
            mode="topic",
            topic=self.topic,
            total_questions=1,
        )

        self.client.post(
            reverse("quizzes:submit_quiz", args=[attempt.pk]),
            {
                "question_ids": [str(question.pk)],
                f"q_{question.pk}_text": "print()",
            },
        )

        attempt.refresh_from_db()
        answer = UserAnswer.objects.get(attempt=attempt, question=question)

        self.assertEqual(answer.text_answer, "print()")
        self.assertTrue(answer.is_correct)
        self.assertEqual(attempt.correct_count, 1)
        self.assertEqual(attempt.score, 100.0)

    def test_multi_select_requires_exact_set_of_correct_choices(self):
        question = Question.objects.create(
            topic=self.topic,
            domain=self.domain,
            text="Pick both correct answers",
            question_type="ms",
            is_active=True,
        )
        correct_one = AnswerChoice.objects.create(
            question=question,
            text="First correct",
            is_correct=True,
            order=1,
        )
        correct_two = AnswerChoice.objects.create(
            question=question,
            text="Second correct",
            is_correct=True,
            order=2,
        )
        wrong = AnswerChoice.objects.create(
            question=question,
            text="Wrong",
            is_correct=False,
            order=3,
        )
        attempt = QuizAttempt.objects.create(
            user=self.user,
            mode="topic",
            topic=self.topic,
            total_questions=1,
        )

        self.client.post(
            reverse("quizzes:submit_quiz", args=[attempt.pk]),
            {
                "question_ids": [str(question.pk)],
                f"q_{question.pk}": [
                    str(correct_one.pk),
                    str(correct_two.pk),
                ],
            },
        )

        attempt.refresh_from_db()
        answer = UserAnswer.objects.get(attempt=attempt, question=question)

        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.selected_choices.count(), 2)
        self.assertEqual(attempt.correct_count, 1)
        self.assertEqual(attempt.score, 100.0)

        second_attempt = QuizAttempt.objects.create(
            user=self.user,
            mode="topic",
            topic=self.topic,
            total_questions=1,
        )
        self.client.post(
            reverse("quizzes:submit_quiz", args=[second_attempt.pk]),
            {
                "question_ids": [str(question.pk)],
                f"q_{question.pk}": [
                    str(correct_one.pk),
                    str(wrong.pk),
                ],
            },
        )

        second_attempt.refresh_from_db()
        wrong_answer = UserAnswer.objects.get(attempt=second_attempt, question=question)

        self.assertFalse(wrong_answer.is_correct)
        self.assertEqual(second_attempt.correct_count, 0)
        self.assertEqual(second_attempt.score, 0.0)
