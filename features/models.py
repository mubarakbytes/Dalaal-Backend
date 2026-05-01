from django.db import models


class FeatureFlag(models.Model):
    CATEGORY_CHOICES = [
        ('filters', 'Filters'),
        ('property_detail', 'Property Detail'),
        ('broker_create', 'Broker Create'),
        ('landing_page', 'Landing Page'),
        ('messaging', 'Messaging'),
        ('global', 'Global'),
    ]

    key = models.CharField(max_length=100, unique=True, help_text="Unique identifier for frontend (e.g., enable_price_filter)")
    name = models.CharField(max_length=200, help_text="Display name for admin")
    description = models.TextField(blank=True, help_text="What this feature controls")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='global')
    is_enabled = models.BooleanField(default=True, help_text="Enable or disable this feature")
    order = models.PositiveIntegerField(default=0, help_text="Display order in admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', 'name']
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'

    def __str__(self):
        return f"{self.key} ({'ON' if self.is_enabled else 'OFF'})"

    def to_key_value(self):
        """Returns key-value pair for API response"""
        return self.key, self.is_enabled