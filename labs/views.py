import ast
import io
import contextlib
import json
import multiprocessing
import resource

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView

from .forms import CodeSubmitForm
from .models import CodingChallenge, CodingAttempt
from progress.models import TopicProgress


# ── helpers ────────────────────────────────────────────────────────────────

_MAX_REVEAL_DEFAULT = 5  # fallback if challenge has 0


def _should_reveal_solution(challenge, user, just_solved=False):
    """Return True when the solution explanation should be shown.

    Conditions:
      1. The user just solved it (is_correct == True), OR
      2. The user has N+ *failed* attempts where N = max_attempts_before_reveal.
    """
    if just_solved:
        return True
    max_tries = challenge.max_attempts_before_reveal or _MAX_REVEAL_DEFAULT
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

        # Attempts remaining before auto-reveal
        max_tries = challenge.max_attempts_before_reveal or _MAX_REVEAL_DEFAULT
        ctx["attempts_until_reveal"] = max(0, max_tries - failed) if not reveal else 0

        # Hint gating: only allow hints proportional to failed attempts
        ctx["hints_available"] = min(3, (failed // 1) + (1 if failed > 0 else 0))

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
        actual_output = self._run_code(code, challenge.test_input)
        expected = challenge.expected_output.strip()

        # Separate error messages from normal output
        error_message = ""
        if actual_output.startswith("Error:"):
            error_message = actual_output
            is_correct = False
        else:
            is_correct = actual_output.strip() == expected

        # Count hints user has requested so far
        prev_hints = (
            CodingAttempt.objects.filter(
                user=request.user, challenge=challenge
            ).order_by("-submitted_at").first()
        )
        hints_used = prev_hints.hints_used if prev_hints else 0

        # ── Save attempt ─────────────────────────────────────────────
        attempt = CodingAttempt.objects.create(
            user=request.user,
            challenge=challenge,
            submitted_code=code,
            actual_output=actual_output if not error_message else "",
            error_message=error_message,
            is_correct=is_correct,
            hints_used=hints_used,
            time_taken_seconds=time_taken,
        )

        # ── Update progress ──────────────────────────────────────────
        if is_correct:
            from progress.services import record_lab_solved
            record_lab_solved(request.user, challenge)
        else:
            tp, _ = TopicProgress.objects.get_or_create(
                user=request.user, topic=challenge.topic
            )
            tp.record_answer(is_correct=False)

        # Update streak
        profile = getattr(request.user, "profile", None)
        if profile:
            profile.update_streak()

        # ── Solution reveal logic ────────────────────────────────────
        reveal = _should_reveal_solution(challenge, request.user, just_solved=is_correct)
        _, failed, _ = _attempt_stats(challenge, request.user)
        max_tries = challenge.max_attempts_before_reveal or _MAX_REVEAL_DEFAULT

        response_data = {
            "is_correct": is_correct,
            "actual_output": actual_output,
            "error_message": error_message,
            "expected_output": expected if not is_correct else None,
            "attempt_id": attempt.id,
            "attempt_number": CodingAttempt.objects.filter(
                user=request.user, challenge=challenge
            ).count(),
        }

        if reveal and challenge.solution_explanation:
            response_data["solution_explanation"] = challenge.solution_explanation
        if reveal and challenge.solution_code:
            response_data["solution_code"] = challenge.solution_code

        if not is_correct and not reveal:
            response_data["attempts_until_reveal"] = max(0, max_tries - failed)

        return JsonResponse(response_data)

    # ── Code evaluation helpers ──────────────────────────────────────

    @staticmethod
    def _validate_code(code: str) -> str | None:
        """AST-based validation: reject dangerous attribute access patterns."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return None  # Let exec surface the SyntaxError with a message

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                return f"Forbidden: access to '{node.attr}' is not allowed"
            if isinstance(node, ast.Name) and node.id.startswith("__"):
                return f"Forbidden: use of '{node.id}' is not allowed"
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return "Forbidden: imports are not allowed"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in (
                    "exec", "eval", "compile", "__import__",
                    "globals", "locals", "vars", "dir",
                    "getattr", "setattr", "delattr", "open",
                ):
                    return f"Forbidden: '{node.func.id}()' is not allowed"
        return None

    @staticmethod
    def _execute_in_subprocess(code: str, test_input: str, result_dict):
        """Run user code in a child process with resource limits."""
        resource.setrlimit(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))

        input_lines = test_input.strip().split("\n") if test_input.strip() else []
        input_iter = iter(input_lines)

        def fake_input(prompt=""):
            try:
                return next(input_iter)
            except StopIteration:
                return ""

        safe_builtins = {
            "print": print,
            "input": fake_input,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "tuple": tuple,
            "dict": dict,
            "set": set,
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "round": round,
            "sorted": sorted,
            "reversed": reversed,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "isinstance": isinstance,
            "True": True,
            "False": False,
            "None": None,
        }

        stdout_capture = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(code, {"__builtins__": safe_builtins})  # noqa: S102
        except Exception as exc:
            result_dict["output"] = f"Error: {type(exc).__name__}: {exc}"
            return

        result_dict["output"] = stdout_capture.getvalue()

    @staticmethod
    def _run_code(code: str, test_input: str) -> str:
        """Execute user code in a sandboxed subprocess with AST validation,
        resource limits, and a hard timeout."""
        error = SubmitCodeView._validate_code(code)
        if error:
            return f"Error: {error}"

        manager = multiprocessing.Manager()
        result_dict = manager.dict()
        result_dict["output"] = ""

        proc = multiprocessing.Process(
            target=SubmitCodeView._execute_in_subprocess,
            args=(code, test_input, result_dict),
        )
        proc.start()
        proc.join(timeout=10)

        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=2)
            if proc.is_alive():
                proc.kill()
            return "Error: Code execution timed out (max 10 seconds)"

        if proc.exitcode != 0 and not result_dict.get("output"):
            return "Error: Code execution failed (possible memory limit exceeded)"

        return result_dict.get("output", "")


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
