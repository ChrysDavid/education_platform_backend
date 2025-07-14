from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Conversation, ConversationParticipant, Message, 
    MessageReaction, MessageRead
)


class ConversationParticipantInline(admin.TabularInline):
    model = ConversationParticipant
    extra = 1
    raw_id_fields = ['user']


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ['sender', 'message_type', 'content', 'created_at']
    readonly_fields = ['sender', 'message_type', 'content', 'created_at']
    can_delete = False
    max_num = 10
    ordering = ['-created_at']


class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_display', 'conversation_type', 'is_group', 'created_by', 'participants_count', 'created_at', 'last_message_at']
    list_filter = ['conversation_type', 'is_group', 'created_at']
    search_fields = ['title', 'created_by__first_name', 'created_by__last_name', 'created_by__email']
    date_hierarchy = 'created_at'
    inlines = [ConversationParticipantInline, MessageInline]
    raw_id_fields = ['created_by']
    
    def title_display(self, obj):
        return obj.title or f"Conversation #{obj.id}"
    title_display.short_description = _('Titre')
    
    def participants_count(self, obj):
        return obj.participants.count()
    participants_count.short_description = _('Nombre de participants')


class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversation', 'is_admin', 'is_muted', 'notify_on_new_message', 'joined_at', 'last_read_at']
    list_filter = ['is_admin', 'is_muted', 'notify_on_new_message', 'joined_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'conversation__title']
    raw_id_fields = ['user', 'conversation']
    date_hierarchy = 'joined_at'


class MessageReactionInline(admin.TabularInline):
    model = MessageReaction
    extra = 0
    raw_id_fields = ['user']


class MessageReadInline(admin.TabularInline):
    model = MessageRead
    extra = 0
    raw_id_fields = ['user']


class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'content_preview', 'created_at', 'is_edited', 'is_delivered']
    list_filter = ['message_type', 'is_edited', 'is_delivered', 'created_at']
    search_fields = ['content', 'sender__first_name', 'sender__last_name', 'sender__email', 'conversation__title']
    raw_id_fields = ['sender', 'conversation', 'parent']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [MessageReactionInline, MessageReadInline]
    
    def content_preview(self, obj):
        if obj.content and len(obj.content) > 50:
            return obj.content[:47] + '...'
        return obj.content
    content_preview.short_description = _('Contenu')


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(ConversationParticipant, ConversationParticipantAdmin)
admin.site.register(Message, MessageAdmin)