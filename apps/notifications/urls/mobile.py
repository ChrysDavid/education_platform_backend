from django.urls import path
from .. import views

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/mark-as-read/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('<int:pk>/mark-as-unread/', views.mark_notification_as_unread, name='mark_notification_as_unread'),
    path('mark-all-as-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('<int:pk>/archive/', views.archive_notification, name='archive_notification'),
    path('archive-all/', views.archive_all_notifications, name='archive_all_notifications'),
    path('count/', views.get_notification_count, name='get_notification_count'),
    
    # Préférences
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
    
    # Tokens d'appareil
    path('device/register/', views.register_device_token, name='register_device_token'),
    path('device/unregister/', views.unregister_device_token, name='unregister_device_token'),
]