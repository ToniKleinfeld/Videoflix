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


@job("default", timeout=3600)
def process_video_task(video_id):
    """
    Generating different resolutions in hls format
    """
    try:
        video = Video.objects.get(id=video_id)
        video.processing_status = "processing"
        video.save()

        resolutions = {
            "480p": {"height": 480, "bitrate": "1600k"},
            "720p": {"height": 720, "bitrate": "2500k"},
            "1080p": {"height": 1080, "bitrate": "5000k"},
        }

        input_path = video.video_file.path
        base_output_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(video.id))
        os.makedirs(base_output_dir, exist_ok=True)

        master_playlist_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"

        for resolution, config in resolutions.items():
            quality, created = VideoQuality.objects.get_or_create(
                video=video, resolution=resolution, defaults={"bitrate": int(config["bitrate"].replace("k", ""))}
            )
            quality.processing_status = "processing"
            quality.save()

            try:
                resolution_dir = os.path.join(base_output_dir, resolution)
                os.makedirs(resolution_dir, exist_ok=True)

                playlist_path = os.path.join(resolution_dir, "index.m3u8")
                segment_pattern = os.path.join(resolution_dir, "%03d.ts")

                stream = ffmpeg.input(input_path)
                stream = ffmpeg.output(
                    stream,
                    playlist_path,
                    vcodec="libx264",
                    acodec="aac",
                    vf=f'scale=-2:{config["height"]}',
                    hls_time=15,
                    hls_playlist_type="vod",
                    hls_segment_filename=segment_pattern,
                    f="hls",
                    **{
                        "b:v": config["bitrate"],
                        "b:a": "128k",
                    },
                )

                ffmpeg.run(stream, overwrite_output=True, quiet=True)

                quality.hls_playlist_path = f"hls/{video.id}/{resolution}/index.m3u8"
                quality.processing_status = "completed"
                quality.save()

                bandwidth = int(config["bitrate"].replace("k", "")) * 1000
                master_playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={get_resolution_width(config['height'])}x{config['height']}\n"
                master_playlist_content += f"/api/video/{video.id}/{resolution}/index.m3u8\n\n"

            except ffmpeg.Error as e:
                quality.processing_status = "failed"
                quality.save()
                logger.error(f"Error at {resolution}: stderr:\n{e.stderr.decode()}")

        master_playlist_path = os.path.join(base_output_dir, "master.m3u8")
        with open(master_playlist_path, "w") as f:
            f.write(master_playlist_content)

        video.processing_status = "completed"
        video.save()
        logger.info(f"Master-Playlist for {video.title} successfully created.")

    except Exception as e:
        video.processing_status = "failed"
        video.save()
        logger.error(f"Error while processing the video: {e}")


def get_resolution_width(height):
    """Calculate width based on 16:9 aspect ratio"""
    return int(height * 16 / 9)
