from django.contrib import admin
from django.utils.html import format_html

from .models import Video, VideoQuality
import django_rq


@admin.register(Video)
class VideoAdminAdvanced(admin.ModelAdmin):
    """Admin interface for managing Video objects with advanced features."""

    list_display = [
        "title",
        "id",
        "category",
        "created_at",
        "file_size",
        "thumbnail_status",
    ]
    list_filter = ["category", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]
    readonly_fields = ["video_preview", "thumbnail_preview", "file_info", "processing_info"]

    fieldsets = (
        ("Basic data", {"fields": ("title", "description", "category")}),
        (
            "Media",
            {"fields": ("video_file", "video_preview", "thumbnail_url", "thumbnail_preview"), "classes": ("wide",)},
        ),
        ("Processing", {"fields": ("processing_info",), "classes": ("collapse",)}),
        ("Metadata", {"fields": ("created_at", "file_info"), "classes": ("collapse",)}),
    )

    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="200" controls><source src="{}" type="video/mp4"></video>', obj.video_file.url
            )
        return "No video available"

    video_preview.short_description = "Video preview"

    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;" />', obj.thumbnail_url)
        elif obj.video_file:
            return format_html(
                '<div style="width:100px;height:60px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;color:#666;font-size:10px;">Wird generiert...</div>'
            )
        return "No Thumbnail"

    thumbnail_preview.short_description = "Thumbnail"

    def file_size(self, obj):
        if obj.video_file:
            size = obj.video_file.size
            if size > 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024 * 1024):.1f } GB"
            elif size > 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"
            else:
                return f"{size / 1024:.1f} KB"
        return "N/A"

    file_size.short_description = "Filesize"

    def thumbnail_status(self, obj):
        if obj.video_file and obj.thumbnail_url:
            return format_html('<span style="color: green;">✓</span>')
        elif obj.video_file:
            return format_html('<span style="color: orange;">⏳</span>')
        return format_html('<span style="color: red;">✗</span>')

    thumbnail_status.short_description = "Thumbnail Status"

    def file_info(self, obj):
        if obj.video_file:
            return format_html(
                "<strong>Filename:</strong> {}<br>" "<strong>Path:</strong> {}<br>" "<strong>Size:</strong> {}",
                obj.video_file.name.split("/")[-1],
                obj.video_file.name,
                self.file_size(obj),
            )
        return "No file available"

    file_info.short_description = "File-information"

    def processing_info(self, obj):
        queue = django_rq.get_queue("default")
        job_count = len(queue.jobs)

        return format_html(
            "<strong>Queue status:</strong> {} Jobs in the queue<br>" "<strong>Thumbnail status:</strong> {}",
            job_count,
            "Available" if obj.thumbnail_url else "Not generated",
        )

    processing_info.short_description = "Processing status"


class VideoQualityAdmin(admin.ModelAdmin):
    """Admin interface for managing VideoQuality objects."""

    list_display = ("video_title", "resolution", "bitrate", "processing_status")
    list_filter = ("processing_status", "resolution", "video__title")
    search_fields = ("video__title",)

    def video_title(self, obj):
        return obj.video.title

    video_title.short_description = "Video Title"
    video_title.admin_order_field = "video__title"


admin.site.register(VideoQuality, VideoQualityAdmin)
