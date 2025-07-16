import os

from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import cache_control
from django.db.models import Q

from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from content.models import Video, VideoQuality
from content.api.serializers import VideoListSerializer


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
@cache_control(max_age=300)
def hls_playlist(request, movie_id, resolution):
    """
    Endpoint: /api/video/<int:movie_id>/<str:resolution>/index.m3u8
    Returns HLS playlist for a specific movie and resolution.
    """
    video = get_object_or_404(Video, id=movie_id)
    quality = get_object_or_404(VideoQuality, video=video, resolution=resolution)

    if quality.processing_status != "completed":
        return Response({"error": "Video not yet available"}, status=404)

    playlist_path = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution, "index.m3u8")

    if not os.path.exists(playlist_path):
        raise Http404("Playlist not found")

    try:
        with open(playlist_path, "r", encoding="utf-8") as f:
            playlist_content = f.read()

        lines = playlist_content.split("\n")
        modified_lines = []

        for line in lines:
            if line.endswith(".ts"):
                segment_name = line.strip()
                api_url = f"/api/video/{movie_id}/{resolution}/{segment_name}"
                modified_lines.append(api_url)
            else:
                modified_lines.append(line)

        modified_playlist = "\n".join(modified_lines)

        response = HttpResponse(modified_playlist, content_type="application/vnd.apple.mpegurl")

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET"
        response["Access-Control-Allow-Headers"] = "Content-Type"

        return response

    except IOError:
        return Response({"error": "Error reading playlist"}, status=500)


@api_view(["GET"])
# @permission_classes([IsAuthenticated])
@cache_control(max_age=3600)
def hls_segment(request, movie_id, resolution, segment_name):
    """
    Endpoint: /api/video/<int:movie_id>/<str:resolution>/<str:segment_name>/
    Returns a single HLS video segment.
    """
    video = get_object_or_404(Video, id=movie_id)
    quality = get_object_or_404(VideoQuality, video=video, resolution=resolution)

    if quality.processing_status != "completed":
        raise Http404("Video not yet available")

    if not segment_name.endswith(".ts"):
        raise Http404("Invalid segment name")

    if ".." in segment_name or "/" in segment_name or "\\" in segment_name:
        raise Http404("Invalid segment name")

    segment_path = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution, segment_name)

    if not os.path.exists(segment_path):
        raise Http404("Segment not found")

    expected_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution)
    if not os.path.commonpath([segment_path, expected_dir]) == expected_dir:
        raise Http404("Invalid path")

    try:
        response = FileResponse(open(segment_path, "rb"), content_type="video/mp2t")

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        response["Accept-Ranges"] = "bytes"

        return response

    except IOError:
        raise Http404("Error reading segment")


class VideoListView(generics.ListAPIView):
    """
    Returns list of all videos with basic information
    """

    serializer_class = VideoListSerializer
    # permission_classes = [permissions.IsAuthenticated]
