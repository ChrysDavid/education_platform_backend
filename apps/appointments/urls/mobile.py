from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import views

app_name = 'appointments'

# Création d'un routeur pour les API REST
router = DefaultRouter()
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    # URLs standards pour les utilisateurs
    path('calendar/', views.AppointmentCalendarView.as_view(), name='calendar'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my_appointments'),
    path('create/', views.AppointmentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AppointmentDetailView.as_view(), name='detail'),
    path('<int:pk>/cancel/', views.AppointmentCancelView.as_view(), name='cancel'),
    path('<int:pk>/confirm/', views.AppointmentConfirmView.as_view(), name='confirm'),
    path('<int:pk>/complete/', views.AppointmentCompleteView.as_view(), name='complete'),
    path('<int:pk>/reschedule/', views.AppointmentRescheduleView.as_view(), name='reschedule'),
    
    # APIs pour la disponibilité
    path('api/availability/<int:user_id>/', views.UserAvailabilityView.as_view(), name='user_availability'),
    path('api/next-available/<int:user_id>/', views.NextAvailableSlotView.as_view(), name='next_available_slot'),
    
    # URLs du routeur API
    path('api/', include(router.urls)),
]