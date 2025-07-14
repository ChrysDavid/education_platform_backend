from django.urls import path
from .. import views

app_name = 'notifications'

urlpatterns = [
    # Types de notification (admin)
    path('admin/types/', views.NotificationTypeListView.as_view(), name='admin_notification_type_list'),
    path('admin/types/<int:pk>/', views.NotificationTypeDetailView.as_view(), name='admin_notification_type_detail'),
    path('admin/types/create/', views.NotificationTypeCreateView.as_view(), name='admin_notification_type_create'),
    path('admin/types/<int:pk>/update/', views.NotificationTypeUpdateView.as_view(), name='admin_notification_type_update'),
    path('admin/types/<int:pk>/delete/', views.NotificationTypeDeleteView.as_view(), name='admin_notification_type_delete'),
    
    # Modèles de notification (admin)
    path('admin/templates/', views.NotificationTemplateListView.as_view(), name='admin_notification_template_list'),
    path('admin/templates/create/', views.NotificationTemplateCreateView.as_view(), name='admin_notification_template_create'),
    path('admin/templates/<int:pk>/update/', views.NotificationTemplateUpdateView.as_view(), name='admin_notification_template_update'),
    path('admin/templates/<int:pk>/delete/', views.NotificationTemplateDeleteView.as_view(), name='admin_notification_template_delete'),
    
    # Tokens d'appareil (admin)
    path('admin/devices/', views.DeviceTokenListView.as_view(), name='admin_device_token_list'),
    path('admin/devices/create/', views.DeviceTokenCreateView.as_view(), name='admin_device_token_create'),
    path('admin/devices/<int:pk>/update/', views.DeviceTokenUpdateView.as_view(), name='admin_device_token_update'),
    path('admin/devices/<int:pk>/delete/', views.DeviceTokenDeleteView.as_view(), name='admin_device_token_delete'),
]