from django.db import transaction
from django.contrib.auth import get_user_model
from django.conf import settings
from chat.models import Conversation, Message
from .models import DEFAULT_PROFILE_PHOTO

User = get_user_model()

EDALAAL_USERNAME = 'edalaal'
EDALAAL_LOGO_URL = 'https://ui-avatars.com/api/?name=eDalaal&background=10B981&color=fff&size=256&font-size=0.4&bold=true'


def get_edalaal_user():
    """Get or create the eDalaal system user with profile"""
    user, created = User.objects.get_or_create(
        username=EDALAAL_USERNAME,
        defaults={
            'email': 'system@dalaal.com',
            'is_agent': False,
            'is_customer': False,
            'is_staff': False,
        }
    )
    
    if created or not hasattr(user, 'profile'):
        from .models import Profile
        profile, profile_created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': 'eDalaal',
                'bio': 'Official eDalaal System - Somalia Real Estate Marketplace',
                'city': 'Mogadishu',
                'profile_photo': DEFAULT_PROFILE_PHOTO,
            }
        )
    
    return user


def send_verification_message(user, message_type, rejection_reason=None):
    """
    Send a verification status message to a user from eDalaal system.
    
    Args:
        user: The user (agent) to send message to
        message_type: 'approved' or 'rejected'
        rejection_reason: Required if message_type is 'rejected'
    
    Returns:
        The created Message object
    """
    edalaal_user = get_edalaal_user()
    
    if message_type == 'approved':
        content = f"""🎉 **Xaqiijintu Waa La Ansixiyay!**

Waad barakaysay {user.profile.full_name or user.username}!

Shahaadada xaqiijinta ee aad soo dirtay waa la ansixiyay. Waxaad hadda noqon kartaa mid fully verified.

Tani waxaa keentay inaad hesho luqadda Soomaali ee barnaamijka.

Hadal kasta oo aad la xidhiidho, fadlan noo soo dir emailka: support@dalaal.com

Wadajirkeen,  
Kooxda Dalaal 🏠"""
    
    elif message_type == 'rejected':
        content = f"""❌ **Shahaadada Xaqiijinta Loo Diiday**

Waad u mahadsan tahay inaad diiwaangelisay Dalaal {user.profile.full_name or user.username}.

Wixii dhacay, shahaadada xaqiijinta aad soo dirtay ma la ansixin.

📋 **Sababta loo diiday:**
{rejection_reason or 'Sababta lama soo sheegay.'}

Haddii aad qabto su'aalo ama aad rabto inaad soo-dirto warqad cusub, fadlan soo xidhiidh emailka: support@dalaal.com

Wadajirkeen,  
Kooxda Dalaal 🏠"""
    
    else:
        raise ValueError("message_type must be 'approved' or 'rejected'")
    
    with transaction.atomic():
        conversation, created = Conversation.objects.get_or_create(
            listing=None,
        )
        
        if not conversation.participants.filter(id=user.id).exists():
            conversation.participants.add(user)
        
        if not conversation.participants.filter(id=edalaal_user.id).exists():
            conversation.participants.add(edalaal_user)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=edalaal_user,
            content=content,
            is_read=False,
        )
        
        # Also create in-app notification
        from .models import Notification
        if message_type == 'approved':
            Notification.objects.create(
                user=user,
                notification_type='verification',
                title='Verification Approved! 🎉',
                message='Your verification has been approved. You are now a verified agent.',
                data={'verified': True}
            )
        elif message_type == 'rejected':
            Notification.objects.create(
                user=user,
                notification_type='verification',
                title='Verification Rejected',
                message=f'Your verification was rejected. Reason: {rejection_reason}',
                data={'verified': False, 'reason': rejection_reason}
            )
    
    return message


def send_property_approved_message(user, listing_title):
    """Send message when a property listing is approved"""
    edalaal_user = get_edalaal_user()
    
    content = f"""✅ **Liiskagu Waa La Dalban Yadayo!**

Waad barakaysay {user.profile.full_name or user.username}!

Liiskaagii "{listing_title}" waa la dalban yadayo waana laga yaallaa bogga wadajirka.

Isticmaaleyaashu hadda waa arki karaan oo soo xidhiidhi karaan kaa.

Wadajirkeen,  
Kooxda Dalaal 🏠"""
    
    with transaction.atomic():
        conversation, created = Conversation.objects.get_or_create(
            listing=None,
        )
        conversation.participants.add(user)
        conversation.participants.add(edalaal_user)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=edalaal_user,
            content=content,
            is_read=False,
        )
    
    return message


def send_property_rejected_message(user, listing_title, reason):
    """Send message when a property listing is rejected"""
    edalaal_user = get_edalaal_user()
    
    content = f"""❌ **Liiskagaaga La Rejectay**

Waad u mahadsan tahay inaad diiwaangelisay Dalaal {user.profile.full_name or user.username}.

Liiskaagii "{listing_title}" waa la diiday.

📋 **Sababta:**
{reason}

Haddii aad su'aalo qabtid, faahfaahin dheeri ah codso, waydiis support@dalaal.com

Wadajirkeen,  
Kooxda Dalaal 🏠"""
    
    with transaction.atomic():
        conversation, created = Conversation.objects.get_or_create(
            listing=None,
        )
        conversation.participants.add(user)
        conversation.participants.add(edalaal_user)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=edalaal_user,
            content=content,
            is_read=False,
        )
    
    return message
