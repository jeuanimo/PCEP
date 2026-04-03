from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    token = forms.UUIDField(widget=forms.HiddenInput(), required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class InviteForm(forms.Form):
    email = forms.EmailField(
        label="Recipient email address",
        widget=forms.EmailInput(attrs={"placeholder": "user@example.com"}),
    )
