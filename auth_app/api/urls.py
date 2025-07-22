from django.urls import path
from auth_app.api.views import (
    RegistrationView,
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    ActivateUserView,
    CookieTokenLogoutView,
    PasswordResetView,
    PasswordConfirmView,
)

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", CookieTokenLogoutView.as_view(), name="cookie_logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("activate/<uidb64>/<token>/", ActivateUserView.as_view(), name="activate"),
    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password_confirm/<uidb64>/<token>/", PasswordConfirmView.as_view(), name="password_confirm"),
]
