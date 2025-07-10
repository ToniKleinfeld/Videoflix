from django.contrib import admin
from .models import Video
from django.utils.html import format_html


@admin.register(Video)
class VideoAdminAdvanced(admin.ModelAdmin):
    list_display = ["title", "category", "create_at", "video_preview", "thumbnail_preview", "file_size"]
    list_filter = ["category", "create_at"]
    search_fields = ["title", "description"]
    ordering = ["-create_at"]
    readonly_fields = ["video_preview", "thumbnail_preview", "file_info"]

    fieldsets = (
        ("Grunddaten", {"fields": ("title", "description", "category")}),
        (
            "Medien",
            {"fields": ("video_file", "video_preview", "thumbnail_url", "thumbnail_preview"), "classes": ("wide",)},
        ),
        ("Metadaten", {"fields": ("create_at", "file_info"), "classes": ("collapse",)}),
    )

    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="200" controls><source src="{}" type="video/mp4"></video>', obj.video_file.url
            )
        return "Kein Video vorhanden"

    video_preview.short_description = "Video Vorschau"

    def thumbnail_preview(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;" />', obj.thumbnail_url)
        return "Kein Thumbnail"

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

    file_size.short_description = "Dateigröße"

    def file_info(self, obj):
        if obj.video_file:
            return format_html(
                "<strong>Dateiname:</strong> {}<br>" "<strong>Pfad:</strong> {}<br>" "<strong>Größe:</strong> {}",
                obj.video_file.name.split("/")[-1],
                obj.video_file.name,
                self.file_size(obj),
            )
        return "Keine Datei vorhanden"

    file_info.short_description = "Datei-Informationen"
