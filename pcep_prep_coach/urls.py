"""Root URL configuration for PCEP Prep Coach."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # App routes
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("learn/", include("learning.urls")),
    path("quiz/", include("quizzes.urls")),
    path("labs/", include("labs.urls")),
    path("progress/", include("progress.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
