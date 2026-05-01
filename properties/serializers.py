from rest_framework import serializers
from django.db.models import Q
from .models import Listing, PropertyImage, PropertyView, PropertyCategory, PropertySubtype, Favorite
from users.serializers import UserSerializer


class FavoriteSerializer(serializers.ModelSerializer):
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    listing_price = serializers.DecimalField(source='listing.price', max_digits=12, decimal_places=2, read_only=True)
    listing_photo = serializers.SerializerMethodField()
    listing_address = serializers.CharField(source='listing.address', read_only=True)
    listing_category = serializers.CharField(source='listing.category.name', read_only=True)
    listing_bedrooms = serializers.IntegerField(source='listing.bedrooms', read_only=True)
    listing_bathrooms = serializers.IntegerField(source='listing.bathrooms', read_only=True)
    listing_area = serializers.IntegerField(source='listing.area_sqm', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'id', 'listing', 'listing_title', 'listing_price', 'listing_photo',
            'listing_address', 'listing_category', 'listing_bedrooms',
            'listing_bathrooms', 'listing_area', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_listing_photo(self, obj):
        request = self.context.get('request')
        if obj.listing.main_photo and hasattr(obj.listing.main_photo, 'url'):
            return request.build_absolute_uri(obj.listing.main_photo.url) if request else obj.listing.main_photo.url
        return None


class PropertyImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'image_url', 'is_primary', 'order', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None

class PropertyViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyView
        fields = ['id', 'viewer', 'ip_address', 'viewed_at']

class PropertyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCategory
        fields = ['id', 'name', 'name_so', 'icon']

class PropertySubtypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertySubtype
        fields = ['id', 'name', 'name_so', 'category_id']

class ListingSerializer(serializers.ModelSerializer):
    agent = UserSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    property_category_display = serializers.CharField(source='get_category_display', read_only=True)
    property_category = serializers.SerializerMethodField()
    subtype_display = serializers.CharField(source='get_subtype_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    state = serializers.CharField(source='get_state_display', read_only=True)
    degmo = serializers.CharField(source='get_degmo_display', read_only=True)
    magaalo = serializers.CharField(source='get_magaalo_display', read_only=True)
    district = serializers.CharField(source='get_degmo_display', read_only=True)
    city = serializers.CharField(source='get_magaalo_display', read_only=True)
    state_id = serializers.IntegerField(source='state.id', read_only=True, allow_null=True)
    degmo_id = serializers.IntegerField(source='degmo.id', read_only=True, allow_null=True)
    magaalo_id = serializers.IntegerField(source='magaalo.id', read_only=True, allow_null=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True, allow_null=True)
    subtype_id = serializers.IntegerField(source='subtype.id', read_only=True, allow_null=True)
    price_period_display = serializers.CharField(source='get_price_period_display', read_only=True)
    
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'slug', 'price', 'price_period', 'price_period_display',
            'category', 'category_id', 'category_display', 'property_category_display', 'property_category',
            'subtype', 'subtype_id', 'subtype_display',
            'transaction_type', 'transaction_type_display',
            'state', 'state_id', 'degmo', 'degmo_id', 'magaalo', 'magaalo_id', 'district', 'city',
            'state_text', 'degmo_text', 'magaalo_text',
            'address', 'latitude', 'longitude',
            'area_sqm', 'area_width', 'area_length', 'description', 'features',
            'bedrooms', 'bathrooms', 'living_rooms', 'kitchens', 'parking_spots',
            'floor', 'year_built', 'is_furnished',
            'height_meters', 'has_loading_dock', 'has_corridor_access',
            'land_type',
            'main_photo', 'images', 'status', 'status_display',
            'views_count', 'created_at', 'updated_at',
            'agent'
        ]
        extra_kwargs = {
            'main_photo': {'required': False}
        }

    def get_property_category(self, obj):
        if obj.category and obj.category.slug:
            return obj.category.slug
        return ''


class ListingCreateUpdateSerializer(serializers.ModelSerializer):
    state_id = serializers.IntegerField(required=False, allow_null=True)
    degmo_id = serializers.IntegerField(required=False, allow_null=True)
    magaalo_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    subtype_id = serializers.IntegerField(required=False, allow_null=True)
    property_category = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Listing
        fields = [
            'title', 'price', 'price_period',
            'property_category',
            'category_id', 'subtype_id', 'transaction_type',
            'state_id', 'degmo_id', 'magaalo_id',
            'state_text', 'degmo_text', 'magaalo_text',
            'address', 'latitude', 'longitude',
            'area_sqm', 'area_width', 'area_length', 'description', 'features',
            'bedrooms', 'bathrooms', 'living_rooms', 'kitchens', 'parking_spots',
            'floor', 'year_built', 'is_furnished',
            'height_meters', 'has_loading_dock', 'has_corridor_access',
            'land_type',
            'main_photo'
        ]
        extra_kwargs = {
            'main_photo': {'required': False}
        }

    def validate(self, data):
        state_id = data.get('state_id')
        degmo_id = data.get('degmo_id')
        magaalo_id = data.get('magaalo_id')
        category_id = data.get('category_id')
        subtype_id = data.get('subtype_id')
        property_category = data.get('property_category')

        if state_id:
            from users.models import State
            try:
                data['state'] = State.objects.get(id=state_id)
            except State.DoesNotExist:
                raise serializers.ValidationError({'state_id': 'Invalid State ID'})

        if degmo_id:
            from users.models import Degmo
            try:
                data['degmo'] = Degmo.objects.get(id=degmo_id)
            except Degmo.DoesNotExist:
                raise serializers.ValidationError({'degmo_id': 'Invalid Degmo ID'})

        if magaalo_id:
            from users.models import Magaalo
            try:
                data['magaalo'] = Magaalo.objects.get(id=magaalo_id)
            except Magaalo.DoesNotExist:
                raise serializers.ValidationError({'magaalo_id': 'Invalid Magaalo ID'})

        if category_id:
            try:
                data['category'] = PropertyCategory.objects.get(id=category_id)
            except PropertyCategory.DoesNotExist:
                raise serializers.ValidationError({'category_id': 'Invalid Category ID'})
        elif property_category:
            category = PropertyCategory.objects.filter(
                Q(slug__iexact=property_category) |
                Q(name__iexact=property_category) |
                Q(name_so__iexact=property_category)
            ).first()
            if category:
                data['category'] = category
            else:
                raise serializers.ValidationError({'property_category': 'Invalid property category'})

        if subtype_id:
            try:
                data['subtype'] = PropertySubtype.objects.get(id=subtype_id)
            except PropertySubtype.DoesNotExist:
                raise serializers.ValidationError({'subtype_id': 'Invalid Subtype ID'})

        state = data.get('state')
        degmo = data.get('degmo')
        magaalo = data.get('magaalo')
        category = data.get('category')
        subtype = data.get('subtype')

        if degmo and state and degmo.state_id != state.id:
            raise serializers.ValidationError({'degmo_id': 'Degmo does not belong to selected state'})

        if magaalo and degmo and magaalo.degmo_id != degmo.id:
            raise serializers.ValidationError({'magaalo_id': 'Magaalo does not belong to selected degmo'})

        if magaalo and state and magaalo.degmo.state_id != state.id:
            raise serializers.ValidationError({'magaalo_id': 'Magaalo does not belong to selected state'})

        if subtype and category and subtype.category_id != category.id:
            raise serializers.ValidationError({'subtype_id': 'Subtype does not belong to selected category'})

        data.pop('state_id', None)
        data.pop('degmo_id', None)
        data.pop('magaalo_id', None)
        data.pop('category_id', None)
        data.pop('subtype_id', None)
        data.pop('property_category', None)

        return data
