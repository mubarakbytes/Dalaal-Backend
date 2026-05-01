from django.contrib import admin
from .models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ['key', 'name', 'category', 'is_enabled', 'order', 'updated_at']
    list_filter = ['category', 'is_enabled']
    search_fields = ['key', 'name', 'description']
    list_editable = ['is_enabled', 'order']
    ordering = ['category', 'order', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('key', 'name', 'description')
        }),
        ('Settings', {
            'fields': ('category', 'is_enabled', 'order')
        }),
    )