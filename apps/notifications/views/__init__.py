# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    NotificationListView,
    NotificationDetailView,
    mark_notification_as_read,
    mark_notification_as_unread,
    mark_all_notifications_as_read,
    archive_notification,
    archive_all_notifications,
    get_notification_count,
    NotificationPreferencesView,
    register_device_token,
    unregister_device_token,
)

from .web import (
    NotificationTypeListView,
    NotificationTypeCreateView,
    NotificationTypeUpdateView,
    NotificationTypeDetailView,
    NotificationTypeDeleteView,
    NotificationTemplateListView,
    NotificationTemplateCreateView,
    NotificationTemplateUpdateView,
    NotificationTemplateDeleteView,
    DeviceTokenListView,
    DeviceTokenCreateView,
    DeviceTokenUpdateView,
    DeviceTokenDeleteView,
)

# Exporter toutes les vues pour l'API mobile et web
__all__ = [
    'NotificationListView',
    'NotificationDetailView',
    'mark_notification_as_read',
    'mark_notification_as_unread',
    'mark_all_notifications_as_read',
    'archive_notification',
    'archive_all_notifications',
    'get_notification_count',
    'NotificationPreferencesView',
    'register_device_token',
    'unregister_device_token',
    'NotificationTypeListView',
    'NotificationTypeCreateView',
    'NotificationTypeUpdateView',
    'NotificationTypeDetailView',
    'NotificationTypeDeleteView',
    'NotificationTemplateListView',
    'NotificationTemplateCreateView',
    'NotificationTemplateUpdateView',
    'NotificationTemplateDeleteView',
    'DeviceTokenListView',
    'DeviceTokenCreateView',
    'DeviceTokenUpdateView',
    'DeviceTokenDeleteView',
]