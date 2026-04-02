"""Forms for the labs (coding challenge) app."""
from django import forms


class CodeSubmitForm(forms.Form):
    """Validates code submitted from the challenge editor.

    Used both for the synchronous POST fallback and as server-side
    validation before the AJAX path runs the code evaluator.
    """

    code = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(attrs={
            "id": "code-editor",
            "class": "code-editor w-100",
            "rows": 14,
            "spellcheck": "false",
            "autocomplete": "off",
            "placeholder": "# Write your Python code here…",
        }),
        error_messages={"max_length": "Code too long (5 000 character limit)."},
    )
    time_taken = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.HiddenInput(attrs={"id": "time-taken-field"}),
    )
