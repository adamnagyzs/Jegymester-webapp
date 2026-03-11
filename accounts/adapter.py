from allauth.account.adapter import DefaultAccountAdapter
from django.contrib import messages


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom allauth adapter to show success message on signup and ensure login."""

    def save_user(self, request, user, form, commit=True):
        """Save user and add a success message."""
        user = super().save_user(request, user, form, commit=commit)
        if request:
            messages.success(
                request,
                f'Sikeres regisztráció! Üdvözlünk, {user.username}! 🎬'
            )
        return user

    def get_login_redirect_url(self, request):
        """Redirect to home after login."""
        return '/'

    def get_signup_redirect_url(self, request):
        """Redirect to home after signup."""
        return '/'
