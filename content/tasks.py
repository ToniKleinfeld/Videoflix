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
from content.utils import video_processing


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

        temp_video_path = video_processing.create_temporary_file_mp4(video)
        temp_thumb_path = video_processing.create_temporary_file_thumbnail()
        timestamp = video_processing.set_timestamp(temp_video_path)

        try:
            video_processing.generate_thumbnail_try(video, temp_video_path, temp_thumb_path, timestamp)

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


@job("default", timeout=14400)
def process_video_task(video_id):
    """
    Generating different resolutions in hls format
    """
    video = Video.objects.get(id=video_id)
    try:
        video_processing.set_prossesing_status(video, "processing")

        resolutions = video_processing.get_resolutions()

        input_path = video.video_file.path
        base_output_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(video.id))
        os.makedirs(base_output_dir, exist_ok=True)

        master_playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"

        for resolution, config in resolutions.items():
            quality, created = VideoQuality.objects.get_or_create(
                video=video, resolution=resolution, defaults={"bitrate": int(config["bitrate"].replace("k", ""))}
            )

            video_processing.set_prossesing_status(quality, "processing")

            try:

                master_playlist_content = video_processing.try_generate_video_quality(
                    video, resolution, config, base_output_dir, input_path, quality, master_playlist_content
                )

            except ffmpeg.Error as e:

                video_processing.set_prossesing_status(quality, "failed")

                logger.error(f"Error at {resolution}: stderr:\n{e.stderr.decode()}")

        master_playlist_path = os.path.join(base_output_dir, "master.m3u8")
        with open(master_playlist_path, "w") as f:
            f.write(master_playlist_content)

        video_processing.set_prossesing_status(video, "completed")
        logger.info(f"Master-Playlist for {video.title} successfully created.")

    except Exception as e:

        video_processing.set_prossesing_status(video, "failed")
        logger.error(f"Error while processing the video: {e}")
