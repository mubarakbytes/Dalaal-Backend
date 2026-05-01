from rest_framework import serializers
from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = (
            'id',
            'title',
            'image',
            'content',
            'target_audience',
            'action_link',
            'priority',
            'start_date',
            'end_date',
        )
