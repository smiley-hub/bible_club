from django.contrib import admin
from django.utils.html import format_html

from .models import ClubProfile, FAQ, HistoryMilestone, HomeSlide, Organizer


class PhotoPreviewMixin:
    @admin.display(description='Current photo')
    def photo_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" alt="{}" style="max-width:240px;max-height:150px;object-fit:contain">', obj.image.url, obj.alt_text)
        return 'No photo uploaded.'


@admin.register(ClubProfile)
class ClubProfileAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return super().has_add_permission(request) and not ClubProfile.objects.exists()


@admin.register(HomeSlide)
class HomeSlideAdmin(PhotoPreviewMixin, admin.ModelAdmin):
    list_display = ['title', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'caption', 'alt_text']
    readonly_fields = ['photo_preview']


@admin.register(HistoryMilestone)
class HistoryMilestoneAdmin(PhotoPreviewMixin, admin.ModelAdmin):
    list_display = ['title', 'year', 'display_order', 'is_published']
    list_editable = ['display_order', 'is_published']
    list_filter = ['is_published', 'year']
    search_fields = ['title', 'story']
    readonly_fields = ['photo_preview']


@admin.register(Organizer)
class OrganizerAdmin(PhotoPreviewMixin, admin.ModelAdmin):
    list_display = ['name', 'role', 'display_order', 'is_active']
    list_editable = ['display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'role']
    readonly_fields = ['photo_preview']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'display_order', 'is_published']
    list_editable = ['display_order', 'is_published']
    list_filter = ['is_published']
    search_fields = ['question', 'answer']


admin.site.site_header = 'METU Bible Club administration'
admin.site.site_title = 'METU Bible Club'
admin.site.index_title = 'Manage club content'
