from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from users.models import User
from chat.models import Conversation, Message
from properties.models import Listing


class ChatModelTests(TestCase):
    """Test cases for Chat models"""
    
    def setUp(self):
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            is_agent=False
        )
        self.agent = User.objects.create_user(
            username='testagent',
            email='agent@test.com',
            password='testpass123',
            is_agent=True
        )
        
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.customer, self.agent)
        
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.customer,
            content='Hello, I am interested in this property'
        )
    
    def test_conversation_creation(self):
        """Test that conversation is created with participants"""
        self.assertEqual(self.conversation.participants.count(), 2)
        self.assertIn(self.customer, self.conversation.participants.all())
        self.assertIn(self.agent, self.conversation.participants.all())
    
    def test_message_creation(self):
        """Test that message is created correctly"""
        self.assertEqual(self.message.content, 'Hello, I am interested in this property')
        self.assertEqual(self.message.sender, self.customer)
        self.assertEqual(self.message.conversation, self.conversation)


class ChatAPITests(APITestCase):
    """Test cases for Chat API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@test.com',
            password='testpass123',
            is_agent=False
        )
        self.agent = User.objects.create_user(
            username='testagent',
            email='agent@test.com',
            password='testpass123',
            is_agent=True
        )
        self.other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@test.com',
            password='testpass123',
            is_agent=False
        )
        
        # Create conversation
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.customer, self.agent)
        
        # Create messages
        self.message1 = Message.objects.create(
            conversation=self.conversation,
            sender=self.customer,
            content='Hello from customer'
        )
        self.message2 = Message.objects.create(
            conversation=self.conversation,
            sender=self.agent,
            content='Hello from agent'
        )
    
    def test_get_conversations(self):
        """Test getting user's conversations"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/conversations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_start_new_conversation(self):
        """Test starting a new conversation"""
        self.client.force_authenticate(user=self.other_customer)
        data = {'agent_id': self.agent.id}
        response = self.client.post('/api/conversations/start/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify conversation was created
        self.assertEqual(Conversation.objects.count(), 2)
    
    def test_start_conversation_with_self(self):
        """Test that users cannot start conversation with themselves"""
        self.client.force_authenticate(user=self.customer)
        data = {'agent_id': self.customer.id}
        response = self.client.post('/api/conversations/start/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_messages(self):
        """Test getting messages for a conversation"""
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(f'/api/messages/?conversation_id={self.conversation.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_send_message(self):
        """Test sending a message"""
        self.client.force_authenticate(user=self.customer)
        data = {
            'conversation': self.conversation.id,
            'content': 'New test message'
        }
        response = self.client.post('/api/messages/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify message was created
        self.assertEqual(Message.objects.filter(conversation=self.conversation).count(), 3)
    
    def test_unauthorized_user_cannot_access_messages(self):
        """Test that unauthorized users cannot access conversation messages"""
        self.client.force_authenticate(user=self.other_customer)
        response = self.client.get(f'/api/messages/?conversation_id={self.conversation.id}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
