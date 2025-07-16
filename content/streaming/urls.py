from django.urls import path
from .views import hls_playlist, hls_segment

app_name = "content-hls"

urlpatterns = [
    path("<int:movie_id>/<str:resolution>/index.m3u8", hls_playlist, name="hls_playlist"),
    path("<int:movie_id>/<str:resolution>/<str:segment_name>/", hls_segment, name="hls_segment"),
]
