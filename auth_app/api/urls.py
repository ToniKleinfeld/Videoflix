from django.urls import path
from auth_app.api.views import RegistrationView, CookieTokenObtainPairView, CookieTokenRefreshView, ActivateUserView

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path("login/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("activate/<uidb64>/<token>/", ActivateUserView.as_view(), name="activate"),
]
