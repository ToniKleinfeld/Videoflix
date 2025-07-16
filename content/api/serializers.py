from rest_framework import serializers
from content.models import Video


class VideoListSerializer(serializers.ModelSerializer):
    """
    Serializer for Video list view - returns basic information only
    """

    class Meta:
        model = Video
        fields = ["id", "created_at", "title", "description", "thumbnail_url", "category"]
        read_only_fields = ["id", "created_at"]
