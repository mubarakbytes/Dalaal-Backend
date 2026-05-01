from django.db import models
from django.utils.timezone import now # <--- Halkan ka hubi inuu jiro

class Announcement(models.Model):
    TARGET_CHOICES = (
        ('all', 'Global'),
        ('agents', 'Agents Only'),
        ('customers', 'Customers Only'),
    )
    
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    content = models.TextField(blank=True)
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    action_link = models.URLField(blank=True, null=True)
    
    # Control Fields (Kuwani ayaa maqnaa)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    start_date = models.DateTimeField(default=now) # <--- Added
    end_date = models.DateTimeField(null=True, blank=True) # <--- Added
    
    def __str__(self):
        return self.title