from rest_framework import serializers
from .models import FeatureFlag


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ['key', 'name', 'description', 'category', 'is_enabled', 'order']


class FeatureFlagListSerializer(serializers.Serializer):
    """Serializer that returns all features as a key-value dictionary"""
    def to_representation(self, instance):
        return {flag.key: flag.is_enabled for flag in instance}