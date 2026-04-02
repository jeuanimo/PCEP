"""Root URL configuration for PCEP Prep Coach."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("learn/", include("learning.urls")),
    path("quiz/", include("quizzes.urls")),
    path("labs/", include("labs.urls")),
    path("progress/", include("progress.urls")),
]
