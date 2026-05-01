from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models import User
from properties.models import Listing, PropertyCategory, PropertyImage, PropertyView
from chat.models import Conversation, Message
from io import BytesIO
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def create_test_image(name='test.jpg'):
    """Create a temporary test image for upload tests"""
    image = Image.new('RGB', (100, 100), 'white')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile(name, image_io.read(), content_type='image/jpeg')


class ListingModelTests(TestCase):
    """Test cases for Listing model"""

    def setUp(self):
        self.agent = User.objects.create_user(
            username='testagent',
            email='agent@test.com',
            password='testpass123',
            is_agent=True
        )
        self.house_category = PropertyCategory.objects.create(name='House')
        self.land_category = PropertyCategory.objects.create(name='Land')
        self.listing = Listing.objects.create(
            title='Test Property',
            category=self.house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='Test Address',
            bedrooms=3,
            bathrooms=2,
            area_sqm=150,
            description='Test description',
            agent=self.agent,
            status='active'
        )

    def test_listing_creation(self):
        """Test that listing is created correctly"""
        self.assertEqual(self.listing.title, 'Test Property')
        self.assertEqual(self.listing.price, 100000)
        self.assertEqual(self.listing.status, 'active')
        self.assertEqual(self.listing.agent, self.agent)

    def test_listing_str_method(self):
        """Test listing string representation"""
        self.assertIn('Test Property', str(self.listing))

    def test_listing_auto_slug(self):
        """Test that slug is created"""
        self.assertIsNotNone(self.listing.slug)

    def test_listing_ordering(self):
        """Test default ordering"""
        listing2 = Listing.objects.create(
            title='Second Property',
            category=self.land_category,
            transaction_type='sale',
            price=50000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Wadajir',
            address='Another Address',
            area_sqm=200,
            description='Another',
            agent=self.agent,
            status='active'
        )
        listings = list(Listing.objects.all())
        self.assertEqual(listings[0], listing2)


class ListingAPITests(APITestCase):
    """Test cases for Listing API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.house_category = PropertyCategory.objects.create(name='House')
        self.apartment_category = PropertyCategory.objects.create(name='Apartment')

        self.agent = User.objects.create_user(
            username='testagent',
            email='agent@test.com',
            password='testpass123',
            is_agent=True
        )
        self.agent.profile.is_verified = True
        self.agent.profile.save()

        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            is_agent=False
        )

        self.active_listing = Listing.objects.create(
            title='Active Property',
            category=self.house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='Test Address',
            bedrooms=3,
            bathrooms=2,
            area_sqm=150,
            description='Test description',
            agent=self.agent,
            status='active'
        )

        self.pending_listing = Listing.objects.create(
            title='Pending Property',
            category=self.apartment_category,
            transaction_type='rent',
            price=500,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Waberi',
            address='Another Address',
            bedrooms=2,
            bathrooms=1,
            area_sqm=80,
            description='Pending description',
            agent=self.agent,
            status='pending'
        )

    def test_get_all_listings(self):
        """Test getting all active listings"""
        response = self.client.get('/api/listings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Active Property')

    def test_get_single_listing(self):
        """Test getting a single listing"""
        response = self.client.get(f'/api/listings/{self.active_listing.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Active Property')
        self.active_listing.refresh_from_db()
        self.assertEqual(self.active_listing.views_count, 1)

    def test_create_listing_as_verified_agent(self):
        """Test creating listing as verified agent"""
        self.client.force_authenticate(user=self.agent)
        data = {
            'title': 'New Property',
            'category_id': self.house_category.id,
            'transaction_type': 'sale',
            'price': 150000,
            'state_text': 'Banaadir',
            'magaalo_text': 'Mogadishu',
            'degmo_text': 'Hodan',
            'address': 'New Address',
            'bedrooms': 4,
            'bathrooms': 3,
            'area_sqm': 200,
            'description': 'New property description'
        }
        response = self.client.post('/api/listings/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'active')
        self.assertTrue(response.data['auto_approved'])

    def test_create_listing_as_customer(self):
        """Test that customers cannot create listings"""
        self.client.force_authenticate(user=self.customer)
        data = {
            'title': 'New Property',
            'category_id': self.house_category.id,
            'transaction_type': 'sale',
            'price': 150000,
            'state_text': 'Banaadir',
            'magaalo_text': 'Mogadishu',
            'degmo_text': 'Hodan',
            'address': 'New Address',
            'bedrooms': 4,
            'bathrooms': 3,
            'area_sqm': 200,
            'description': 'New property description'
        }
        response = self.client.post('/api/listings/create/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_listing(self):
        """Test updating own listing"""
        self.client.force_authenticate(user=self.agent)
        data = {'price': 120000}
        response = self.client.patch(f'/api/listings/{self.active_listing.id}/update/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_listing.refresh_from_db()
        self.assertEqual(self.active_listing.price, 120000)

    def test_delete_own_listing(self):
        """Test deleting own listing"""
        self.client.force_authenticate(user=self.agent)
        response = self.client.delete(f'/api/listings/{self.active_listing.id}/delete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Listing.objects.filter(id=self.active_listing.id).exists())

    def test_get_my_properties(self):
        """Test getting agent's own properties"""
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/api/listings/my-properties/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class SearchAndFilterTests(APITestCase):
    """Test cases for search and filter functionality"""

    def setUp(self):
        self.client = APIClient()
        self.house_category = PropertyCategory.objects.create(name='House')
        self.apartment_category = PropertyCategory.objects.create(name='Apartment')
        self.land_category = PropertyCategory.objects.create(name='Land')
        self.agent = User.objects.create_user(
            username='searchagent',
            email='search@test.com',
            password='testpass123',
            is_agent=True
        )
        self.agent.profile.is_verified = True
        self.agent.profile.save()

        Listing.objects.create(
            title='Beautiful House in Hodan',
            category=self.house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='123 Main St',
            bedrooms=3,
            bathrooms=2,
            area_sqm=150,
            description='A beautiful house with ocean view',
            agent=self.agent,
            status='active'
        )

        Listing.objects.create(
            title='Luxury Apartment',
            category=self.apartment_category,
            transaction_type='rent',
            price=500,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Waberi',
            address='456 High St',
            bedrooms=2,
            bathrooms=1,
            area_sqm=80,
            description='Modern apartment in city center',
            agent=self.agent,
            status='active'
        )

        Listing.objects.create(
            title='Commercial Land',
            category=self.land_category,
            transaction_type='sale',
            price=50000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hamarweyne',
            address='789 Commercial Ave',
            area_sqm=500,
            description='Prime commercial land',
            agent=self.agent,
            status='active'
        )

    def test_search_by_title(self):
        """Test searching by title"""
        response = self.client.get('/api/listings/search/', {'search': 'House'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_search_by_description(self):
        """Test searching by description"""
        response = self.client.get('/api/listings/search/', {'search': 'ocean view'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_filter_by_category(self):
        """Test filtering by property category"""
        response = self.client.get('/api/listings/search/', {'category': 'house'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_filter_by_transaction_type(self):
        """Test filtering by transaction type"""
        response = self.client.get('/api/listings/search/', {'transaction_type': 'rent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_filter_by_price_range(self):
        """Test filtering by price range"""
        response = self.client.get('/api/listings/search/', {'price_min': '40000', 'price_max': '150000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 2)

    def test_filter_by_city(self):
        """Test filtering by city"""
        response = self.client.get('/api/listings/search/', {'city': 'Mogadishu'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 3)

    def test_filter_by_bedrooms(self):
        """Test filtering by minimum bedrooms"""
        response = self.client.get('/api/listings/search/', {'bedrooms': '3'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_combined_filters(self):
        """Test combining multiple filters"""
        response = self.client.get('/api/listings/search/', {
            'category': 'house',
            'transaction_type': 'sale',
            'price_max': '200000',
            'bedrooms': '2'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_count'], 1)

    def test_pagination(self):
        """Test pagination"""
        response = self.client.get('/api/listings/search/', {'page': 1, 'page_size': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['page'], 1)
        self.assertEqual(response.data['page_size'], 2)
        self.assertEqual(response.data['total_pages'], 2)

    def test_ordering_by_price(self):
        """Test ordering by price ascending"""
        response = self.client.get('/api/listings/search/', {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(float(results[0]['price']), 500)

    def test_ordering_by_created_at(self):
        """Test ordering by creation date"""
        response = self.client.get('/api/listings/search/', {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_categories(self):
        """Test getting categories with counts"""
        response = self.client.get('/api/listings/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_get_locations(self):
        """Test getting locations for filters"""
        response = self.client.get('/api/listings/locations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('states', response.data)
        self.assertIn('cities', response.data)


class ImageUploadTests(APITestCase):
    """Test cases for image upload functionality"""

    def setUp(self):
        self.client = APIClient()
        self.house_category = PropertyCategory.objects.create(name='House')
        self.agent = User.objects.create_user(
            username='imageagent',
            email='image@test.com',
            password='testpass123',
            is_agent=True
        )
        self.agent.profile.is_verified = True
        self.agent.profile.save()

        self.listing = Listing.objects.create(
            title='Property with Images',
            category=self.house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='123 Image St',
            bedrooms=3,
            bathrooms=2,
            area_sqm=150,
            description='Property for image tests',
            agent=self.agent,
            status='active'
        )

    def test_upload_images(self):
        """Test uploading property images"""
        self.client.force_authenticate(user=self.agent)
        test_image = create_test_image()
        response = self.client.post(
            f'/api/listings/{self.listing.id}/upload-images/',
            {'images': [test_image]},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['images']), 1)

    def test_upload_images_unauthorized(self):
        """Test that unauthorized users cannot upload images"""
        test_image = create_test_image()
        response = self.client.post(
            f'/api/listings/{self.listing.id}/upload-images/',
            {'images': [test_image]},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_image(self):
        """Test deleting a property image"""
        self.client.force_authenticate(user=self.agent)
        image = PropertyImage.objects.create(
            listing=self.listing,
            image=create_test_image()
        )
        response = self.client.delete(
            f'/api/listings/{self.listing.id}/images/{image.id}/delete/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(PropertyImage.objects.filter(id=image.id).exists())

    def test_set_primary_image(self):
        """Test setting primary image"""
        self.client.force_authenticate(user=self.agent)
        image1 = PropertyImage.objects.create(listing=self.listing, image=create_test_image(), is_primary=False)
        image2 = PropertyImage.objects.create(listing=self.listing, image=create_test_image(), is_primary=False)
        response = self.client.post(
            f'/api/listings/{self.listing.id}/images/{image2.id}/set-primary/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        image1.refresh_from_db()
        image2.refresh_from_db()
        self.assertFalse(image1.is_primary)
        self.assertTrue(image2.is_primary)


class PropertyViewTests(APITestCase):
    """Test cases for property view tracking"""

    def setUp(self):
        self.house_category = PropertyCategory.objects.create(name='House')
        self.agent = User.objects.create_user(
            username='viewagent',
            email='view@test.com',
            password='testpass123',
            is_agent=True
        )
        self.listing = Listing.objects.create(
            title='Tracked Property',
            category=self.house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='123 Track St',
            area_sqm=100,
            description='Test',
            agent=self.agent,
            status='active'
        )

    def test_view_count_increments(self):
        """Test that viewing a listing increments the view count"""
        initial_views = self.listing.views_count
        response = self.client.get(f'/api/listings/{self.listing.id}/')
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.views_count, initial_views + 1)

    def test_property_view_created(self):
        """Test that PropertyView record is created"""
        response = self.client.get(f'/api/listings/{self.listing.id}/')
        self.assertEqual(PropertyView.objects.filter(listing=self.listing).count(), 1)
