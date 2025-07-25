from django_rq import job
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from core.settings import env

import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@job("default", timeout=300)
def send_activation_email(user_id, uid, token):
    """
    Send an activation email to the user after registration.
    """
    try:
        user = User.objects.get(pk=user_id)
        activation_link = (
            f"{env('FRONTEND_URL', default='http://localhost:8000')}/pages/auth/activate.html?uid={uid}&token={token}"
        )

        subject = "Activate your account"
        message = (
            f"Hi {user.email},\n\n"
            f"Please activate your account using the link below:\n{activation_link}\n\n"
            "If you did not create an account, please ignore this email.\n"
        )

        send_mail(
            subject,
            message,
            env("DEFAULT_FROM_EMAIL", default="noreply@videoflix.local"),
            [user.email],
            fail_silently=False,
        )

        logger.info(f"Activation email sent to {user.email}")
    except Exception as e:
        print(f"Error sending activation email: {e}")
        raise


@job("default", timeout=300)
def send_password_reset_email(email, reset_url):
    """
    Send a password reset email to the user.
    """
    try:
        subject = "Password Reset Request"
        message = (
            "You requested a password reset for your Videoflix account.\n\n"
            f"Please click the link below to reset your password:\n{reset_url}\n\n"
            "If you did not request this, just ignore this email.\n"
        )
        send_mail(
            subject, message, env("DEFAULT_FROM_EMAIL", default="noreply@videoflix.local"), [email], fail_silently=False
        )

        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        print(f"Error sending activation email: {e}")
        raise
