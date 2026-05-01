from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.db import models
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

User = get_user_model()


def create_notification(user, notification_type, title, message, data=None):
    """Helper to create notifications"""
    from users.models import Notification
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        data=data or {}
    )

# 1. Liiska Wada-hadalada (Inbox List)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    # Show conversations that:
    # 1. Have at least one message, OR
    # 2. Were started by the current user (even if no message sent yet)
    # This prevents spam from users who clicked but never sent a message
    chats = Conversation.objects.filter(participants=request.user).filter(
        models.Q(messages__isnull=False) | models.Q(started_by=request.user)
    ).distinct()
    serializer = ConversationSerializer(chats, many=True, context={'request': request})
    return Response(serializer.data)

# 2. Bilow Chat Cusub (Start Chat)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_chat(request):
    agent_id = request.data.get('agent_id')
    listing_id = request.data.get('listing_id')  # Optional: chat about specific property
    
    # Soo hel dilaalka
    agent = get_object_or_404(User, id=agent_id)

    # Ha isula hadlin naftaada
    if agent == request.user:
        return Response({'error': "You cannot chat with yourself"}, status=400)

    # Hubi haddii chat hore jiro
    existing_chat = Conversation.objects.filter(participants=request.user).filter(participants=agent).first()
    
    if existing_chat:
        # Update listing to the new property if one is provided
        if listing_id:
            from properties.models import Listing
            listing = get_object_or_404(Listing, id=listing_id)
            existing_chat.listing = listing
            existing_chat.save()
        
        serializer = ConversationSerializer(existing_chat, context={'request': request})
        return Response(serializer.data)

    # Abuur cusub haddii uusan jirin
    new_chat = Conversation.objects.create(started_by=request.user)
    new_chat.participants.add(request.user, agent)
    
    # Haddii ay ku saabsan tahay hanti gaar ah, ku xir
    if listing_id:
        from properties.models import Listing
        listing = get_object_or_404(Listing, id=listing_id)
        new_chat.listing = listing
        
        # Create Inquiry for analytics
        from .models import Inquiry
        inquiry = Inquiry.objects.create(
            listing=listing,
            customer=request.user,
            conversation=new_chat
        )
        
        # Notify agent about new inquiry
        agent_name = request.user.profile.full_name or request.user.username
        if listing:
            create_notification(
                user=agent,
                notification_type='inquiry',
                title='New Inquiry',
                message=f'{agent_name} is interested in your property "{listing.title}"',
                data={
                    'conversation_id': new_chat.id,
                    'listing_id': listing.id
                }
            )
        else:
            create_notification(
                user=agent,
                notification_type='inquiry',
                title='New Message',
                message=f'{agent_name} wants to contact you',
                data={
                    'conversation_id': new_chat.id
                }
            )
    
    new_chat.save()
    
    serializer = ConversationSerializer(new_chat, context={'request': request})
    return Response(serializer.data)

# Get single conversation details
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_detail(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        
        # Check if user is participant
        if request.user not in conversation.participants.all():
            return Response({'error': 'Not authorized'}, status=403)
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=404)

# 3. Fariimaha (Get & Send Messages)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_messages(request):
    # GET: Soo qaado fariimaha chat gaar ah
    if request.method == 'GET':
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response({'error': 'Conversation ID required'}, status=400)
            
        # Hubi inaan chat-kan qeyb ka ahay
        try:
            chat = Conversation.objects.prefetch_related('participants').get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=404)
        
        # Fix: Properly check if user is a participant
        participant_ids = list(chat.participants.values_list('id', flat=True))
        if request.user.id not in participant_ids:
            return Response({'error': 'Not authorized'}, status=403)
            
        messages = Message.objects.filter(conversation=chat).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    # POST: Dir fariin cusub
    elif request.method == 'POST':
        serializer = MessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            conversation = serializer.validated_data['conversation']
            # Fix: Properly check if user is a participant
            participant_ids = list(conversation.participants.values_list('id', flat=True))
            if request.user.id not in participant_ids:
                return Response({'error': 'Not authorized'}, status=403)
            
            # Save message
            message = serializer.save(sender=request.user)
            conversation.save() # Update timestamp
            
            # Send notification to other participants
            for participant in conversation.participants.all():
                if participant.id != request.user.id:
                    # Get other user's name
                    other_user = request.user.profile.full_name or request.user.username
                    create_notification(
                        user=participant,
                        notification_type='message',
                        title='New Message',
                        message=f'{other_user} sent you a message',
                        data={
                            'conversation_id': conversation.id,
                            'message_id': message.id
                        }
                    )
            
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

# 8. Test Notification (Demo)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """Test endpoint to create a notification for demo purposes"""
    title = request.data.get('title', 'Test Notification')
    message = request.data.get('message', 'This is a test notification from eDalaal!')
    
    create_notification(
        user=request.user,
        notification_type='test',
        title=title,
        message=message,
        data={'source': 'test_endpoint'}
    )
    
    return Response({'success': True, 'message': 'Notification created'})
