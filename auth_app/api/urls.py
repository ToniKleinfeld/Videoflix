from django.urls import path
from .views import RegistrationView, CookieTokenObtainPairView, CookieTokenRefreshView

urlpatterns = [
    path("registration/", RegistrationView.as_view(), name="register"),
    path("token/", CookieTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
]
