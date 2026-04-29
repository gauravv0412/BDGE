"""Small auth forms built on Django's default user model."""

from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from app.accounts.services import create_password_user


class WisdomizeSignupForm(UserCreationForm):
    """Email-based signup while keeping Django's built-in User model."""

    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Arjuna Sharma"}),
    )
    email = forms.EmailField(
        label="Email address",
        max_length=150,
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "password1", "password2")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit: bool = True) -> User:
        if not commit:
            raise ValueError("WisdomizeSignupForm requires commit=True.")
        return create_password_user(
            full_name=self.cleaned_data["full_name"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
        )


class WisdomizeLoginForm(AuthenticationForm):
    """Login form with labels that match the public site tone."""

    username = forms.CharField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "you@example.com"}),
    )


class AccountSettingsForm(forms.Form):
    """Editable account fields (name only in this step)."""

    full_name = forms.CharField(
        label="Full name",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )

