from django.db import models
from datetime import date


class Video(models.Model):
    create_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.TextField(max_length=400)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=40, default="None")

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-create_at"]

    def __str__(self):
        return self.title
