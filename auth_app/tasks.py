from django_rq import job
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse
from core.settings import env

User = get_user_model()


@job("default", timeout=300)
def send_activation_email(user_id, uid, token):
    try:
        user = User.objects.get(pk=user_id)
        activation_link = f"{env('FRONTEND_URL', default='http://localhost:4200')}/activate/{uid}/{token}/"

        subject = "Activate your account"
        message = f"Hi {user.username},\n\nPlease activate your account using the link below:\n{activation_link}"

        send_mail(
            subject, message, env("DEFAULT_FROM_EMAIL", default="EMAIL_HOST_USER"), [user.email], fail_silently=False
        )
    except Exception as e:
        print(f"Error sending activation email: {e}")
        raise
