from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as AuthLoginView, LogoutView as AuthLogoutView
from django.core.mail import send_mail
from django.db import models
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, FormView, ListView, TemplateView

from .forms import InviteForm, RegisterForm
from .models import Invitation, UserProfile

User = get_user_model()


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("progress:dashboard")

    def _get_invitation(self, token_str: str):
        if not token_str:
            return None
        try:
            return Invitation.objects.get(
                token=token_str, is_active=True, accepted_at__isnull=True
            )
        except (Invitation.DoesNotExist, ValueError):
            return None

    def _token_str(self) -> str:
        if self.request.method == "POST":
            return self.request.POST.get("token", "")
        return self.request.GET.get("token", "")

    def get(self, request, *args, **kwargs):
        if not self._get_invitation(self._token_str()):
            return render(request, "accounts/register_closed.html", status=403)
        return super().get(request, *args, **kwargs)

    def get_initial(self):
        token_str = self._token_str()
        invitation = self._get_invitation(token_str)
        if invitation:
            return {"email": invitation.email, "token": str(invitation.token)}
        return {}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self._get_invitation(self._token_str()):
            form.fields["email"].widget.attrs["readonly"] = True
        return form

    def form_valid(self, form):
        token_str = str(form.cleaned_data.get("token") or "")
        invitation = self._get_invitation(token_str)
        if invitation is None:
            form.add_error(None, "This invitation link is no longer valid.")
            return self.form_invalid(form)
        if form.cleaned_data["email"].strip().lower() != invitation.email.strip().lower():
            form.add_error("email", "Email must match the address this invitation was sent to.")
            return self.form_invalid(form)
        response = super().form_valid(form)
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        UserProfile.objects.get_or_create(user=self.object)
        login(self.request, self.object)
        return response


class LoginView(AuthLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(AuthLogoutView):
    next_page = reverse_lazy("core:home")


User = get_user_model()


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Staff-only view: all registered users with sign-up and last-login info."""

    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return (
            User.objects.select_related("profile")
            .order_by("-date_joined")
        )


class InviteCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Staff-only: create and email an invitation link."""

    template_name = "accounts/invite_create.html"
    form_class = InviteForm
    success_url = reverse_lazy("accounts:invite_list")

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        import uuid as _uuid

        email = form.cleaned_data["email"].strip().lower()
        existing = Invitation.objects.filter(email__iexact=email).first()
        previous_invite_state = None

        if existing and existing.is_used:
            messages.error(
                self.request,
                f"{email} has already accepted an invitation and registered.",
            )
            return self.form_invalid(form)

        if existing:
            previous_invite_state = {
                "token": existing.token,
                "is_active": existing.is_active,
                "invited_by_id": existing.invited_by_id,
            }
            # Refresh token so old link is invalidated, then resend
            existing.token = _uuid.uuid4()
            existing.is_active = True
            existing.invited_by = self.request.user
            existing.save(update_fields=["token", "is_active", "invited_by"])
            invitation = existing
        else:
            invitation = Invitation.objects.create(
                email=email,
                invited_by=self.request.user,
            )

        register_url = self.request.build_absolute_uri(
            reverse("accounts:register") + f"?token={invitation.token}"
        )
        try:
            send_mail(
                subject="You're invited to PCEP Prep Coach",
                message=render_to_string(
                    "accounts/email/invite.txt",
                    {
                        "invited_by": (
                            self.request.user.get_full_name()
                            or self.request.user.username
                        ),
                        "register_url": register_url,
                    },
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            # Keep invitation state consistent when SMTP config/provider fails.
            if previous_invite_state is not None:
                invitation.token = previous_invite_state["token"]
                invitation.is_active = previous_invite_state["is_active"]
                invitation.invited_by_id = previous_invite_state["invited_by_id"]
                invitation.save(update_fields=["token", "is_active", "invited_by"])
            else:
                invitation.delete()

            error_msg = (
                "Invite email could not be sent. Check email settings "
                "(EMAIL_HOST_USER / EMAIL_HOST_PASSWORD) and try again."
            )
            messages.error(self.request, error_msg)
            form.add_error(None, error_msg)
            return self.form_invalid(form)

        messages.success(self.request, f"Invitation sent to {email}.")
        return super().form_valid(form)


class InviteListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Staff-only: view all sent invitations."""

    template_name = "accounts/invite_list.html"
    context_object_name = "invitations"
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return Invitation.objects.select_related("invited_by").order_by("-created_at")


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
