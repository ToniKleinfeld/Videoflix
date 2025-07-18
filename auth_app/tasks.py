from django_rq import job
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.urls import reverse

User = get_user_model()


@job("default", timeout=300)
def send_activation_email(user_id, uid, token):
    user = User.objects.get(pk=user_id)
    activation_link = f"http://your-domain.com/api/activate/{uid}/{token}/"

    subject = "Activate your account"
    message = f"Hi {user.username},\n\nPlease activate your account using the link below:\n{activation_link}"

    send_mail(subject, message, "noreply@yourdomain.com", [user.email])
