from django.db import models
from datetime import date


class Video(models.Model):
    created_at = models.DateField(default=date.today)
    title = models.CharField(max_length=80)
    description = models.TextField(max_length=400)
    video_file = models.FileField(upload_to="videos", blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=40, default="None")
    duration = models.DurationField(null=True, blank=True)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    hls_master_playlist = models.FileField(upload_to="hls/master/", blank=True, null=True)

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class VideoQuality(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="qualities")
    resolution = models.CharField(
        max_length=10,
        choices=[
            ("480p", "480p"),
            ("720p", "720p"),
            ("1080p", "1080p"),
        ],
    )
    bitrate = models.IntegerField()
    hls_playlist_path = models.CharField(max_length=255, blank=True, null=True)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    class Meta:
        unique_together = ["video", "resolution"]

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"
