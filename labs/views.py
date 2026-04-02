import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView
from django_ratelimit.decorators import ratelimit

from .forms import CodeSubmitForm
from .models import CodingChallenge, CodingAttempt
from .sandbox import run_user_code
from progress.models import TopicProgress


def _should_reveal_solution(challenge, user, just_solved=False):
    """Return True when the solution explanation should be shown.

    Conditions:
      1. The user just solved it (is_correct == True), OR
      2. The user has N+ *failed* attempts, where N = max_attempts_before_reveal.
         If max_attempts_before_reveal == 0 the solution is never auto-revealed.
    """
    if just_solved:
        return True
    max_tries = challenge.max_attempts_before_reveal
    if max_tries == 0:
        return False  # 0 means "never auto-reveal"
    failed = CodingAttempt.objects.filter(
        user=user, challenge=challenge, is_correct=False,
    ).count()
    return failed >= max_tries


def _attempt_stats(challenge, user):
    """Return (total_attempts, failed_attempts, has_solved) for a user."""
    qs = CodingAttempt.objects.filter(user=user, challenge=challenge)
    total = qs.count()
    solved = qs.filter(is_correct=True).exists()
    failed = qs.filter(is_correct=False).count()
    return total, failed, solved


# ── List view ──────────────────────────────────────────────────────────────

class ChallengeListView(LoginRequiredMixin, ListView):
    model = CodingChallenge
    template_name = "labs/challenge_list.html"
    context_object_name = "challenges"

    def get_queryset(self):
        return (
            CodingChallenge.objects.filter(is_active=True)
            .select_related("topic", "domain")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        completed_ids = set(
            CodingAttempt.objects.filter(user=user, is_correct=True)
            .values_list("challenge_id", flat=True)
        )
        attempted_ids = set(
            CodingAttempt.objects.filter(user=user)
            .values_list("challenge_id", flat=True)
        )
        ctx["completed_ids"] = completed_ids
        ctx["attempted_ids"] = attempted_ids
        return ctx


# ── Detail view ────────────────────────────────────────────────────────────

class ChallengeDetailView(LoginRequiredMixin, DetailView):
    model = CodingChallenge
    template_name = "labs/challenge_detail.html"
    context_object_name = "challenge"

    def get_queryset(self):
        return CodingChallenge.objects.filter(is_active=True).select_related("topic", "domain")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        challenge = self.object

        # Attempt stats
        total, failed, has_solved = _attempt_stats(challenge, user)
        ctx["total_attempts"] = total
        ctx["failed_attempts"] = failed
        ctx["has_solved"] = has_solved

        # Past attempts (most recent first)
        ctx["past_attempts"] = (
            CodingAttempt.objects.filter(user=user, challenge=challenge)
            .order_by("-submitted_at")[:10]
        )

        # Solution reveal logic
        reveal = _should_reveal_solution(challenge, user, just_solved=has_solved)
        ctx["show_solution"] = reveal and bool(challenge.solution_explanation)
        ctx["show_solution_code"] = reveal and bool(challenge.solution_code)

        # Attempts remaining before auto-reveal (0 = never auto-reveal)
        max_tries = challenge.max_attempts_before_reveal
        ctx["attempts_until_reveal"] = max(0, max_tries - failed) if (not reveal and max_tries) else 0

        # Unlock one hint per failed attempt, up to 3 total
        ctx["hints_available"] = min(3, failed)

        # Prepopulate form with starter code (or last attempt's code)
        last_attempt = (
            CodingAttempt.objects.filter(user=user, challenge=challenge)
            .order_by("-submitted_at")
            .first()
        )
        initial_code = last_attempt.submitted_code if last_attempt else challenge.starter_code
        ctx["form"] = CodeSubmitForm(initial={"code": initial_code})

        # Expected output preview (show the first line for easy challenges)
        if challenge.difficulty == "easy" and challenge.expected_output:
            lines = challenge.expected_output.strip().splitlines()
            ctx["expected_preview"] = lines[0] + ("…" if len(lines) > 1 else "")
        else:
            ctx["expected_preview"] = None

        return ctx


# ── Code submission ────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key="user", rate="10/m", method="POST", block=True),
    name="post",
)
class SubmitCodeView(LoginRequiredMixin, View):
    """Evaluate submitted code and return results as JSON.

    MVP evaluation strategy
    -----------------------
    1. **AST validation** — reject imports, dunder access, dangerous builtins.
    2. **Subprocess execution** — run in a forked process with CPU + memory
       limits so infinite loops and memory bombs can't harm the server.
    3. **Output comparison** — strip + compare stdout against the challenge's
       ``expected_output``.  Instructor defines the expected answer at
       challenge-authoring time.

    Future upgrade path
    -------------------
    Replace ``_run_code`` with one of:
      • Docker container per submission (firejail / nsjail)
      • External sandboxed API (e.g. Piston, Judge0)
      • Celery task → isolated worker with seccomp
    """

    def post(self, request, pk):
        challenge = get_object_or_404(CodingChallenge, pk=pk, is_active=True)

        # Parse JSON body (AJAX) or fall back to form POST
        try:
            body = json.loads(request.body)
            code = body.get("code", "")
            time_taken = body.get("time_taken")
        except (json.JSONDecodeError, AttributeError):
            code = request.POST.get("code", "")
            time_taken = request.POST.get("time_taken")

        # Server-side validation via form
        form = CodeSubmitForm(data={"code": code, "time_taken": time_taken})
        if not form.is_valid():
            return JsonResponse(
                {"error": "; ".join(e for errs in form.errors.values() for e in errs)},
                status=400,
            )

        code = form.cleaned_data["code"]
        time_taken = form.cleaned_data.get("time_taken")

        # ── Run code evaluator ───────────────────────────────────────
        actual_output = run_user_code(code, challenge.test_input)
        is_correct, error_message = self._evaluate_output(
            actual_output, challenge.expected_output.strip()
        )

        attempt = self._save_attempt(
            request.user, challenge, code, actual_output,
            error_message, is_correct, time_taken,
        )
        self._update_progress(request.user, challenge, is_correct)

        return JsonResponse(
            self._build_response(request.user, challenge, attempt, is_correct,
                                 actual_output, error_message)
        )

    # ── Post helpers ─────────────────────────────────────────────────

    @staticmethod
    def _evaluate_output(actual_output, expected):
        """Return (is_correct, error_message) from sandbox output."""
        if actual_output.startswith("Error:"):
            return False, actual_output
        return actual_output.strip() == expected, ""

    @staticmethod
    def _save_attempt(user, challenge, code, actual_output,
                      error_message, is_correct, time_taken):
        prev = (
            CodingAttempt.objects.filter(user=user, challenge=challenge)
            .order_by("-submitted_at").first()
        )
        return CodingAttempt.objects.create(
            user=user,
            challenge=challenge,
            submitted_code=code,
            actual_output=actual_output if not error_message else "",
            error_message=error_message,
            is_correct=is_correct,
            hints_used=prev.hints_used if prev else 0,
            time_taken_seconds=time_taken,
        )

    @staticmethod
    def _update_progress(user, challenge, is_correct):
        from progress.services import invalidate_user_progress_cache, record_lab_solved
        if is_correct:
            record_lab_solved(user, challenge)
        else:
            tp, _ = TopicProgress.objects.get_or_create(
                user=user, topic=challenge.topic,
            )
            tp.record_answer(is_correct=False)
        invalidate_user_progress_cache(user)
        profile = getattr(user, "profile", None)
        if profile:
            profile.update_streak()

    @staticmethod
    def _build_response(user, challenge, attempt, is_correct,
                        actual_output, error_message):
        expected = challenge.expected_output.strip()
        reveal = _should_reveal_solution(challenge, user, just_solved=is_correct)
        _, failed, _ = _attempt_stats(challenge, user)
        max_tries = challenge.max_attempts_before_reveal

        data = {
            "is_correct": is_correct,
            "actual_output": actual_output,
            "error_message": error_message,
            "expected_output": expected if not is_correct else None,
            "attempt_id": attempt.id,
            "attempt_number": CodingAttempt.objects.filter(
                user=user, challenge=challenge,
            ).count(),
        }
        if reveal and challenge.solution_explanation:
            data["solution_explanation"] = challenge.solution_explanation
        if reveal and challenge.solution_code:
            data["solution_code"] = challenge.solution_code
        if not is_correct and not reveal and max_tries:
            data["attempts_until_reveal"] = max(0, max_tries - failed)
        return data



# ── Hint API ───────────────────────────────────────────────────────────────

class GetHintView(LoginRequiredMixin, View):
    """Return the next hint for a challenge and record that it was used."""

    def post(self, request, pk):
        challenge = get_object_or_404(CodingChallenge, pk=pk)
        try:
            body = json.loads(request.body)
            hint_num = body.get("hint_number", 1)
        except (json.JSONDecodeError, AttributeError):
            hint_num = int(request.POST.get("hint_number", 1))

        hints = [challenge.hint_1, challenge.hint_2, challenge.hint_3]
        hint_num = max(1, min(hint_num, 3))
        hint_text = hints[hint_num - 1] or "No more hints available."

        # Track that user used this many hints on their *latest* attempt
        latest = (
            CodingAttempt.objects.filter(user=request.user, challenge=challenge)
            .order_by("-submitted_at")
            .first()
        )
        if latest and hint_num > latest.hints_used:
            latest.hints_used = hint_num
            latest.save(update_fields=["hints_used"])

        return JsonResponse({"hint": hint_text, "hint_number": hint_num})
