from django.urls import path
from . import views

app_name = "labs"

urlpatterns = [
    path("", views.ChallengeListView.as_view(), name="challenge_list"),
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge_detail"),
    path("<int:pk>/submit/", views.SubmitCodeView.as_view(), name="submit_code"),
    path("<int:pk>/hint/", views.GetHintView.as_view(), name="get_hint"),
]
