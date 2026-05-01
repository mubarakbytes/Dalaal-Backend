from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Announcement
from .serializers import AnnouncementSerializer
from django.utils.timezone import now
from django.db.models import Q

@api_view(['GET'])
@permission_classes([AllowAny])
def get_announcements(request):
    current_time = now()
    if request.user.is_authenticated and getattr(request.user, 'is_agent', False):
        audience_filter = Q(target_audience='all') | Q(target_audience='agents')
    else:
        audience_filter = Q(target_audience='all') | Q(target_audience='customers')

    ads = (
        Announcement.objects.filter(is_active=True, start_date__lte=current_time)
        .filter(audience_filter)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=current_time))
        .order_by('priority', '-start_date')
    )
    serializer = AnnouncementSerializer(ads, many=True)
    return Response(serializer.data)
