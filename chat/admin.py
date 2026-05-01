from django.contrib import admin
from .models import Conversation, Message, Inquiry

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participants_list', 'listing', 'started_by', 'started_at', 'last_message_at')
    list_filter = ('started_at', 'last_message_at')
    search_fields = ('participants__username', 'listing__title')
    inlines = [MessageInline]
    filter_horizontal = ('participants',)

    def participants_list(self, obj):
        return ", ".join(obj.participants.values_list('username', flat=True))
    participants_list.short_description = 'Participants'

class InquiryAdmin(admin.ModelAdmin):
    list_display = ('customer', 'listing', 'conversation', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('customer', 'listing', 'conversation', 'created_at')
    search_fields = ('customer__username', 'listing__title')
    list_select_related = ('customer', 'listing', 'conversation')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'short_content', 'is_read', 'timestamp')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'content')
    readonly_fields = ('timestamp',)
    list_select_related = ('conversation', 'sender')

    def short_content(self, obj):
        if len(obj.content) <= 80:
            return obj.content
        return f"{obj.content[:77]}..."
    short_content.short_description = 'Message'

admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Inquiry, InquiryAdmin)
