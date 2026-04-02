from django.urls import path

from . import views

app_name = "quizzes"

urlpatterns = [
    # ── Hub ────────────────────────────────────────────────────────────
    path("",                          views.QuizHubView.as_view(),       name="quiz_hub"),

    # ── Start a quiz ───────────────────────────────────────────────────
    path("topic/<int:topic_pk>/",     views.TopicQuizView.as_view(),     name="topic_quiz"),
    path("domain/<int:domain_pk>/",   views.DomainQuizView.as_view(),    name="domain_quiz"),
    path("mixed/",                    views.MixedQuizView.as_view(),     name="mixed_quiz"),
    path("exam/",                     views.ExamModeView.as_view(),      name="exam_mode"),

    # ── Submit & results ───────────────────────────────────────────────
    path("submit/<int:attempt_pk>/",  views.SubmitQuizView.as_view(),    name="submit_quiz"),
    path("results/<int:pk>/",         views.QuizResultsView.as_view(),   name="quiz_results"),

    # ── Review ─────────────────────────────────────────────────────────
    path("review/",                   views.ReviewMistakesView.as_view(),name="review_mistakes"),
    path("review/practice/",          views.ReviewQuizView.as_view(),    name="review_quiz"),
]
