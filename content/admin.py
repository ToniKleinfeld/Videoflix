from django.contrib import admin
from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "create_at"]
    list_filter = ["create_at"]
    search_fields = ["title", "description"]
    ordering = ["-create_at"]
