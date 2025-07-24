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
    """Create a temporary file for the video in mp4 format."""
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


def set_prossesing_status(video, status):
    """Set the processing status of the video."""
    video.processing_status = status
    video.save()


def get_resolutions():
    """Define the resolutions for video processing."""
    return {
        "480p": {"height": 480, "bitrate": "1600k"},
        "720p": {"height": 720, "bitrate": "2500k"},
        "1080p": {"height": 1080, "bitrate": "5000k"},
    }


def get_resolution_width(height):
    """Calculate width based on 16:9 aspect ratio"""
    return int(height * 16 / 9)


def try_generate_video_quality(
    video, resolution, config, base_output_dir, input_path, quality, master_playlist_content
):
    """Generate video quality for a specific resolution."""
    resolution_dir = os.path.join(base_output_dir, resolution)
    os.makedirs(resolution_dir, exist_ok=True)

    playlist_path = os.path.join(resolution_dir, "index.m3u8")
    segment_pattern = os.path.join(resolution_dir, "%03d.ts")

    stream = stream_video(input_path, playlist_path, config, segment_pattern)

    ffmpeg.run(stream, overwrite_output=True, quiet=True)

    quality.hls_playlist_path = f"hls/{video.id}/{resolution}/index.m3u8"

    set_prossesing_status(quality, "completed")

    bandwidth = int(config["bitrate"].replace("k", "")) * 1000
    master_playlist_content += f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={get_resolution_width(config['height'])}x{config['height']}\n"
    master_playlist_content += f"/api/video/{video.id}/{resolution}/index.m3u8\n\n"

    return master_playlist_content


def stream_video(input_path, playlist_path, config, segment_pattern):
    """Create a video stream for processing."""
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

    return stream
