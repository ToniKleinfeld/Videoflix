from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from auth_app.api.serializers import (
    RegistrationSerializer,
    CustomTokenObtainPairSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer,
)
from auth_app.tasks import send_password_reset_email

from core.settings import env
from core.utils.tasks import enqueue_after_commit
import django_rq

User = get_user_model()


class RegistrationView(APIView):
    """
    View to handle user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account, token = serializer.save()
            data = {"user": {"id": saved_account.pk, "email": saved_account.email}, "token": token}
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Get HTTPOnly Cookie with Email login
    """

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]

        response = Response({"message": "Login successful"})

        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,
            samesite="lax",
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="lax",
        )

        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    View to refresh the access token using the refresh token stored in cookies.
    """

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response({"detail": "Refresh token not found!"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Refresh token not Valid!"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed", " access": access_token})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
        )

        return response


class ActivateUserView(APIView):
    """
    View to activate user account via email link.
    """

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid activation link"}, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenLogoutView(APIView):
    """
    Logout view to delete HttpOnly access & refresh token cookies
    """

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = request.COOKIES.get("access_token")

        if not refresh_token or not access_token:
            return Response(
                {"detail": "No token cookies found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass

        response = Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK,
        )

        response.delete_cookie("access_token", samesite="lax")
        response.delete_cookie("refresh_token", samesite="lax")

        return response


class PasswordResetView(APIView):
    """
    View to handle password reset requests.
    """

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = f"{env("FRONTEND_URL", default="http://127.0.0.1:5500")}/pages/auth/confirm_password.html?uid={uid}&token={token}"

        enqueue_after_commit(send_password_reset_email, user.email, reset_url)

        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)


class PasswordConfirmView(APIView):
    """
    View to handle password confirm post.
    """

    def post(self, request, uidb64, token):
        serializer = PasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"detail": "Invalid link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
