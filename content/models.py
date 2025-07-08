from django.db import models
from datetime import date


class Video(models.Model):
    create_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=400)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
