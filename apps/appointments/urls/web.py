from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import views

app_name = 'appointments'

# Création d'un routeur pour les API REST
router = DefaultRouter()
router.register(r'slots', views.AppointmentSlotViewSet, basename='slot')
router.register(r'exceptions', views.AppointmentExceptionViewSet, basename='exception')

urlpatterns = [
    # URLs pour la gestion des créneaux
    path('slots/manage/', views.ManageAppointmentSlotsView.as_view(), name='manage_slots'),
    path('slots/create/', views.AppointmentSlotCreateView.as_view(), name='create_slot'),
    path('slots/<int:pk>/update/', views.AppointmentSlotUpdateView.as_view(), name='update_slot'),
    path('slots/<int:pk>/delete/', views.AppointmentSlotDeleteView.as_view(), name='delete_slot'),
    
    # URLs pour la gestion des exceptions
    path('exceptions/create/', views.AppointmentExceptionCreateView.as_view(), name='create_exception'),
    path('exceptions/<int:pk>/update/', views.AppointmentExceptionUpdateView.as_view(), name='update_exception'),
    path('exceptions/<int:pk>/delete/', views.AppointmentExceptionDeleteView.as_view(), name='delete_exception'),
    
    # URLs pour la mise à jour des rendez-vous
    path('<int:pk>/update/', views.AppointmentUpdateView.as_view(), name='update'),
    
    # URLs du routeur API
    path('api/', include(router.urls)),
]