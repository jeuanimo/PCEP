"""Root URL configuration for PCEP Prep Coach."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def healthz(_request):
    """Simple health check endpoint for uptime monitors."""
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("learn/", include("learning.urls")),
    path("quiz/", include("quizzes.urls")),
    path("labs/", include("labs.urls")),
    path("progress/", include("progress.urls")),
]
