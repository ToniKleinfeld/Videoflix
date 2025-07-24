from rest_framework import generics, permissions

from content.api.serializers import VideoListSerializer
from content.models import Video


class VideoListView(generics.ListAPIView):
    """
    Returns list of all videos with basic information
    """

    queryset = Video.objects.all()
    serializer_class = VideoListSerializer

    permission_classes = [permissions.IsAuthenticated]
