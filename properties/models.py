from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.utils.text import slugify
import uuid

class PropertyCategory(models.Model):
    """Categories like House, Land, Apartment, Warehouse"""
    name = models.CharField(max_length=50, unique=True)
    name_so = models.CharField(max_length=50, blank=True, help_text="Somali name")
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Material icon name")
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Property Category'
        verbose_name_plural = 'Property Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PropertySubtype(models.Model):
    """Subtypes linked to categories - e.g., for Land: commercial, residential, industrial"""
    category = models.ForeignKey(PropertyCategory, on_delete=models.CASCADE, related_name='subtypes')
    name = models.CharField(max_length=100)
    name_so = models.CharField(max_length=100, blank=True, help_text="Somali name")
    slug = models.SlugField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['category', 'name']
        ordering = ['sort_order', 'name']
        verbose_name = 'Property Subtype'
        verbose_name_plural = 'Property Subtypes'

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Listing(models.Model):
    TRANSACTION_TYPES = (
        ('sale', 'Iibka / For Sale'),
        ('rent', 'Kiro / For Rent'),
    )

    STATUS_CHOICES = (
        ('draft', 'Qabyo / Draft'),
        ('pending', 'Sugitaan / Pending Review'),
        ('active', 'Firfircoon / Active'),
        ('rejected', 'La Diiday / Rejected'),
        ('sold', 'La Iibiyay / Sold/Rented'),
    )

    LAND_TYPES = (
        ('residential', 'Gurigeliyada / Residential'),
        ('commercial', 'Ganacsi / Commercial'),
        ('agricultural', 'Beerasho / Agricultural'),
        ('industrial', 'Tignolaaysan / Industrial'),
        ('mixed', 'Mixed Use'),
    )

    agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(PropertyCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    subtype = models.ForeignKey(PropertySubtype, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='sale')
    price = models.DecimalField(max_digits=12, decimal_places=2)

    # Location fields - using foreign keys to structured location table
    state = models.ForeignKey('users.State', on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    degmo = models.ForeignKey('users.Degmo', on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    magaalo = models.ForeignKey('users.Magaalo', on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    
    # Keep text fields for display purposes
    state_text = models.CharField(max_length=50, blank=True, default='')
    degmo_text = models.CharField(max_length=50, blank=True, default='')
    magaalo_text = models.CharField(max_length=50, blank=True, default='')
    address = models.CharField(max_length=255)

    # Location coordinates for map
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Common field
    area_sqm = models.IntegerField()
    area_width = models.IntegerField(null=True, blank=True, help_text="Width in meters")
    area_length = models.IntegerField(null=True, blank=True, help_text="Length in meters")
    description = models.TextField()
    features = models.TextField(blank=True, default='', max_length=500, help_text="Enter features as bullet points (one per line starting with -)")

    # Price period for rent listings
    PRICE_PERIODS = (
        ('month', 'Bishii / Monthly'),
        ('year', 'Sanadkii / Yearly'),
    )
    price_period = models.CharField(max_length=10, choices=PRICE_PERIODS, blank=True, default='')

    # House/Apartment features
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    living_rooms = models.IntegerField(null=True, blank=True, help_text="Qolka Fadhiga")
    kitchens = models.IntegerField(null=True, blank=True, help_text="Musqul")
    parking_spots = models.IntegerField(null=True, blank=True, help_text="Baarkin / Parking")
    floor = models.IntegerField(null=True, blank=True, help_text="Dabaqa / Floor")
    year_built = models.IntegerField(null=True, blank=True, help_text="Sanadka la dhisay")
    is_furnished = models.BooleanField(default=False, help_text="Furnished / Qalalan")

    # Warehouse features
    height_meters = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Dhererka (meters)")
    has_loading_dock = models.BooleanField(default=False, help_text="Dayax / Loading Dock")
    has_corridor_access = models.BooleanField(default=False, help_text="Coridor / Corridor Access")

    # Land features
    land_type = models.CharField(max_length=20, choices=LAND_TYPES, blank=True, default='')

    # Photos
    main_photo = models.ImageField(upload_to='listings/%Y/%m/', blank=True, default='')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_listings')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    views_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            counter = 1
            while Listing.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{base_slug}-{uuid.uuid4().hex[:8]}'
            self.slug = unique_slug
        super().save(*args, **kwargs)
    
    def get_state_display(self):
        if self.state:
            return self.state.name
        return self.state_text or 'N/A'
    
    def get_degmo_display(self):
        if self.degmo:
            state_name = self.state.name if self.state else (self.degmo.state.name if self.degmo.state else '')
            return f"{self.degmo.name}{', ' + state_name if state_name else ''}"
        return self.degmo_text or 'N/A'
    
    def get_magaalo_display(self):
        if self.magaalo:
            state_name = ''
            if self.degmo and self.degmo.state:
                state_name = self.degmo.state.name
            elif self.state:
                state_name = self.state.name
            return f"{self.magaalo.name}{', ' + state_name if state_name else ''}"
        return self.magaalo_text or 'N/A'
    
    def get_category_display(self):
        return self.category.name if self.category else 'N/A'
    
    def get_subtype_display(self):
        return self.subtype.name if self.subtype else 'N/A'
    
    def get_price_period_display(self):
        if self.price_period:
            return dict(self.PRICE_PERIODS).get(self.price_period, self.price_period)
        return ''

class PropertyImage(models.Model):
    """Sawirrada Hantida - Multiple images per listing"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/%Y/%m/gallery/')
    is_primary = models.BooleanField(default=False)  # Sawirka ugu muhiimsan
    order = models.IntegerField(default=0)  # Tartiibtaada sawirrada
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.listing.title}"


class PropertyView(models.Model):
    """Daawashada Hantida - Track property views for analytics"""
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='property_views')
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.listing.title} at {self.viewed_at}"
    
    def get_category_display(self):
        return self.category.name if self.category else 'N/A'
    
    def get_subtype_display(self):
        return self.subtype.name if self.subtype else 'N/A'


class Favorite(models.Model):
    """Saved properties / Favorites"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'listing']
    
    def __str__(self):
        return f"{self.user.username} favorited {self.listing.title}"