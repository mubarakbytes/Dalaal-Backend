from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import path, reverse
from .models import User, Profile, State, Degmo, Magaalo, DeviceToken, Notification, Review
from .messaging import send_verification_message


def approve_broker_verification(modeladmin, request, queryset):
    """Approve broker verification and send chat message"""
    approved = 0
    for profile in queryset.filter(user__is_agent=True):
        profile.is_verified = True
        profile.verified_at = timezone.now()
        profile.verified_by = request.user
        profile.rejection_reason = ''
        profile.save()
        
        try:
            send_verification_message(profile.user, 'approved')
        except Exception as e:
            print(f"Failed to send message: {e}")
        
        approved += 1
    
    messages.success(request, f"{approved} broker(s) approved! Chat messages sent.")
approve_broker_verification.short_description = "Approve Selected Brokers"


def reject_broker_verification(modeladmin, request, queryset):
    """Reject broker verification and send chat message with reason"""
    if request.POST.get('confirm') == 'yes':
        reason = request.POST.get('rejection_reason', '').strip()
        
        if not reason:
            messages.error(request, "Please provide a rejection reason!")
            return redirect(request.get_full_path())
        
        rejected = 0
        for profile in queryset.filter(user__is_agent=True):
            profile.is_verified = False
            profile.verified_at = None
            profile.verified_by = None
            profile.rejection_reason = reason
            profile.save()
            
            try:
                send_verification_message(profile.user, 'rejected', rejection_reason=reason)
            except Exception as e:
                print(f"Failed to send message: {e}")
            
            rejected += 1
        
        messages.success(request, f"{rejected} broker(s) rejected! Chat messages sent.")
        return redirect('admin:users_profile_changelist')
    
    return render(request, 'admin/reject_confirmation.html', {
        'queryset': queryset,
        'title': 'Reject Broker Verification',
    })
reject_broker_verification.short_description = "Reject Selected Brokers"


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'user_email', 'full_name', 'is_verified', 'verification_submitted', 'city', 'rating', 'action_buttons')
    list_filter = ('is_verified', 'verification_submitted', 'city')
    search_fields = ('user__username', 'user__email', 'full_name', 'city')
    actions = [approve_broker_verification, reject_broker_verification]
    readonly_fields = ('verified_at', 'verified_by')
    ordering = ('-verification_submitted', '-verified_at')
    
    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def action_buttons(self, obj):
        if obj.verification_submitted and not obj.is_verified and obj.user.is_agent:
            from django.utils.html import format_html
            approve_url = reverse('admin:approve_verification', args=[obj.id])
            reject_url = reverse('admin:reject_verification', args=[obj.id])
            return format_html(
                '<a href="{}" style="background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; margin-right: 5px;">✅ Approve</a>'
                '<a href="{}" style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none;">❌ Reject</a>',
                approve_url, reject_url
            )
        return '-'
    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'full_name', 'bio', 'city', 'profile_photo')
        }),
        ('Verification (Xaqiijinta)', {
            'fields': ('nira_id_image', 'is_verified', 'verified_at', 'verified_by', 'rejection_reason')
        }),
        ('Statistics', {
            'fields': ('rating', 'deals_completed')
        }),
    )
    
    def get_queryset(self, request):
        return Profile.objects.select_related('user')
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:profile_id>/approve/',
                self.admin_site.admin_view(self.approve_view),
                name='approve_verification',
            ),
            path(
                '<int:profile_id>/reject/',
                self.admin_site.admin_view(self.reject_view),
                name='reject_verification',
            ),
        ]
        return custom_urls + urls
    
    def approve_view(self, request, profile_id):
        """Approve a single verification"""
        try:
            profile = Profile.objects.select_related('user').get(id=profile_id)
        except Profile.DoesNotExist:
            messages.error(request, "Profile not found!")
            return redirect('admin:users_profile_changelist')
        
        profile.is_verified = True
        profile.verified_at = timezone.now()
        profile.verified_by = request.user
        profile.rejection_reason = ''
        profile.save()
        
        try:
            send_verification_message(profile.user, 'approved')
            messages.success(request, f"✅ {profile.user.username} approved! Chat message sent to their inbox.")
        except Exception as e:
            messages.error(request, f"Approved but failed to send message: {e}")
        
        return redirect('admin:users_profile_changelist')
    
    def reject_view(self, request, profile_id):
        """Reject a verification with reason"""
        try:
            profile = Profile.objects.select_related('user').get(id=profile_id)
        except Profile.DoesNotExist:
            messages.error(request, "Profile not found!")
            return redirect('admin:users_profile_changelist')
        
        if request.method == 'POST':
            reason = request.POST.get('rejection_reason', '').strip()
            
            if not reason:
                messages.error(request, "Please provide a rejection reason!")
                return render(request, 'admin/reject_single.html', {'profile': profile})
            
            profile.is_verified = False
            profile.verified_at = None
            profile.verified_by = None
            profile.rejection_reason = reason
            profile.save()
            
            try:
                send_verification_message(profile.user, 'rejected', rejection_reason=reason)
                messages.success(request, f"❌ {profile.user.username} rejected! Chat message sent with reason.")
            except Exception as e:
                messages.error(request, f"Rejected but failed to send message: {e}")
            
            return redirect('admin:users_profile_changelist')
        
        return render(request, 'admin/reject_single.html', {'profile': profile})


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline, )
    list_display = ('username', 'email', 'is_agent', 'is_customer', 'is_staff')
    list_filter = ('is_agent', 'is_customer', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('is_agent', 'is_customer')}),
    )


class DegmoInline(admin.TabularInline):
    model = Degmo
    extra = 1
    fields = ('name', 'name_so', 'is_active')


class MagaaloInline(admin.TabularInline):
    model = Magaalo
    extra = 1
    fields = ('name', 'name_so', 'is_active')


class DegmoAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'is_active')
    list_filter = ('state', 'is_active')
    search_fields = ('name',)
    inlines = [MagaaloInline]


class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_so', 'flag_image', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_so')
    inlines = [DegmoInline]


class MagaaloAdmin(admin.ModelAdmin):
    list_display = ('name', 'degmo', 'is_active')
    list_filter = ('degmo__state', 'degmo', 'is_active')
    search_fields = ('name', 'degmo__name', 'degmo__state__name')
    list_select_related = ('degmo', 'degmo__state')


class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'token_preview', 'device_name', 'is_active', 'updated_at')
    list_filter = ('device_type', 'is_active')
    search_fields = ('user__username', 'device_name', 'token')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user',)

    def token_preview(self, obj):
        if len(obj.token) <= 24:
            return obj.token
        return f"{obj.token[:12]}...{obj.token[-8:]}"
    token_preview.short_description = 'Token'


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    list_select_related = ('user',)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'agent', 'rating', 'is_anonymous', 'created_at')
    list_filter = ('rating', 'is_anonymous', 'created_at')
    search_fields = ('reviewer__username', 'agent__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('reviewer', 'agent')


class PendingVerificationAdminSite(admin.AdminSite):
    """Custom admin site for pending verifications only"""
    site_header = "Dalaal - Pending Verifications"
    site_title = "Pending Verifications"
    index_title = "Agent Verification Management"
    index_template = 'admin/index.html'
    
    def get_app_list(self, request, app_label=None):
        from .models import Profile
        pending_count = Profile.objects.filter(
            verification_submitted=True,
            is_verified=False,
            user__is_agent=True
        ).count()
        
        app_list = []
        
        if pending_count > 0:
            models = [{
                'name': f'Pending Verifications ({pending_count})',
                'object_name': 'PendingVerification',
                'admin_url': '/admin/users/profile/?verification_submitted=True&is_verified=False',
                'view_only': True,
            }]
            app_list.append({
                'name': 'Pending Verifications',
                'app_label': 'users',
                'models': models,
            })
        
        return app_list
    
    def index(self, request, extra_context=None):
        """Custom index showing pending verifications"""
        from .models import Profile
        pending_profiles = Profile.objects.filter(
            verification_submitted=True,
            is_verified=False,
            user__is_agent=True
        ).select_related('user')[:20]
        
        extra_context = extra_context or {}
        extra_context['pending_profiles'] = pending_profiles
        
        return super().index(request, extra_context)


pending_site = PendingVerificationAdminSite(name='pending_admin')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(Degmo, DegmoAdmin)
admin.site.register(Magaalo, MagaaloAdmin)
admin.site.register(DeviceToken, DeviceTokenAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Review, ReviewAdmin)
