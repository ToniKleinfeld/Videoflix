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
    try:
        user = User.objects.get(pk=user_id)
        activation_link = f"{env('FRONTEND_URL', default='http://localhost:8000')}/api/activate/{uid}/{token}/"

        subject = "Activate your account"
        message = f"Hi {user.email},\n\nPlease activate your account using the link below:\n{activation_link}"

        send_mail(subject, message, env("DEFAULT_FROM_EMAIL"), [user.email], fail_silently=False)

        logger.info(f"Activation email sent to {user.email}")
    except Exception as e:
        print(f"Error sending activation email: {e}")
        raise
