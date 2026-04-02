from django.urls import path
from . import views

app_name = "learning"

urlpatterns = [
    path("",                                views.DomainListView.as_view(),     name="domain_list"),
    path("domain/<slug:slug>/",             views.DomainDetailView.as_view(),   name="domain_detail"),
    path("topic/<int:pk>/",                 views.TopicDetailView.as_view(),    name="topic_detail"),
    path("lesson/<int:pk>/",               views.LessonDetailView.as_view(),   name="lesson_detail"),

    # Flashcard routes
    path("flashcards/",                     views.FlashcardBrowseView.as_view(), name="flashcard_browse"),
    path("flashcards/rate/",                views.FlashcardRateView.as_view(),   name="flashcard_rate"),
    path("flashcards/<int:topic_pk>/",      views.FlashcardView.as_view(),       name="flashcards"),
]
