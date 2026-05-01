from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models import User, Profile
from io import BytesIO
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def create_test_image(name='test.jpg'):
    """Create a temporary test image"""
    image = Image.new('RGB', (100, 100), 'white')
    image_io = BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    return SimpleUploadedFile(name, image_io.read(), content_type='image/jpeg')


class UserModelTests(TestCase):
    """Test cases for User and Profile models"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_agent=False
        )

    def test_user_creation(self):
        """Test that user is created successfully"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertFalse(self.user.is_agent)
        self.assertTrue(self.user.is_active)

    def test_profile_auto_created(self):
        """Test that profile is auto-created when user is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_agent_user_creation(self):
        """Test creating an agent user"""
        agent = User.objects.create_user(
            username='agentuser',
            email='agent@example.com',
            password='agentpass123',
            is_agent=True
        )
        self.assertTrue(agent.is_agent)


class AgentAPITests(APITestCase):
    """Test cases for Agent API endpoints"""

    def setUp(self):
        self.client = APIClient()

        self.verified_agent = User.objects.create_user(
            username='verifiedagent',
            email='verified@example.com',
            password='agentpass123',
            is_agent=True
        )
        self.verified_agent.profile.is_verified = True
        self.verified_agent.profile.save()

        self.unverified_agent = User.objects.create_user(
            username='unverifiedagent',
            email='unverified@example.com',
            password='agentpass123',
            is_agent=True
        )

        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='userpass123',
            is_agent=False
        )

    def test_get_agents_list(self):
        """Test getting list of verified agents"""
        response = self.client.get('/api/agents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'verifiedagent')

    def test_get_my_profile_authenticated(self):
        """Test getting own profile when authenticated"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/profile/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], self.regular_user.profile.full_name)

    def test_get_my_profile_unauthenticated(self):
        """Test that unauthenticated users cannot access profile"""
        response = self.client.get('/api/profile/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Test updating profile information"""
        self.client.force_authenticate(user=self.regular_user)
        data = {
            'full_name': 'Updated Name',
            'bio': 'Updated bio',
            'city': 'Mogadishu'
        }
        response = self.client.patch('/api/profile/me/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_user.profile.refresh_from_db()
        self.assertEqual(self.regular_user.profile.full_name, 'Updated Name')
        self.assertEqual(self.regular_user.profile.bio, 'Updated bio')


class AgentVerificationTests(APITestCase):
    """Test cases for agent verification workflow"""

    def setUp(self):
        self.client = APIClient()

        self.agent = User.objects.create_user(
            username='agentverify',
            email='agentverify@test.com',
            password='agentpass123',
            is_agent=True
        )
        self.agent.profile.full_name = 'Agent to Verify'
        self.agent.profile.save()

        self.admin = User.objects.create_user(
            username='adminuser',
            email='admin@test.com',
            password='adminpass123',
            is_staff=True
        )

    def test_upload_verification_document(self):
        """Test uploading verification document"""
        self.client.force_authenticate(user=self.agent)
        test_image = create_test_image()
        response = self.client.post(
            '/api/profile/verify/',
            {'nira_id_image': test_image},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.agent.profile.is_verified)
        self.assertTrue(self.agent.profile.verification_submitted)

    def test_get_verification_status(self):
        """Test getting verification status"""
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/api/profile/verify/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_verified', response.data)

    def test_get_pending_verifications_admin(self):
        """Test that admin can get pending verifications"""
        self.agent.profile.verification_submitted = True
        self.agent.profile.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/admin/pending-verifications/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_agent_approve(self):
        """Test admin approving agent verification"""
        self.agent.profile.verification_submitted = True
        self.agent.profile.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/admin/verify-agent/{self.agent.id}/',
            {'action': 'approve'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent.profile.refresh_from_db()
        self.assertTrue(self.agent.profile.is_verified)

    def test_verify_agent_reject(self):
        """Test admin rejecting agent verification"""
        self.agent.profile.verification_submitted = True
        self.agent.profile.save()

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f'/api/admin/verify-agent/{self.agent.id}/',
            {'action': 'reject', 'reason': 'Invalid documents'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent.profile.refresh_from_db()
        self.assertFalse(self.agent.profile.is_verified)
        self.assertEqual(self.agent.profile.rejection_reason, 'Invalid documents')

    def test_non_admin_cannot_verify(self):
        """Test that non-admin cannot verify agents"""
        other_agent = User.objects.create_user(
            username='otheragent',
            email='other@test.com',
            password='otherpass123',
            is_agent=True
        )

        self.client.force_authenticate(user=other_agent)
        response = self.client.post(
            f'/api/admin/verify-agent/{self.agent.id}/',
            {'action': 'approve'}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_upload_verification(self):
        """Test that customers cannot upload verification documents"""
        customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customerpass123',
            is_agent=False
        )

        self.client.force_authenticate(user=customer)
        response = self.client.post('/api/profile/verify/', {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MyListingsStatsTests(APITestCase):
    """Test cases for agent listings statistics"""

    def setUp(self):
        self.client = APIClient()
        self.agent = User.objects.create_user(
            username='statsagent',
            email='stats@test.com',
            password='agentpass123',
            is_agent=True
        )
        self.agent.profile.full_name = 'Stats Agent'
        self.agent.profile.save()

        from properties.models import Listing, PropertyCategory
        house_category = PropertyCategory.objects.create(name='House')
        apartment_category = PropertyCategory.objects.create(name='Apartment')

        Listing.objects.create(
            title='Active Listing',
            category=house_category,
            transaction_type='sale',
            price=100000,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Hodan',
            address='123 Stats St',
            area_sqm=100,
            description='Active',
            agent=self.agent,
            status='active',
            views_count=50
        )

        Listing.objects.create(
            title='Pending Listing',
            category=apartment_category,
            transaction_type='rent',
            price=500,
            state_text='Banaadir',
            magaalo_text='Mogadishu',
            degmo_text='Waberi',
            address='456 Pending Ave',
            area_sqm=80,
            description='Pending',
            agent=self.agent,
            status='pending'
        )

    def test_get_my_listings_stats(self):
        """Test getting own listings statistics"""
        self.client.force_authenticate(user=self.agent)
        response = self.client.get('/api/profile/my-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_listings', response.data)
        self.assertIn('active_listings', response.data)
        self.assertIn('total_views', response.data)

    def test_customer_cannot_get_stats(self):
        """Test that customers cannot access agent stats"""
        customer = User.objects.create_user(
            username='statscustomer',
            email='statscustomer@test.com',
            password='customerpass123',
            is_agent=False
        )

        self.client.force_authenticate(user=customer)
        response = self.client.get('/api/profile/my-stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
