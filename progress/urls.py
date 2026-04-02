from django.urls import path
from . import views

app_name = "progress"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("topic/<int:pk>/", views.TopicProgressView.as_view(), name="topic_progress"),
    path("api/recommendation/", views.RecommendationAPIView.as_view(), name="recommendation_api"),
    path("api/readiness/", views.ReadinessAPIView.as_view(), name="readiness_api"),
]
