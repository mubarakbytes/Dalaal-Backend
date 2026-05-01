from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from .models import Profile, DeviceToken, Notification, Review, DEFAULT_PROFILE_PHOTO

User = get_user_model()
DEFAULT_PROFILE_STATIC_PATH = "users/default-avatar.svg"


def _build_static_url(path, request=None):
    static_path = static(path)
    return request.build_absolute_uri(static_path) if request else static_path


def _resolve_profile_photo_url(profile, request=None):
    if profile.profile_photo and hasattr(profile.profile_photo, "url"):
        # Treat legacy/default placeholders as "no custom photo" and use tracked static avatar.
        if profile.profile_photo.name in {DEFAULT_PROFILE_PHOTO, "defaults/user_avatar.png"}:
            return _build_static_url(DEFAULT_PROFILE_STATIC_PATH, request=request)
        return request.build_absolute_uri(profile.profile_photo.url) if request else profile.profile_photo.url
    return _build_static_url(DEFAULT_PROFILE_STATIC_PATH, request=request)

class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    is_agent = serializers.BooleanField(source='user.is_agent', read_only=True)
    is_customer = serializers.BooleanField(source='user.is_customer', read_only=True)
    profile_photo_url = serializers.SerializerMethodField()
    total_reviews = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id',
            'username',
            'email',
            'is_agent',
            'is_customer',
            'full_name',
            'bio',
            'city',
            'phone',
            'profile_photo',
            'profile_photo_url',
            'is_verified',
            'rating',
            'total_reviews',
            'deals_completed',
            'verification_submitted',
            'verification_submitted_at',
            'verified_at',
            'rejection_reason'
        ]
        extra_kwargs = {
            'full_name': {'required': False, 'allow_blank': True},
            'bio': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
        }

    def get_profile_photo_url(self, obj):
        request = self.context.get('request')
        return _resolve_profile_photo_url(obj, request=request)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        request = self.context.get("request")
        resolved_url = _resolve_profile_photo_url(obj, request=request)
        data["profile_photo_url"] = resolved_url
        data["profile_photo"] = resolved_url
        return data


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'device_type', 'device_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'data', 'is_read', 'read_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    reviewer_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'reviewer_name', 'reviewer_photo', 'agent', 'rating', 'comment', 'is_anonymous', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'reviewer']
    
    def get_reviewer_name(self, obj):
        if obj.is_anonymous:
            return "Anonymous"
        return obj.reviewer.username
    
    def get_reviewer_photo(self, obj):
        if obj.is_anonymous:
            return None
        request = self.context.get('request')
        if hasattr(obj.reviewer, 'profile') and obj.reviewer.profile.profile_photo:
            return _resolve_profile_photo_url(obj.reviewer.profile, request=request)
        return _build_static_url(DEFAULT_PROFILE_STATIC_PATH, request=request)


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_agent', 'is_customer', 'profile']

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return ProfileSerializer(profile, context=self.context).data
        except Profile.DoesNotExist:
            return None


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password', 'is_agent', 'is_customer')
