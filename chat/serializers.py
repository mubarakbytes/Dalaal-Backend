from rest_framework import serializers
from .models import Conversation, Message
from users.serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    conversation = serializers.PrimaryKeyRelatedField(queryset=Conversation.objects.all(), required=False)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'content', 'timestamp', 'is_read']
        read_only_fields = ['id', 'sender', 'timestamp', 'is_read']

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    listing = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'listing', 'last_message', 'last_message_at']
    
    def get_listing(self, obj):
        request = self.context.get("request")
        if obj.listing:
            main_photo_url = None
            if obj.listing.main_photo and hasattr(obj.listing.main_photo, "url"):
                main_photo_url = request.build_absolute_uri(obj.listing.main_photo.url) if request else obj.listing.main_photo.url
            return {
                'id': obj.listing.id,
                'title': obj.listing.title,
                'price': str(obj.listing.price),
                'address': obj.listing.address,
                'main_photo': main_photo_url,
            }
        return None
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None
