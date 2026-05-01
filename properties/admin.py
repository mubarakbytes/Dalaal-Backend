from django.contrib import admin
from django.utils import timezone
from .models import Favorite, Listing, PropertyCategory, PropertyImage, PropertySubtype, PropertyView

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

class PropertySubtypeInline(admin.TabularInline):
    model = PropertySubtype
    extra = 1
    fields = ('name', 'name_so', 'sort_order', 'is_active')

# Custom actions for Listing
def approve_properties(modeladmin, request, queryset):
    """Ansaxi hantida (Approve properties)"""
    for listing in queryset:
        listing.status = 'active'
        listing.approved_by = request.user
        listing.approved_at = timezone.now()
        listing.save()
    modeladmin.message_user(request, f"{queryset.count()} property/properties approved!")
approve_properties.short_description = "✅ Ansaxi Hantida (Approve Properties)"

def reject_properties(modeladmin, request, queryset):
    """Diid hantida (Reject properties)"""
    queryset.update(status='rejected', approved_by=None, approved_at=None)
    modeladmin.message_user(request, f"{queryset.count()} property/properties rejected!")
reject_properties.short_description = "❌ Diid Hantida (Reject Properties)"

class PropertyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_so', 'icon', 'sort_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_so')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PropertySubtypeInline]
    fieldsets = (
        ('Category Info', {
            'fields': ('name', 'name_so', 'slug', 'icon', 'sort_order', 'is_active')
        }),
    )

class PropertySubtypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'name_so', 'sort_order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    list_select_related = ('category',)

class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'agent', 'get_category', 'get_subtype', 'transaction_type', 'price', 'status', 'get_state', 'views_count', 'created_at')
    list_filter = ('status', 'category', 'transaction_type', 'state', 'degmo', 'agent__profile__is_verified')
    search_fields = ('title', 'description', 'address', 'agent__username')
    list_editable = ('status',)
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyImageInline]
    actions = [approve_properties, reject_properties]
    readonly_fields = ('views_count', 'approved_by', 'approved_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('agent', 'title', 'slug', 'category', 'subtype', 'transaction_type', 'price')
        }),
        ('Location (Goobta)', {
            'fields': ('state', 'degmo', 'magaalo', 'address', 'state_text', 'degmo_text', 'magaalo_text', 'latitude', 'longitude')
        }),
        ('Details (Faahfaahinta)', {
            'fields': ('area_width', 'area_length', 'area_sqm', 'description', 'features', 'main_photo')
        }),
        ('House/Apartment Features', {
            'fields': ('bedrooms', 'bathrooms', 'living_rooms', 'kitchens', 'parking_spots', 'floor', 'year_built', 'is_furnished'),
            'classes': ('collapse',),
        }),
        ('Warehouse Features', {
            'fields': ('height_meters', 'has_loading_dock', 'has_corridor_access'),
            'classes': ('collapse',),
        }),
        ('Land Features', {
            'fields': ('land_type',),
            'classes': ('collapse',),
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Analytics', {
            'fields': ('views_count', 'created_at', 'updated_at')
        }),
    )
    
    def get_category(self, obj):
        return obj.get_category_display()
    get_category.short_description = 'Category'
    
    def get_subtype(self, obj):
        return obj.get_subtype_display()
    get_subtype.short_description = 'Subtype'
    
    def get_state(self, obj):
        return obj.get_state_display()
    get_state.short_description = 'State'

class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'is_primary', 'order', 'uploaded_at')
    list_filter = ('is_primary',)

class PropertyViewAdmin(admin.ModelAdmin):
    list_display = ('listing', 'viewer', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    readonly_fields = ('listing', 'viewer', 'ip_address', 'viewed_at')

class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'listing__title')
    readonly_fields = ('created_at',)
    list_select_related = ('user', 'listing')

admin.site.register(PropertyCategory, PropertyCategoryAdmin)
admin.site.register(PropertySubtype, PropertySubtypeAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(PropertyImage, PropertyImageAdmin)
admin.site.register(PropertyView, PropertyViewAdmin)
admin.site.register(Favorite, FavoriteAdmin)
