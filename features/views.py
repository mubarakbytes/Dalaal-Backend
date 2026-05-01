from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import FeatureFlag
from .serializers import FeatureFlagSerializer, FeatureFlagListSerializer


class FeatureFlagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to list all feature flags.
    Read-only - feature flags can only be modified through Django Admin.
    """
    queryset = FeatureFlag.objects.all()
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FeatureFlagListSerializer
        return FeatureFlagSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def feature_flags_all(request):
    """
    Get all feature flags as a key-value dictionary.
    This is the main endpoint the frontend will use.
    """
    flags = FeatureFlag.objects.all()
    result = {flag.key: flag.is_enabled for flag in flags}
    return Response(result)