from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import RegisterForm
from .models import UserProfile


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("progress:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create profile and auto-login
        UserProfile.objects.get_or_create(user=self.object)
        login(self.request, self.object)
        return response


class LoginView(AuthLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(AuthLogoutView):
    next_page = reverse_lazy("core:home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        ctx["profile"] = profile

        # Gather domain progress for profile page
        from progress.models import TopicProgress
        from learning.models import Domain
        domains = Domain.objects.all()
        domain_progress = []
        for d in domains:
            topics = d.topics.all()
            if topics.exists():
                avg = (
                    TopicProgress.objects.filter(
                        user=self.request.user, topic__in=topics
                    ).aggregate(models.Avg("confidence"))["confidence__avg"]
                    or 0
                )
            else:
                avg = 0
            domain_progress.append({"domain": d, "mastery": round(avg)})
        ctx["domain_progress"] = domain_progress

        from quizzes.models import QuizAttempt
        from labs.models import CodingAttempt, CodingChallenge
        attempts = QuizAttempt.objects.filter(
            user=self.request.user, finished_at__isnull=False
        )
        ctx["total_quizzes"] = attempts.count()
        ctx["passed_quizzes"] = attempts.filter(is_passed=True).count()
        ctx["recent_quizzes"] = (
            attempts.select_related("topic", "domain").order_by("-started_at")[:5]
        )
        total_labs = CodingChallenge.objects.filter(is_active=True).count()
        completed_labs = (
            CodingAttempt.objects.filter(user=self.request.user, is_correct=True)
            .values("challenge").distinct().count()
        )
        ctx["total_labs"] = total_labs
        ctx["completed_labs"] = completed_labs
        return ctx
