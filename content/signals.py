from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.files.storage import default_storage
from django.db import transaction

import django_rq

from .models import Video
from content.tasks import generate_video_thumbnail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Signal is triggered after a video has been saved
    """
    if created and instance.video_file:
        logger.info(f"New Video {instance.title} uploaded, start thumbnail generation")

        transaction.on_commit(lambda: django_rq.enqueue(generate_video_thumbnail, instance.id))

    elif not created and instance.video_file:
        pass


@receiver(post_delete, sender=Video)
def video_post_delete(sender, instance, **kwargs):
    """
    Delte file from filesystem
    when corresponding 'Video' object is delted.
    """

    if instance.video_file:
        try:
            default_storage.delete(instance.video_file.name)
            logger.info(f"Video-file for {instance.id} deleted")
        except Exception as e:
            logger.error(f"Error when deleting the video file for {instance.id}: {str(e)}")

    if instance.thumbnail_url:
        try:
            thumbnail_path = instance.thumbnail_url.split("/")[-2:]
            thumbnail_path = "/".join(thumbnail_path)
            default_storage.delete(thumbnail_path)
            logger.info(f"Thumbnail for {instance.id} deleted")
        except Exception as e:
            logger.error(f"Error when deleting the thumbnail for{instance.id}: {str(e)}")
