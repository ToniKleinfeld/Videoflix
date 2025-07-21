from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from core.utils.tasks import enqueue_after_commit

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)
    username = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_confirmed_password(self, value):
        password = self.initial_data.get("password")
        if password and value and password != value:
            raise serializers.ValidationError("Passwords do not match")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def generate_username(self, email):
        local_part, domain_part = email.split("@", 1)
        domain_clean = domain_part[::-1].replace(".", "_", 1)[::-1]

        username = f"{local_part}{domain_clean}"

        return username

    def save(self):
        pw = self.validated_data["password"]
        email = self.validated_data["email"]
        username = self.generate_username(email)

        account = User(username=username, email=email, is_active=False)
        account.set_password(pw)
        account.save()

        uid = urlsafe_base64_encode(force_bytes(account.pk))
        token = default_token_generator.make_token(account)

        from auth_app.tasks import send_activation_email

        enqueue_after_commit(send_activation_email, account.pk, uid, token)
        return account, token


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Change TokenObtainPairSerializer to login with Email
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No valid email or password.")

        if not user.check_password(password):
            raise serializers.ValidationError("No valid email or password.")

        data = super().validate({"username": user.username, "password": password})

        return data


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset requests."""

    email = serializers.EmailField()
