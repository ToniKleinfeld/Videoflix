from django.urls import path
from .views import VideoListView

app_name = "content-api"

urlpatterns = [
    path("", VideoListView.as_view(), name="video-list"),
]
