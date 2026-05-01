from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .models import Favorite, Listing, PropertyCategory, PropertyImage, PropertyView
from .serializers import ListingSerializer, PropertyImageSerializer, ListingCreateUpdateSerializer, FavoriteSerializer
from chat.models import Inquiry

@api_view(['GET'])
@permission_classes([AllowAny])
def get_listings(request):
    listings = Listing.objects.filter(status='active').order_by('-created_at')
    serializer = ListingSerializer(listings, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_listing_detail(request, pk):
    try:
        listing = Listing.objects.get(pk=pk)
        listing.views_count += 1
        listing.save()

        PropertyView.objects.create(
            listing=listing,
            viewer=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR')
        )

        serializer = ListingSerializer(listing, context={'request': request})
        return Response(serializer.data)
    except Listing.DoesNotExist:
        return Response({'error': 'Listing not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_listing(request):
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can create listings'}, status=403)

    serializer = ListingCreateUpdateSerializer(data=request.data)
    if serializer.is_valid():
        is_verified = hasattr(request.user, 'profile') and request.user.profile.is_verified
        status = 'active' if is_verified else 'pending'

        listing = serializer.save(agent=request.user, status=status)

        # Handle additional photos
        additional_photos = request.FILES.getlist('additional_photos')
        for index, photo in enumerate(additional_photos):
            PropertyImage.objects.create(
                listing=listing,
                image=photo,
                is_primary=False,
                order=index + 1
            )

        return Response({
            'message': 'Property created successfully!',
            'status': status,
            'auto_approved': is_verified,
            'listing': ListingSerializer(listing, context={'request': request}).data
        }, status=201)

    return Response(serializer.errors, status=400)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if listing.agent != request.user:
        return Response({'error': 'You can only edit your own properties'}, status=403)

    serializer = ListingCreateUpdateSerializer(listing, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(ListingSerializer(listing, context={'request': request}).data)

    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if listing.agent != request.user:
        return Response({'error': 'You can only delete your own properties'}, status=403)

    listing.delete()
    return Response({'message': 'Property deleted successfully'}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_listings(request):
    if not request.user.is_agent:
        return Response({'error': 'Only brokers can access this'}, status=403)

    listings = Listing.objects.filter(agent=request.user).order_by('-created_at')
    serializer = ListingSerializer(listings, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def search_listings(request):
    queryset = Listing.objects.filter(status='active')

    search_query = request.query_params.get('search', '')
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(state__name__icontains=search_query) |
            Q(degmo__name__icontains=search_query) |
            Q(magaalo__name__icontains=search_query) |
            Q(state_text__icontains=search_query) |
            Q(degmo_text__icontains=search_query) |
            Q(magaalo_text__icontains=search_query)
        )

    category_id = request.query_params.get('category_id')
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    else:
        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__name__icontains=category)

    subtype_id = request.query_params.get('subtype_id')
    if subtype_id:
        queryset = queryset.filter(subtype_id=subtype_id)

    transaction_type = request.query_params.get('transaction_type')
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type)

    price_min = request.query_params.get('price_min')
    price_max = request.query_params.get('price_max')
    if price_min:
        queryset = queryset.filter(price__gte=price_min)
    if price_max:
        queryset = queryset.filter(price__lte=price_max)

    # Filter by state ID
    state_id = request.query_params.get('state_id')
    if state_id:
        queryset = queryset.filter(state_id=state_id)

    # Filter by degmo ID (district)
    degmo_id = request.query_params.get('degmo_id')
    if degmo_id:
        queryset = queryset.filter(degmo_id=degmo_id)

    # Filter by city ID (magaalo)
    magaalo_id = request.query_params.get('magaalo_id')
    city_id = request.query_params.get('city_id')
    target_city_id = magaalo_id or city_id
    if target_city_id:
        queryset = queryset.filter(magaalo_id=target_city_id)
    elif request.query_params.get('city'):
        # Fallback to text search if ID not provided
        city_name = request.query_params.get('city')
        queryset = queryset.filter(
            Q(magaalo__name__icontains=city_name) | Q(magaalo_text__icontains=city_name)
        )

    bedrooms = request.query_params.get('bedrooms')
    if bedrooms:
        if str(bedrooms).endswith('+'):
            bedrooms = str(bedrooms).replace('+', '')
        if str(bedrooms).isdigit():
            queryset = queryset.filter(bedrooms__gte=int(bedrooms))

    bathrooms = request.query_params.get('bathrooms')
    if bathrooms and str(bathrooms).isdigit():
        queryset = queryset.filter(bathrooms__gte=int(bathrooms))

    area_min = request.query_params.get('area_min')
    area_max = request.query_params.get('area_max')
    if area_min:
        queryset = queryset.filter(area_sqm__gte=area_min)
    if area_max:
        queryset = queryset.filter(area_sqm__lte=area_max)

    status = request.query_params.get('status')
    if status:
        queryset = queryset.filter(status=status)

    ordering = request.query_params.get('ordering', '-created_at')
    valid_orderings = ['created_at', '-created_at', 'price', '-price', 'views_count', '-views_count']
    if ordering in valid_orderings:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')

    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        page_size = max(1, int(request.query_params.get('page_size', 10)))
    except (TypeError, ValueError):
        page_size = 10

    start = (page - 1) * page_size
    end = start + page_size

    total_count = queryset.count()
    listings = queryset[start:end]

    serializer = ListingSerializer(listings, many=True, context={'request': request})

    return Response({
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def get_property_categories(request):
    categories = (
        PropertyCategory.objects.filter(is_active=True)
        .annotate(count=Count('listings', filter=Q(listings__status='active')))
        .order_by('sort_order', 'name')
    )

    data = [
        {
            'id': category.id,
            'name': category.name,
            'name_so': category.name_so,
            'icon': category.icon,
            'count': category.count,
            # Keep legacy keys for existing clients.
            'value': category.id,
            'label': category.name,
        }
        for category in categories
    ]
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_locations(request):
    active_listings = Listing.objects.filter(status='active')

    state_names = set(active_listings.exclude(state__isnull=True).values_list('state__name', flat=True))
    state_names.update(filter(None, active_listings.values_list('state_text', flat=True)))

    city_names = set(active_listings.exclude(magaalo__isnull=True).values_list('magaalo__name', flat=True))
    city_names.update(filter(None, active_listings.values_list('magaalo_text', flat=True)))

    return Response({
        'states': sorted(state_names),
        'cities': sorted(city_names)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_property_images(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if listing.agent != request.user:
        return Response({'error': 'You can only upload images to your own properties'}, status=403)

    images = request.FILES.getlist('images')
    results = []

    for image in images:
        is_primary = request.POST.get('is_primary', 'false').lower() == 'true'
        prop_image = PropertyImage.objects.create(
            listing=listing,
            image=image,
            is_primary=is_primary
        )
        results.append(PropertyImageSerializer(prop_image, context={'request': request}).data)

    return Response({
        'message': f'{len(results)} images uploaded successfully',
        'images': results
    }, status=201)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_property_image(request, pk, image_id):
    listing = get_object_or_404(Listing, pk=pk)
    image = get_object_or_404(PropertyImage, pk=image_id, listing=listing)

    if listing.agent != request.user:
        return Response({'error': 'You can only delete images from your own properties'}, status=403)

    image.delete()
    return Response({'message': 'Image deleted successfully'}, status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_primary_image(request, pk, image_id):
    listing = get_object_or_404(Listing, pk=pk)
    image = get_object_or_404(PropertyImage, pk=image_id, listing=listing)

    if listing.agent != request.user:
        return Response({'error': 'You can only modify your own properties'}, status=403)

    PropertyImage.objects.filter(listing=listing).update(is_primary=False)
    image.is_primary = True
    image.save()

    return Response({'message': 'Primary image set successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_listing(request, pk):
    if not request.user.is_staff:
        return Response({'error': 'Only admins can approve listings'}, status=403)

    listing = get_object_or_404(Listing, pk=pk)
    action = request.data.get('action')
    reason = request.data.get('reason', '')

    if action == 'approve':
        listing.status = 'active'
        listing.approved_by = request.user
        listing.rejection_reason = ''
        listing.save()
        
        # Notify agent
        from users.models import Notification
        Notification.objects.create(
            user=listing.agent,
            notification_type='listing_approved',
            title='Listing Approved! 🎉',
            message=f'Your property "{listing.title}" has been approved and is now live!',
            data={'listing_id': listing.id}
        )

        return Response({'message': 'Listing approved successfully', 'status': 'active'})

    elif action == 'reject':
        listing.status = 'rejected'
        listing.rejection_reason = reason
        listing.approved_by = None
        listing.save()
        
        # Notify agent
        from users.models import Notification
        Notification.objects.create(
            user=listing.agent,
            notification_type='listing_rejected',
            title='Listing Rejected',
            message=f'Your property "{listing.title}" was not approved. Reason: {reason}',
            data={'listing_id': listing.id}
        )

        return Response({'message': 'Listing rejected', 'status': 'rejected'})

    return Response({'error': 'Invalid action. Use approve or reject'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    if listing.agent != request.user:
        return Response({'error': 'You can only modify your own properties'}, status=403)

    listing.status = 'sold'
    listing.save()

    return Response({'message': 'Listing marked as sold/rented', 'status': 'sold'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_favorites(request):
    """Get user's favorite properties"""
    favorites = Favorite.objects.filter(user=request.user).select_related('listing')
    serializer = FavoriteSerializer(favorites, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_favorite(request, pk):
    """Add property to favorites"""
    listing = get_object_or_404(Listing, pk=pk, status='active')
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        listing=listing
    )
    
    # Notify agent if this is a new favorite
    if created and listing.agent:
        from users.models import Notification
        user_name = request.user.profile.full_name or request.user.username
        Notification.objects.create(
            user=listing.agent,
            notification_type='favorite',
            title='Property Favorited',
            message=f'{user_name} added your property "{listing.title}" to favorites',
            data={
                'listing_id': listing.id,
                'user_id': request.user.id
            }
        )
    
    return Response({
        'message': 'Property added to favorites' if created else 'Already in favorites',
        'created': created,
        'favorite_id': favorite.id
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_favorite(request, pk):
    """Remove property from favorites"""
    deleted, _ = Favorite.objects.filter(user=request.user, listing_id=pk).delete()
    
    return Response({
        'message': 'Removed from favorites' if deleted else 'Not in favorites',
        'deleted': deleted > 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_favorite(request, pk):
    """Check if property is favorited by user"""
    is_favorite = Favorite.objects.filter(user=request.user, listing_id=pk).exists()
    return Response({'is_favorite': is_favorite})
