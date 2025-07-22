import os
from django_rq import job
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

import ffmpeg
import tempfile
import logging

from .models import Video, VideoQuality

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
                ffmpeg.input(temp_video_path, ss=20)
                .filter("scale", 640, -1)
                .output(temp_thumb_path, vframes=1, **{"q:v": 2})
                .overwrite_output()
                .run(quiet=True)
            )

            thumbnail_filename = f"thumbnails/{video.title + str(video.id)}.jpg"

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
