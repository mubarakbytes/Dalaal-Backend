from django.db import models
from django.conf import settings

class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    # Waxaan ku xireynaa 'Listing' oo ku jirta app-ka 'properties'
    # Qaabka loo qoro: 'app_name.ModelName'
    listing = models.ForeignKey('properties.Listing', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Track who started the conversation
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='started_conversations')
    
    started_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_message_at']


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


class Inquiry(models.Model):
    """Su'aalaha - Track when customer starts conversation about property"""
    listing = models.ForeignKey('properties.Listing', on_delete=models.CASCADE, related_name='inquiries')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_inquiries')
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Inquiries'
    
    def __str__(self):
        return f"{self.customer.username} inquired about {self.listing.title}"