from django.contrib import admin
from .models import Announcement

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_audience', 'is_active', 'priority', 'start_date', 'end_date')
    list_editable = ('is_active', 'priority')
    list_filter = ('target_audience', 'is_active', 'start_date')
    search_fields = ('title', 'content')
    ordering = ('priority', '-start_date')

admin.site.register(Announcement, AnnouncementAdmin)
