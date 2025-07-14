from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"videos", views.VideoViewSet)

urlpatterns = [
    path("<int:movie_id>/<str:resolution>/index.m3u8", views.hls_playlist, name="hls_playlist"),
    path("<int:movie_id>/<str:resolution>/<str:segment_name>/", views.hls_segment, name="hls_segment"),
]
