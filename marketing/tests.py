from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Announcement


class AnnouncementAPITests(APITestCase):
    def setUp(self):
        self.now = timezone.now()
        user_model = get_user_model()
        self.customer = user_model.objects.create_user(
            username='announcement_customer',
            password='testpass123',
            is_agent=False,
        )
        self.agent = user_model.objects.create_user(
            username='announcement_agent',
            password='testpass123',
            is_agent=True,
        )

    def _create_announcement(self, **kwargs):
        data = {
            'title': kwargs.pop('title', 'Announcement'),
            'content': kwargs.pop('content', 'Content'),
            'target_audience': kwargs.pop('target_audience', 'all'),
            'is_active': kwargs.pop('is_active', True),
            'priority': kwargs.pop('priority', 1),
            'start_date': kwargs.pop('start_date', self.now - timedelta(hours=1)),
            'end_date': kwargs.pop('end_date', self.now + timedelta(days=1)),
        }
        data.update(kwargs)
        return Announcement.objects.create(**data)

    def test_returns_only_active_announcements_with_valid_dates(self):
        live = self._create_announcement(title='Live')
        self._create_announcement(title='Inactive', is_active=False)
        self._create_announcement(title='Future', start_date=self.now + timedelta(hours=1))
        self._create_announcement(title='Expired', end_date=self.now - timedelta(minutes=1))

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], live.id)
        self.assertEqual(response.data[0]['title'], 'Live')

    def test_includes_active_announcements_without_end_date(self):
        no_end = self._create_announcement(title='No End', end_date=None)

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [item['id'] for item in response.data]
        self.assertIn(no_end.id, ids)

    def test_orders_by_priority_then_latest_start_date(self):
        low_priority = self._create_announcement(
            title='Low Priority',
            priority=5,
            start_date=self.now - timedelta(days=2),
        )
        newer_high = self._create_announcement(
            title='Newer High',
            priority=1,
            start_date=self.now - timedelta(hours=1),
        )
        older_high = self._create_announcement(
            title='Older High',
            priority=1,
            start_date=self.now - timedelta(days=1),
        )

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ordered_ids = [item['id'] for item in response.data]
        self.assertEqual(ordered_ids[:3], [newer_high.id, older_high.id, low_priority.id])

    def test_response_contains_expected_fields(self):
        announcement = self._create_announcement(
            title='Field Test',
            action_link='https://example.com/offer',
            target_audience='all',
        )

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = next((a for a in response.data if a['id'] == announcement.id), None)
        self.assertIsNotNone(item)
        self.assertEqual(item['title'], 'Field Test')
        self.assertEqual(item['target_audience'], 'all')
        self.assertEqual(item['action_link'], 'https://example.com/offer')
        self.assertIn('start_date', item)
        self.assertIn('end_date', item)

    def test_anonymous_users_do_not_receive_agent_only_announcements(self):
        all_announcement = self._create_announcement(title='All', target_audience='all')
        customer_announcement = self._create_announcement(title='Customers', target_audience='customers')
        self._create_announcement(title='Agents', target_audience='agents')

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data}
        self.assertIn(all_announcement.id, ids)
        self.assertIn(customer_announcement.id, ids)
        self.assertEqual(len(ids), 2)

    def test_agent_users_receive_agent_and_global_announcements_only(self):
        all_announcement = self._create_announcement(title='All', target_audience='all')
        agent_announcement = self._create_announcement(title='Agents', target_audience='agents')
        self._create_announcement(title='Customers', target_audience='customers')
        self.client.force_authenticate(user=self.agent)

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data}
        self.assertIn(all_announcement.id, ids)
        self.assertIn(agent_announcement.id, ids)
        self.assertEqual(len(ids), 2)

    def test_customer_users_receive_customer_and_global_announcements_only(self):
        all_announcement = self._create_announcement(title='All', target_audience='all')
        customer_announcement = self._create_announcement(title='Customers', target_audience='customers')
        self._create_announcement(title='Agents', target_audience='agents')
        self.client.force_authenticate(user=self.customer)

        response = self.client.get('/api/announcements/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item['id'] for item in response.data}
        self.assertIn(all_announcement.id, ids)
        self.assertIn(customer_announcement.id, ids)
        self.assertEqual(len(ids), 2)
