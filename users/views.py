from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Avg
from .models import User, Profile, State, Degmo, Magaalo, DeviceToken, Notification, Review
from .serializers import UserSerializer, ProfileSerializer, DeviceTokenSerializer, NotificationSerializer, ReviewSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def custom_register(request):
    """Custom registration that handles is_agent field"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    re_password = request.data.get('re_password')
    is_agent = request.data.get('is_agent', False)
    
    # Validate required fields
    if not username or not email or not password:
        return Response({'error': 'Username, email and password are required'}, status=400)
    
    if password != re_password:
        return Response({'error': 'Passwords do not match'}, status=400)
    
    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters'}, status=400)
    
    # Check if user exists
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=400)
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        is_agent=is_agent
    )
    
    # Create profile
    Profile.objects.create(user=user)
    
    return Response({
        'message': 'Account created successfully',
        'user_id': user.id,
        'username': user.username,
        'is_agent': user.is_agent
    }, status=201)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_agents(request):
    agents = User.objects.filter(is_agent=True, profile__is_verified=True)
    serializer = UserSerializer(agents, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def my_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_verification_doc(request):
    """Upload verification document (NIRA ID or license)"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found. Please complete your profile first.'}, status=404)

    if not request.user.is_agent:
        return Response({'error': 'Only agents can upload verification documents'}, status=403)

    document = request.FILES.get('nira_id_image') or request.FILES.get('verification_document')
    if document:
        profile.nira_id_image = document
        profile.is_verified = False
        profile.verification_submitted = True
        profile.verification_submitted_at = timezone.now()
        profile.rejection_reason = ''
        profile.save()

        return Response({
            'message': 'Verification document uploaded successfully. Awaiting admin approval.',
            'verification_status': 'pending'
        })

    return Response({'error': 'No verification document provided'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_status(request):
    """Get current verification status"""
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=404)

    return Response({
        'is_verified': profile.is_verified,
        'verification_submitted': getattr(profile, 'verification_submitted', False),
        'verified_at': profile.verified_at,
        'rejection_reason': profile.rejection_reason
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_verifications(request):
    """Get pending agent verifications (admin only)"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=403)

    pending_agents = User.objects.filter(
        is_agent=True,
        profile__verification_submitted=True,
        profile__is_verified=False
    ).order_by('-profile__verification_submitted_at')

    results = []
    for user in pending_agents:
        results.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.profile.full_name,
            'submitted_at': user.profile.verification_submitted_at if hasattr(user.profile, 'verification_submitted_at') else None,
            'rejection_reason': user.profile.rejection_reason
        })

    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_agent(request, user_id):
    """Approve or reject agent verification (admin only)"""
    if not request.user.is_staff:
        return Response({'error': 'Admin access required'}, status=403)

    agent = get_object_or_404(User, id=user_id)

    if not agent.is_agent:
        return Response({'error': 'User is not an agent'}, status=400)

    action = request.data.get('action')
    reason = request.data.get('reason', '')

    if action == 'approve':
        agent.profile.is_verified = True
        agent.profile.verified_at = timezone.now()
        agent.profile.verified_by = request.user
        agent.profile.verification_submitted = False
        agent.profile.verification_submitted_at = None
        agent.profile.rejection_reason = ''
        agent.profile.save()

        Notification.objects.create(
            user=agent,
            notification_type='verification',
            title='Verification Approved',
            message='Your agent verification has been approved.',
        )

        return Response({'message': 'Agent verified successfully', 'is_verified': True})

    elif action == 'reject':
        agent.profile.is_verified = False
        agent.profile.verified_at = None
        agent.profile.verified_by = None
        agent.profile.verification_submitted = False
        agent.profile.verification_submitted_at = None
        agent.profile.rejection_reason = reason
        agent.profile.save()

        Notification.objects.create(
            user=agent,
            notification_type='verification',
            title='Verification Rejected',
            message='Your agent verification was rejected.' + (f' Reason: {reason}' if reason else ''),
        )

        return Response({'message': 'Agent verification rejected', 'rejection_reason': reason})

    return Response({'error': 'Invalid action. Use approve or reject'}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_detail(request, user_id):
    """Get detailed agent profile"""
    agent = get_object_or_404(User, id=user_id, is_agent=True)

    if not (hasattr(agent, 'profile') and agent.profile.is_verified):
        return Response({'error': 'Agent not found or not verified'}, status=404)

    serializer = UserSerializer(agent, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_listings_stats(request):
    """Get statistics for agent's listings"""
    if not request.user.is_agent:
        return Response({'error': 'Only agents can access this'}, status=403)

    from properties.models import Listing
    from chat.models import Inquiry

    listings = Listing.objects.filter(agent=request.user)

    return Response({
        'total_listings': listings.count(),
        'active_listings': listings.filter(status='active').count(),
        'pending_listings': listings.filter(status='pending').count(),
        'sold_listings': listings.filter(status='sold').count(),
        'total_views': sum(l.views_count for l in listings),
        'total_inquiries': Inquiry.objects.filter(listing__agent=request.user).count()
    })


# Location API Views
@api_view(['GET'])
@permission_classes([AllowAny])
def get_states(request):
    """Get all states/regions"""
    states = State.objects.filter(is_active=True).order_by('name')
    data = []
    for s in states:
        flag_url = None
        if s.flag_image:
            flag_url = request.build_absolute_uri(s.flag_image.url) if request else s.flag_image.url
        data.append({
            'id': s.id, 
            'name': s.name, 
            'name_so': s.name_so, 
            'flag_image': flag_url
        })
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_degmo(request):
    """Get districts by state"""
    state_id = request.query_params.get('state_id')
    if state_id:
        degmo = Degmo.objects.filter(state_id=state_id, is_active=True).order_by('name')
    else:
        degmo = Degmo.objects.filter(is_active=True).order_by('name')
    
    data = [{'id': d.id, 'name': d.name, 'name_so': d.name_so, 'state_id': d.state_id} for d in degmo]
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_magaalo(request):
    """Get cities by district"""
    degmo_id = request.query_params.get('degmo_id')
    if degmo_id:
        magaalo = Magaalo.objects.filter(degmo_id=degmo_id, is_active=True).order_by('name')
    else:
        magaalo = Magaalo.objects.filter(is_active=True).order_by('name')
    
    data = [{'id': m.id, 'name': m.name, 'name_so': m.name_so, 'degmo_id': m.degmo_id} for m in magaalo]
    return Response(data)


# Property Categories API
from properties.models import PropertyCategory, PropertySubtype

@api_view(['GET'])
@permission_classes([AllowAny])
def get_property_categories(request):
    """Get all property categories"""
    categories = PropertyCategory.objects.filter(is_active=True).order_by('sort_order', 'name')
    data = [{'id': c.id, 'name': c.name, 'name_so': c.name_so, 'icon': c.icon} for c in categories]
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_property_subtypes(request):
    """Get subtypes by category"""
    category_id = request.query_params.get('category_id')
    if category_id:
        subtypes = PropertySubtype.objects.filter(category_id=category_id, is_active=True).order_by('sort_order', 'name')
    else:
        subtypes = PropertySubtype.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    data = [{'id': s.id, 'name': s.name, 'name_so': s.name_so, 'category_id': s.category_id} for s in subtypes]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device_token(request):
    """Register push notification token"""
    token = request.data.get('token')
    device_type = request.data.get('device_type', 'android')
    device_name = request.data.get('device_name', '')
    
    if not token:
        return Response({'error': 'Token is required'}, status=400)
    
    device_token, created = DeviceToken.objects.update_or_create(
        token=token,
        defaults={
            'user': request.user,
            'device_type': device_type,
            'device_name': device_name,
            'is_active': True
        }
    )
    
    return Response({
        'message': 'Device token registered successfully',
        'created': created
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unregister_device_token(request):
    """Unregister push notification token"""
    token = request.data.get('token')
    
    if not token:
        return Response({'error': 'Token is required'}, status=400)
    
    deleted, _ = DeviceToken.objects.filter(token=token, user=request.user).delete()
    
    return Response({
        'message': 'Device token unregistered',
        'deleted': deleted > 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    """Get user notifications"""
    notifications = Notification.objects.filter(user=request.user)[:50]
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()
    return Response({'message': 'Notification marked as read'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    return Response({'message': 'All notifications marked as read'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notification_count(request):
    """Get unread notification count"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def agent_reviews(request, agent_id):
    """Get agent reviews or create a review"""
    agent = get_object_or_404(User, id=agent_id, is_agent=True)
    
    if request.method == 'GET':
        reviews = Review.objects.filter(agent=agent)
        serializer = ReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    if request.method == 'POST':
        if agent == request.user:
            return Response({'error': 'You cannot review yourself'}, status=400)
        
        existing_review = Review.objects.filter(reviewer=request.user, agent=agent).first()
        if existing_review:
            return Response({'error': 'You have already reviewed this agent'}, status=400)
        
        serializer = ReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(reviewer=request.user, agent=agent)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def update_delete_review(request, review_id):
    """Update or delete a review"""
    review = get_object_or_404(Review, id=review_id, reviewer=request.user)
    
    if request.method == 'PUT':
        serializer = ReviewSerializer(review, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
    
    if request.method == 'DELETE':
        review.delete()
        return Response({'message': 'Review deleted'}, status=200)
