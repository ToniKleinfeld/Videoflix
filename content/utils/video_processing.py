import os
from django_rq import job
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

import ffmpeg
import tempfile
import logging
import math

from core.settings import SITE_URL
from content.models import Video, VideoQuality


logger = logging.getLogger(__name__)


def create_temporary_file_mp4(video):
    """ "Create a temporary file for the video in mp4 format."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        video.video_file.open("rb")
        temp_video.write(video.video_file.read())
        video.video_file.close()
        return temp_video.name


def create_temporary_file_thumbnail():
    """Create a temporary file for the thumbnail."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_thumb:
        return temp_thumb.name


def set_timestamp(temp_video_path):
    """Set a timestamp for the thumbnail generation."""
    metadata = ffmpeg.probe(temp_video_path)
    duration = float(metadata["format"]["duration"])
    timestamp = 20 if duration >= 20 else 1
    return timestamp


def generate_thumbnail_try(video, temp_video_path, temp_thumb_path, timestamp):
    """Generate a thumbnail for the video."""
    (
        ffmpeg.input(temp_video_path, ss=timestamp)
        .filter("scale", 640, -1)
        .output(temp_thumb_path, vframes=1, **{"q:v": 2})
        .overwrite_output()
        .run(quiet=True)
    )

    thumbnail_filename = f"thumbnails/{str(video.id)}/{video.title}.jpg"

    with open(temp_thumb_path, "rb") as thumb_file:
        saved_path = default_storage.save(thumbnail_filename, ContentFile(thumb_file.read()))
        relative_url = default_storage.url(saved_path)
        thumbnail_url = f"{SITE_URL}{relative_url}"

        video.thumbnail_url = thumbnail_url
        video.save(update_fields=["thumbnail_url"])

        logger.info(f"Thumbnail for video {video.title} successfully generated: {thumbnail_url}")
