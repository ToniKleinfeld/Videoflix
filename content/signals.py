from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
import os


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print("Video saved")
    if created:
        print("New video created")


@receiver(post_delete, sender=Video)
def auto_delte_file_on_delte(sender, instance, **kwargs):
    """
    Delte file from filesystem
    when corresponding 'Video' object is delted.
    """

    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
            print("Video ${video_file} is removed")


# TODO: später auch die konvertierten videos! nicht vergessen
