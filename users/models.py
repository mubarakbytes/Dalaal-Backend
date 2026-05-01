from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.timezone import now

DEFAULT_PROFILE_PHOTO = 'defaults/user_avatar.svg'

class User(AbstractUser):
    is_agent = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True, default='')
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True, default='')
    profile_photo = models.ImageField(upload_to='profile_photos/', default=DEFAULT_PROFILE_PHOTO)

    nira_id_image = models.ImageField(upload_to='verification_docs/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_brokers')
    rejection_reason = models.TextField(blank=True)
    verification_submitted = models.BooleanField(default=False)
    verification_submitted_at = models.DateTimeField(null=True, blank=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    deals_completed = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_rating(self):
        from django.db.models import Avg
        avg = self.reviews_received.aggregate(Avg('rating'))['rating__avg']
        self.rating = avg or 0.0
        self.total_reviews = self.reviews_received.count()
        self.save(update_fields=['rating', 'total_reviews'])


class DeviceToken(models.Model):
    """Push notification tokens for mobile devices"""
    DEVICE_TYPES = (
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('web', 'Web'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField(unique=True)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPES, default='android')
    device_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class Notification(models.Model):
    """In-app notifications"""
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('inquiry', 'New Inquiry'),
        ('listing_approved', 'Listing Approved'),
        ('listing_rejected', 'Listing Rejected'),
        ('verification', 'Verification Update'),
        ('review', 'New Review'),
        ('favorite', 'Property Favorited'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Review(models.Model):
    """Agent reviews and ratings"""
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['reviewer', 'agent']
    
    def __str__(self):
        return f"{self.reviewer.username} -> {self.agent.username} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        self.agent.profile.update_rating()
        
        # Create notification for new reviews
        if is_new:
            reviewer_name = "Anonymous" if self.is_anonymous else (self.reviewer.profile.full_name or self.reviewer.username)
            Notification.objects.create(
                user=self.agent,
                notification_type='review',
                title='New Review Received! ⭐',
                message=f'{reviewer_name} gave you {self.rating} star{"s" if self.rating > 1 else ""} rating' + (f': "{self.comment[:50]}..."' if self.comment else ''),
                data={
                    'review_id': self.id,
                    'rating': self.rating
                }
            )


# Location Models for structured address selection
class State(models.Model):
    """States/Regions - Top level administrative division (e.g., Banadir, Jubaland, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    name_so = models.CharField(max_length=50, blank=True, help_text="Somali name")
    flag_image = models.ImageField(upload_to='state_flags/', blank=True, null=True, help_text="State flag image")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Degmo(models.Model):
    """Degmooyinka (Districts) - Second level, child of State"""
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='degmo')
    name = models.CharField(max_length=100)
    name_so = models.CharField(max_length=100, blank=True, help_text="Somali name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['state', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.state.name}"


class Magaalo(models.Model):
    """Magaalooyinka (Cities) - Third level, child of Degmo"""
    degmo = models.ForeignKey(Degmo, on_delete=models.CASCADE, related_name='magaalo')
    name = models.CharField(max_length=50)
    name_so = models.CharField(max_length=50, blank=True, help_text="Somali name")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['degmo', 'name']
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.degmo.state.name}"
