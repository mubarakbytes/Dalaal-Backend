from django.core.management.base import BaseCommand
from features.models import FeatureFlag


class Command(BaseCommand):
    help = 'Seed default feature flags for the application'

    def handle(self, *args, **options):
        features = [
            # Filters (category: filters)
            {'key': 'enable_search', 'name': 'Search', 'description': 'Text search for properties', 'category': 'filters', 'order': 1},
            {'key': 'enable_state_filter', 'name': 'State Filter', 'description': 'Filter by state/region', 'category': 'filters', 'order': 2},
            {'key': 'enable_district_filter', 'name': 'District Filter', 'description': 'Filter by district (degmo)', 'category': 'filters', 'order': 3},
            {'key': 'enable_village_filter', 'name': 'Village Filter', 'description': 'Filter by xaafad/village', 'category': 'filters', 'order': 4},
            {'key': 'enable_type_filter', 'name': 'Property Type Filter', 'description': 'Filter by property category', 'category': 'filters', 'order': 5},
            {'key': 'enable_subtype_filter', 'name': 'Subtype Filter', 'description': 'Filter by property subtype', 'category': 'filters', 'order': 6},
            {'key': 'enable_listing_type_filter', 'name': 'Listing Type Filter', 'description': 'Filter sale vs rent', 'category': 'filters', 'order': 7},
            {'key': 'enable_bedrooms_filter', 'name': 'Bedrooms Filter', 'description': 'Filter by bedroom count', 'category': 'filters', 'order': 8},
            {'key': 'enable_price_filter', 'name': 'Price Range Filter', 'description': 'Min/max price filtering', 'category': 'filters', 'order': 9},
            {'key': 'enable_sorting', 'name': 'Sorting Options', 'description': 'Sort by newest/price', 'category': 'filters', 'order': 10},
            {'key': 'enable_mobile_filters', 'name': 'Mobile Filter Sheet', 'description': 'Full-screen mobile filter modal', 'category': 'filters', 'order': 11},
            {'key': 'enable_results_count', 'name': 'Results Count', 'description': 'Display properties found count', 'category': 'filters', 'order': 12},

            # Property Detail (category: property_detail)
            {'key': 'enable_property_map', 'name': 'Interactive Map', 'description': 'Leaflet map showing property location', 'category': 'property_detail', 'order': 1},
            {'key': 'enable_photo_gallery', 'name': 'Image Gallery', 'description': 'Grid/mobile carousel photo gallery', 'category': 'property_detail', 'order': 2},
            {'key': 'enable_fullscreen_gallery', 'name': 'Fullscreen Photos', 'description': 'Full-screen photo viewer with swipe', 'category': 'property_detail', 'order': 3},
            {'key': 'enable_chat_feature', 'name': 'Chat with Agent', 'description': 'Real-time chat contact with agent', 'category': 'property_detail', 'order': 4},
            {'key': 'enable_call_feature', 'name': 'Call Agent Button', 'description': 'Direct phone call to agent', 'category': 'property_detail', 'order': 5},
            {'key': 'enable_favorites', 'name': 'Favorites Button', 'description': 'Save/remove property to favorites', 'category': 'property_detail', 'order': 6},
            {'key': 'enable_share_feature', 'name': 'Share Button', 'description': 'Share property via native share or clipboard', 'category': 'property_detail', 'order': 7},
            {'key': 'enable_verification_badge', 'name': 'Verified Badge', 'description': 'Property verification status indicator', 'category': 'property_detail', 'order': 8},
            {'key': 'enable_reviews', 'name': 'Reviews Section', 'description': 'Agent reviews display and submission', 'category': 'property_detail', 'order': 9},
            {'key': 'enable_agent_ratings', 'name': 'Rating Display', 'description': 'Agent rating stars display', 'category': 'property_detail', 'order': 10},
            {'key': 'enable_safety_tips', 'name': 'Safety Tip Warning', 'description': 'Fraud prevention safety tip', 'category': 'property_detail', 'order': 11},
            {'key': 'enable_directions_link', 'name': 'Directions Link', 'description': 'Google Maps directions link', 'category': 'property_detail', 'order': 12},

            # Broker Create (category: broker_create)
            {'key': 'enable_main_photo', 'name': 'Main Photo Upload', 'description': 'Primary property photo', 'category': 'broker_create', 'order': 1},
            {'key': 'enable_multiple_photos', 'name': 'Additional Photos', 'description': 'Multiple photos upload', 'category': 'broker_create', 'order': 2},
            {'key': 'enable_title_field', 'name': 'Title Input', 'description': 'Property title field', 'category': 'broker_create', 'order': 3},
            {'key': 'enable_category', 'name': 'Category Selection', 'description': 'Property category dropdown', 'category': 'broker_create', 'order': 4},
            {'key': 'enable_subtype', 'name': 'Subtype Selection', 'description': 'Property subtype dropdown', 'category': 'broker_create', 'order': 5},
            {'key': 'enable_transaction_type', 'name': 'Transaction Type', 'description': 'Sale vs rent selector', 'category': 'broker_create', 'order': 6},
            {'key': 'enable_price', 'name': 'Price Input', 'description': 'Price field', 'category': 'broker_create', 'order': 7},
            {'key': 'enable_rent_period', 'name': 'Rent Period', 'description': 'Monthly/yearly for rent', 'category': 'broker_create', 'order': 8},
            {'key': 'enable_state_selection', 'name': 'State Location', 'description': 'State selection', 'category': 'broker_create', 'order': 9},
            {'key': 'enable_district', 'name': 'District Location', 'description': 'District selection', 'category': 'broker_create', 'order': 10},
            {'key': 'enable_village', 'name': 'Village Location', 'description': 'Xaafad/village selection', 'category': 'broker_create', 'order': 11},
            {'key': 'enable_address', 'name': 'Address Input', 'description': 'Street address', 'category': 'broker_create', 'order': 12},
            {'key': 'enable_location_map', 'name': 'Interactive Map', 'description': 'Map picker for coordinates', 'category': 'broker_create', 'order': 13},
            {'key': 'enable_area_calc', 'name': 'Area Calculation', 'description': 'Width × length = area', 'category': 'broker_create', 'order': 14},
            {'key': 'enable_bedrooms_input', 'name': 'Bedrooms Input', 'description': 'Bedroom count', 'category': 'broker_create', 'order': 15},
            {'key': 'enable_bathrooms_input', 'name': 'Bathrooms Input', 'description': 'Bathroom count', 'category': 'broker_create', 'order': 16},
            {'key': 'enable_living_rooms', 'name': 'Living Rooms Input', 'description': 'Living room count', 'category': 'broker_create', 'order': 17},
            {'key': 'enable_kitchens', 'name': 'Kitchens Input', 'description': 'Kitchen count', 'category': 'broker_create', 'order': 18},
            {'key': 'enable_parking', 'name': 'Parking Input', 'description': 'Parking spots', 'category': 'broker_create', 'order': 19},
            {'key': 'enable_floor', 'name': 'Floor Input', 'description': 'Floor number', 'category': 'broker_create', 'order': 20},
            {'key': 'enable_year_built', 'name': 'Year Built Input', 'description': 'Construction year', 'category': 'broker_create', 'order': 21},
            {'key': 'enable_furnished', 'name': 'Furnished Toggle', 'description': 'Furnished checkbox', 'category': 'broker_create', 'order': 22},
            {'key': 'enable_height', 'name': 'Warehouse Height', 'description': 'Warehouse height field', 'category': 'broker_create', 'order': 23},
            {'key': 'enable_loading_dock', 'name': 'Loading Dock', 'description': 'Loading dock checkbox', 'category': 'broker_create', 'order': 24},
            {'key': 'enable_corridor', 'name': 'Corridor Access', 'description': 'Corridor access checkbox', 'category': 'broker_create', 'order': 25},
            {'key': 'enable_land_type', 'name': 'Land Type', 'description': 'Land type dropdown', 'category': 'broker_create', 'order': 26},
            {'key': 'enable_description', 'name': 'Description', 'description': 'Property description', 'category': 'broker_create', 'order': 27},
            {'key': 'enable_features', 'name': 'Features List', 'description': 'Amenities/features text area', 'category': 'broker_create', 'order': 28},

            # Landing Page (category: landing_page)
            {'key': 'enable_hero_search', 'name': 'Hero Search Section', 'description': 'Main search box', 'category': 'landing_page', 'order': 1},
            {'key': 'enable_transaction_tabs', 'name': 'Transaction Type Tabs', 'description': 'Sale/rent tabs', 'category': 'landing_page', 'order': 2},
            {'key': 'enable_featured_listings', 'name': 'Featured Properties', 'description': 'Featured listings grid', 'category': 'landing_page', 'order': 3},
            {'key': 'enable_how_it_works', 'name': 'How It Works Section', 'description': 'Site explanation', 'category': 'landing_page', 'order': 4},
            {'key': 'enable_stats_section', 'name': 'Statistics Section', 'description': 'Platform stats display', 'category': 'landing_page', 'order': 5},
            {'key': 'enable_cta_section', 'name': 'CTA Section', 'description': 'Call-to-action area', 'category': 'landing_page', 'order': 6},
            {'key': 'enable_footer', 'name': 'Footer', 'description': 'Site footer links', 'category': 'landing_page', 'order': 7},
            {'key': 'enable_quick_stats', 'name': 'Quick Stats', 'description': 'Property/agent counts', 'category': 'landing_page', 'order': 8},

            # Messaging (category: messaging)
            {'key': 'enable_conversations', 'name': 'Conversations List', 'description': 'Chat list sidebar', 'category': 'messaging', 'order': 1},
            {'key': 'enable_messages', 'name': 'Messages Display', 'description': 'Message bubbles', 'category': 'messaging', 'order': 2},
            {'key': 'enable_chat_property_card', 'name': 'Property Card in Chat', 'description': 'Property preview in chat', 'category': 'messaging', 'order': 3},
            {'key': 'enable_send_message', 'name': 'Message Input', 'description': 'Send message field', 'category': 'messaging', 'order': 4},
            {'key': 'enable_system_messages', 'name': 'System Messages', 'description': 'System notifications', 'category': 'messaging', 'order': 5},

            # Global (category: global)
            {'key': 'enable_header', 'name': 'Top Header', 'description': 'Navigation header', 'category': 'global', 'order': 1},
            {'key': 'enable_bottom_nav', 'name': 'Bottom Navigation', 'description': 'Mobile bottom nav', 'category': 'global', 'order': 2},
            {'key': 'enable_announcements', 'name': 'Launch Announcement', 'description': 'Welcome popup', 'category': 'global', 'order': 3},
            {'key': 'enable_push_notifications', 'name': 'Push Notifications', 'description': 'Push notification init', 'category': 'global', 'order': 4},
            {'key': 'enable_local_notifications', 'name': 'Local Notifications', 'description': 'Test notification feature', 'category': 'global', 'order': 5},
        ]

        created_count = 0
        updated_count = 0

        for feature_data in features:
            feature, created = FeatureFlag.objects.update_or_create(
                key=feature_data['key'],
                defaults={
                    'name': feature_data['name'],
                    'description': feature_data['description'],
                    'category': feature_data['category'],
                    'order': feature_data['order'],
                    'is_enabled': True,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {created_count} new features, updated {updated_count} existing features.'
        ))