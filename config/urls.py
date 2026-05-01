from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

from users import views as user_views
from users.admin import pending_site
from properties import views as prop_views
from chat import views as chat_views
from marketing import views as market_views
from features import views as feature_views

schema_view = get_schema_view(
    openapi.Info(
        title="eDalaal API",
        default_version='v1',
        description='Somali Real Estate Marketplace API',
        contact=openapi.Contact(email='support@edalaal.com'),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pending-verifications/', pending_site.urls),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

    # --- AUTHENTICATION (Djoser) ---
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/auth/register/', user_views.custom_register, name='custom_register'),

    # --- USERS & PROFILE ---
    path('api/agents/', user_views.get_agents),
    path('api/agents/<int:user_id>/', user_views.get_agent_detail),
    path('api/profile/me/', user_views.my_profile),
    path('api/profile/verify/', user_views.update_verification_doc),
    path('api/profile/verify/status/', user_views.get_verification_status),
    path('api/admin/pending-verifications/', user_views.get_pending_verifications),
    path('api/admin/verify-agent/<int:user_id>/', user_views.verify_agent),
    path('api/profile/my-stats/', user_views.my_listings_stats),
    
    # --- LOCATIONS (Dropdown data for forms) ---
    path('api/locations/states/', user_views.get_states, name='get_states'),
    path('api/locations/degmo/', user_views.get_degmo, name='get_degmo'),
    path('api/locations/magaalo/', user_views.get_magaalo, name='get_magaalo'),

    # --- PROPERTY TYPES ---
    path('api/properties/categories/', user_views.get_property_categories, name='get_property_categories'),
    path('api/properties/subtypes/', user_views.get_property_subtypes, name='get_property_subtypes'),

    # --- LISTINGS (Guryaha) ---
    path('api/listings/', prop_views.get_listings),
    path('api/listings/<int:pk>/', prop_views.get_listing_detail),
    path('api/listings/create/', prop_views.create_listing),
    path('api/listings/<int:pk>/update/', prop_views.update_listing),
    path('api/listings/<int:pk>/delete/', prop_views.delete_listing),
    path('api/listings/my-properties/', prop_views.my_listings),
    path('api/listings/search/', prop_views.search_listings),
    path('api/listings/categories/', prop_views.get_property_categories),
    path('api/listings/locations/', prop_views.get_locations),
    path('api/listings/<int:pk>/upload-images/', prop_views.upload_property_images),
    path('api/listings/<int:pk>/images/<int:image_id>/delete/', prop_views.delete_property_image),
    path('api/listings/<int:pk>/images/<int:image_id>/set-primary/', prop_views.set_primary_image),
    path('api/listings/<int:pk>/approve/', prop_views.approve_listing),
    path('api/listings/<int:pk>/mark-sold/', prop_views.mark_as_sold),
    
    # --- FAVORITES ---
    path('api/favorites/', prop_views.get_favorites),
    path('api/favorites/<int:pk>/add/', prop_views.add_favorite),
    path('api/favorites/<int:pk>/remove/', prop_views.remove_favorite),
    path('api/favorites/<int:pk>/check/', prop_views.check_favorite),

    # --- CHAT ---
    path('api/conversations/', chat_views.get_conversations),
    path('api/conversations/start/', chat_views.start_chat),
    path('api/conversations/<int:conversation_id>/', chat_views.get_conversation_detail),
    path('api/messages/', chat_views.chat_messages),
    path('api/test-notification/', chat_views.test_notification),

    # --- MARKETING ---
    path('api/announcements/', market_views.get_announcements),

    # --- ANALYTICS (Tirakoobka) ---
    path('api/analytics/', include('analytics.urls')),
    
    # --- NOTIFICATIONS ---
    path('api/notifications/', user_views.get_notifications),
    path('api/notifications/<int:notification_id>/read/', user_views.mark_notification_read),
    path('api/notifications/read-all/', user_views.mark_all_notifications_read),
    path('api/notifications/unread-count/', user_views.unread_notification_count),
    
    # --- PUSH NOTIFICATIONS ---
    path('api/device-tokens/register/', user_views.register_device_token),
    path('api/device-tokens/unregister/', user_views.unregister_device_token),
    
    # --- REVIEWS ---
    path('api/agents/<int:agent_id>/reviews/', user_views.agent_reviews),
    path('api/reviews/<int:review_id>/', user_views.update_delete_review),

    # --- FEATURE FLAGS ---
    path('api/features/', feature_views.feature_flags_all, name='feature_flags'),
]

# Always serve media files (for development and production)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)