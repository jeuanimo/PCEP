"""Tests for labs.sandbox — the two-layer code execution sandbox."""
from django.test import TestCase

from .sandbox import validate, run_user_code


class ValidateTests(TestCase):
    """Layer-1 AST validation."""

    # ── should pass ──────────────────────────────────────────────────

    def test_safe_code_passes(self):
        self.assertIsNone(validate("x = 1 + 2\nprint(x)"))

    def test_empty_string_passes(self):
        self.assertIsNone(validate(""))

    def test_syntax_error_passes_validation(self):
        # SyntaxErrors are reported by the subprocess, not the validator
        self.assertIsNone(validate("def foo(:"))

    # ── imports ──────────────────────────────────────────────────────

    def test_import_blocked(self):
        self.assertIsNotNone(validate("import os"))

    def test_from_import_blocked(self):
        self.assertIsNotNone(validate("from sys import argv"))

    # ── dunders ──────────────────────────────────────────────────────

    def test_dunder_attribute_blocked(self):
        self.assertIsNotNone(validate("x = ().__class__"))

    def test_dunder_name_blocked(self):
        self.assertIsNotNone(validate("x = __builtins__"))

    # ── forbidden builtins ───────────────────────────────────────────

    def test_exec_blocked(self):
        self.assertIsNotNone(validate("exec('print(1)')"))

    def test_eval_blocked(self):
        self.assertIsNotNone(validate("eval('1+1')"))

    def test_open_blocked(self):
        self.assertIsNotNone(validate("open('/etc/passwd')"))

    def test_type_blocked(self):
        self.assertIsNotNone(validate("type(x)"))

    def test_object_blocked(self):
        self.assertIsNotNone(validate("object.__subclasses__()"))

    # ── attribute method calls ───────────────────────────────────────

    def test_attribute_call_allowed_for_normal_python(self):
        self.assertIsNone(validate("nums=[1, 2]\nnums.append(3)\nprint(nums)"))

    def test_import_plus_attribute_call_blocked(self):
        # Imports are blocked, which also prevents module method abuse.
        self.assertIsNotNone(validate("import os\nos.system('ls')"))

    def test_chr_blocked(self):
        self.assertIsNotNone(validate("chr(65)"))


class RunUserCodeTests(TestCase):
    """Integration tests — full sandbox round-trip."""

    def test_hello_world(self):
        out = run_user_code('print("hello")', "")
        self.assertEqual(out.strip(), "hello")

    def test_uses_test_input(self):
        code = "name = input()\nprint('Hi', name)"
        out = run_user_code(code, "Alice")
        self.assertEqual(out.strip(), "Hi Alice")

    def test_forbidden_code_returns_error(self):
        out = run_user_code("import os", "")
        self.assertTrue(out.startswith("Error:"))

    def test_syntax_error_returns_error(self):
        out = run_user_code("def foo(:", "")
        self.assertTrue(out.startswith("Error:"))

    def test_runtime_exception_returns_error(self):
        out = run_user_code("1/0", "")
        self.assertTrue(out.startswith("Error:"))
        self.assertIn("ZeroDivisionError", out)

    def test_infinite_loop_times_out(self):
        # Use a very short timeout so the test suite doesn't hang
        out = run_user_code("while True: pass", "", timeout=2)
        self.assertTrue(out.startswith("Error:"))
        self.assertIn("timed out", out)

    def test_multiline_output(self):
        code = "for i in range(3):\n    print(i)"
        out = run_user_code(code, "")
        self.assertEqual(out.strip(), "0\n1\n2")

    def test_empty_output(self):
        out = run_user_code("x = 42", "")
        self.assertEqual(out, "")

    def test_list_append_allowed(self):
        code = "nums=[1, 2]\nnums.append(3)\nprint(nums)"
        out = run_user_code(code, "")
        self.assertEqual(out.strip(), "[1, 2, 3]")
