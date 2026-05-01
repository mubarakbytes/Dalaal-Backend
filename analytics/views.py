from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from properties.models import Listing, PropertyView
from chat.models import Inquiry

# 1. Broker Dashboard Stats (Tirakoobka Dashboard-ka Dilaalka)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def broker_dashboard_stats(request):
    """
    Soo qaado tirakoobka guud ee dilaalka
    Get overall statistics for the broker
    """
    # Hubi inuu dilaal yahay
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can access this'}, status=403)
    
    # Hantida dilaalka
    my_listings = Listing.objects.filter(agent=request.user)
    
    stats = {
        'total_properties': my_listings.count(),
        'active_properties': my_listings.filter(status='active').count(),
        'pending_properties': my_listings.filter(status='pending').count(),
        'sold_properties': my_listings.filter(status='sold').count(),
        'total_views': sum(listing.views_count for listing in my_listings),
        'total_inquiries': Inquiry.objects.filter(listing__agent=request.user).count(),
    }
    
    return Response(stats)


# 2. Property Performance (Waxqabadka Hanti Gaar ah)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def property_performance(request):
    """
    Soo qaado waxqabadka hanti kasta
    Get performance metrics for each property
    """
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can access this'}, status=403)
    
    my_listings = Listing.objects.filter(agent=request.user)
    
    performance = []
    for listing in my_listings:
        performance.append({
            'id': listing.id,
            'title': listing.title,
            'views': listing.views_count,
            'inquiries': Inquiry.objects.filter(listing=listing).count(),
            'status': listing.status,
            'created_at': listing.created_at,
        })
    
    # Sort by views (descending)
    performance.sort(key=lambda x: x['views'], reverse=True)
    
    return Response(performance)


# 3. Views Over Time (Daawashada Waqtiga)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def views_over_time(request):
    """
    Soo qaado daawashada 30 maalmood ee la soo dhaafay
    Get views for the last 30 days
    """
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can access this'}, status=403)
    
    # Last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all views for broker's properties
    views = PropertyView.objects.filter(
        listing__agent=request.user,
        viewed_at__gte=start_date
    )
    
    # Group by date
    views_by_date = {}
    for view in views:
        date_key = view.viewed_at.date().isoformat()
        views_by_date[date_key] = views_by_date.get(date_key, 0) + 1
    
    # Convert to list format for charts
    data = [
        {'date': date, 'views': count}
        for date, count in sorted(views_by_date.items())
    ]
    
    return Response(data)


# 4. Inquiries Over Time (Su'aalaha Waqtiga)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inquiries_over_time(request):
    """
    Soo qaado su'aalaha 30 maalmood ee la soo dhaafay
    Get inquiries for the last 30 days
    """
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can access this'}, status=403)
    
    # Last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get all inquiries for broker's properties
    inquiries = Inquiry.objects.filter(
        listing__agent=request.user,
        created_at__gte=start_date
    )
    
    # Group by date
    inquiries_by_date = {}
    for inquiry in inquiries:
        date_key = inquiry.created_at.date().isoformat()
        inquiries_by_date[date_key] = inquiries_by_date.get(date_key, 0) + 1
    
    # Convert to list format for charts
    data = [
        {'date': date, 'inquiries': count}
        for date, count in sorted(inquiries_by_date.items())
    ]
    
    return Response(data)
