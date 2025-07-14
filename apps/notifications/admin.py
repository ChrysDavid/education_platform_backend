from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    NotificationType, UserNotificationPreference, Notification, 
    NotificationTemplate, DeviceToken
)


class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'has_email', 'has_in_app', 'has_push', 'is_active', 'default_user_preference', 'order']
    list_filter = ['has_email', 'has_in_app', 'has_push', 'is_active', 'default_user_preference']
    search_fields = ['code', 'name', 'description']
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'order')
        }),
        (_('Templates'), {
            'fields': ('title_template', 'body_template')
        }),
        (_('Canaux de livraison'), {
            'fields': ('has_email', 'has_in_app', 'has_push')
        }),
        (_('Affichage'), {
            'fields': ('icon', 'color')
        }),
        (_('Paramètres'), {
            'fields': ('is_active', 'default_user_preference')
        }),
    )


class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'email_enabled', 'in_app_enabled', 'push_enabled']
    list_filter = ['email_enabled', 'in_app_enabled', 'push_enabled', 'notification_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title_short', 'status', 'created_at', 'sent_by_email', 'sent_by_push']
    list_filter = ['status', 'notification_type', 'sent_by_email', 'sent_by_push', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'title', 'body']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'read_at', 'archived_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'notification_type', 'status')
        }),
        (_('Contenu'), {
            'fields': ('title', 'body', 'action_url', 'action_text')
        }),
        (_('Référence'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Données'), {
            'fields': ('data',)
        }),
        (_('Dates'), {
            'fields': ('created_at', 'read_at', 'archived_at')
        }),
        (_('Livraison'), {
            'fields': ('sent_by_email', 'sent_by_push')
        }),
    )
    
    def title_short(self, obj):
        if len(obj.title) > 50:
            return obj.title[:47] + "..."
        return obj.title
    title_short.short_description = _('Titre')


class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'notification_type', 'is_active']
    list_filter = ['notification_type', 'is_active']
    search_fields = ['code', 'name', 'description']
    
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'description', 'notification_type', 'is_active')
        }),
        (_('Email'), {
            'fields': ('subject_template', 'email_template')
        }),
        (_('Application'), {
            'fields': ('title_template', 'body_template')
        }),
    )


class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'platform', 'device_name', 'is_active', 'created_at', 'last_used_at']
    list_filter = ['platform', 'is_active', 'created_at', 'last_used_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'device_name']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'last_used_at']


admin.site.register(NotificationType, NotificationTypeAdmin)
admin.site.register(UserNotificationPreference, UserNotificationPreferenceAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
admin.site.register(DeviceToken, DeviceTokenAdmin)