from django.contrib import admin

from core.admin import PhotoPreviewMixin
from .models import Event, EventAlbum, EventPhoto


class EventPhotoInline(PhotoPreviewMixin, admin.TabularInline):
    model = EventPhoto
    extra = 1
    fields = ['image', 'photo_preview', 'alt_text', 'caption', 'display_order', 'is_active']
    readonly_fields = ['photo_preview']


@admin.register(Event)
class EventAdmin(PhotoPreviewMixin, admin.ModelAdmin):
    list_display = ['title', 'starts_at', 'venue', 'status', 'category']
    list_filter = ['status', 'category']
    search_fields = ['title', 'description', 'venue']
    prepopulated_fields = {'slug': ['title']}
    readonly_fields = ['photo_preview']
    fieldsets = [
        (None, {'fields': ['title', 'slug', 'description', 'category', 'status']}),
        ('When and where', {'fields': ['starts_at', 'ends_at', 'venue', 'directions_url']}),
        ('Cover photo', {'fields': ['image', 'alt_text', 'photo_preview']}),
    ]


@admin.register(EventAlbum)
class EventAlbumAdmin(PhotoPreviewMixin, admin.ModelAdmin):
    list_display = ['title', 'event', 'is_published']
    list_filter = ['is_published']
    search_fields = ['title', 'event__title']
    autocomplete_fields = ['event']
    readonly_fields = ['photo_preview']
    inlines = [EventPhotoInline]
