import os
from django_rq import job
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import ffmpeg
import tempfile
import logging

from .models import Video

logger = logging.getLogger(__name__)


@job("default", timeout=300)
def generate_video_thumbnail(video_id):
    """
    Generate thumbnail with python-ffmpeg
    """

    try:
        video = Video.objects.get(id=video_id)

        if not video.video_file:
            return False

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
            video.video_file.open("rb")
            temp_video.write(video.video_file.read())
            video.video_file.close()
            temp_video_path = temp_video.name

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_thumb:
            temp_thumb_path = temp_thumb.name

        try:
            (
                ffmpeg.input(temp_video_path, ss=5)
                .filter("scale", 640, -1)
                .output(temp_thumb_path, vframes=1, **{"q:v": 2})
                .overwrite_output()
                .run(quiet=True)
            )

            thumbnail_filename = f"thumbnails/image{video.id}.jpg"

            with open(temp_thumb_path, "rb") as thumb_file:
                saved_path = default_storage.save(thumbnail_filename, ContentFile(thumb_file.read()))
                thumbnail_url = default_storage.url(saved_path)

                video.thumbnail_url = thumbnail_url
                video.save(update_fields=["thumbnail_url"])

                logger.info(f"Thumbnail for video {video.title} successfully generated: {thumbnail_url}")

        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False

        finally:
            if os.path.exists(temp_video_path):
                os.unlink(temp_video_path)
            if os.path.exists(temp_thumb_path):
                os.unlink(temp_thumb_path)

        return True

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False
