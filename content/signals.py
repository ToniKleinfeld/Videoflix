import os
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.files.storage import default_storage
from django.db import transaction
from django.conf import settings

from .models import Video
from content.tasks import generate_video_thumbnail, process_video_task
from urllib.parse import unquote
from datetime import timedelta

import django_rq
import shutil
import logging
import ffmpeg


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Signal is triggered after a video has been saved
    """
    if created and instance.video_file:
        try:
            probe = ffmpeg.probe(instance.video_file.path)
            duration_seconds = float(probe["format"]["duration"])
            instance.duration = timedelta(seconds=duration_seconds)
            instance.save(update_fields=["duration"])
        except Exception as e:
            logger.error(f"Error when extracting the duration: {e}")

        logger.info(f"New Video {instance.title} uploaded, start thumbnail generation")
        transaction.on_commit(lambda: django_rq.enqueue(generate_video_thumbnail, instance.id))

        logger.info(f"New Video {instance.title} uploaded, start Generating different resolutions")
        transaction.on_commit(lambda: django_rq.enqueue(process_video_task, instance.id))

    elif not created and instance.video_file:
        pass


@receiver(post_delete, sender=Video)
def video_post_delete(sender, instance, **kwargs):
    """
    Delte files from filesystem
    when corresponding 'Video' object is delted.
    """

    if instance.video_file:
        try:
            default_storage.delete(instance.video_file.name)
            logger.info(f"Video-file for {instance.title} deleted")
        except Exception as e:
            logger.error(f"Error when deleting the video file for {instance.id}: {str(e)}")

    if instance.thumbnail_url:
        try:
            thumbnail_path = instance.thumbnail_url.split("/")[-2:]
            thumbnail_path = "/".join(thumbnail_path)
            thumbnail_path = unquote(thumbnail_path)
            default_storage.delete(thumbnail_path)
            logger.info(f"Thumbnail {instance.title + str(instance.id)} deleted")
        except Exception as e:
            logger.error(f"Error when deleting the thumbnail for{instance}: {str(e)}")

    cleanup_hls_files(instance.id)


def cleanup_hls_files(video):
    """Helpfunction delte HLS-files"""

    video_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(video.id))
    if os.path.exists(video_dir):
        try:
            shutil.rmtree(video_dir)
            print(f"HLS-files Video {video.title} deletet")
        except Exception as e:
            print(f"Error delete HLS-files: {e}")
