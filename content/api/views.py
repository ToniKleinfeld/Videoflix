import os
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from content.models import Video, VideoQuality


@api_view(["GET"])
def hls_playlist(request, movie_id, resolution):
    """
    Endpunkt: /api/video/<int:movie_id>/<str:resolution>/index.m3u8
    Gibt die HLS-Playlist für einen bestimmten Film und Auflösung zurück.
    """
    video = get_object_or_404(Video, id=movie_id)
    quality = get_object_or_404(VideoQuality, video=video, resolution=resolution)

    if quality.processing_status != "completed":
        return Response({"error": "Video noch nicht verfügbar"}, status=404)

    playlist_path = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution, "index.m3u8")

    if not os.path.exists(playlist_path):
        raise Http404("Playlist nicht gefunden")

    # Lese die Playlist-Datei und passe die Segment-URLs an
    with open(playlist_path, "r") as f:
        playlist_content = f.read()

    # Ersetze relative Segment-Pfade durch absolute API-URLs
    lines = playlist_content.split("\n")
    modified_lines = []

    for line in lines:
        if line.endswith(".ts"):
            # Ersetze segment_xxx.ts durch API-URL
            segment_name = line.strip()
            api_url = f"/api/video/{movie_id}/{resolution}/{segment_name}"
            modified_lines.append(api_url)
        else:
            modified_lines.append(line)

    modified_playlist = "\n".join(modified_lines)

    return HttpResponse(modified_playlist, content_type="application/vnd.apple.mpegurl")


@api_view(["GET"])
def hls_segment(request, movie_id, resolution, segment_name):
    """
    Endpunkt: /api/video/<int:movie_id>/<str:resolution>/<str:segment_name>/
    Gibt ein einzelnes HLS-Videosegment zurück.
    """
    video = get_object_or_404(Video, id=movie_id)
    quality = get_object_or_404(VideoQuality, video=video, resolution=resolution)

    if quality.processing_status != "completed":
        raise Http404("Video noch nicht verfügbar")

    # Sicherheitscheck: Nur .ts Dateien erlauben
    if not segment_name.endswith(".ts"):
        raise Http404("Ungültiger Segment-Name")

    segment_path = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution, segment_name)

    if not os.path.exists(segment_path):
        raise Http404("Segment nicht gefunden")

    # Zusätzliche Sicherheit: Prüfe, ob der Pfad innerhalb des erwarteten Verzeichnisses liegt
    expected_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(movie_id), resolution)
    if not os.path.commonpath([segment_path, expected_dir]) == expected_dir:
        raise Http404("Ungültiger Pfad")

    return FileResponse(open(segment_path, "rb"), content_type="video/mp2t")
