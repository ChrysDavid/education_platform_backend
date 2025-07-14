# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    AppointmentCalendarView,
    MyAppointmentsView,
    AppointmentDetailView,
    AppointmentCreateView,
    AppointmentCancelView,
    AppointmentConfirmView,
    AppointmentCompleteView,
    AppointmentRescheduleView,
    AppointmentViewSet,
    UserAvailabilityView,
    NextAvailableSlotView,
)

from .web import (
    AppointmentUpdateView,
    ManageAppointmentSlotsView,
    AppointmentSlotCreateView,
    AppointmentSlotUpdateView,
    AppointmentSlotDeleteView,
    AppointmentExceptionCreateView,
    AppointmentExceptionUpdateView,
    AppointmentExceptionDeleteView,
    AppointmentSlotViewSet,
    AppointmentExceptionViewSet,
)

# Exporter toutes les vues pour l'API mobile et web
__all__ = [
    'AppointmentCalendarView',
    'MyAppointmentsView',
    'AppointmentDetailView',
    'AppointmentCreateView',
    'AppointmentCancelView',
    'AppointmentConfirmView',
    'AppointmentCompleteView',
    'AppointmentRescheduleView',
    'AppointmentViewSet',
    'UserAvailabilityView',
    'NextAvailableSlotView',
    'AppointmentUpdateView',
    'ManageAppointmentSlotsView',
    'AppointmentSlotCreateView',
    'AppointmentSlotUpdateView',
    'AppointmentSlotDeleteView',
    'AppointmentExceptionCreateView',
    'AppointmentExceptionUpdateView',
    'AppointmentExceptionDeleteView',
    'AppointmentSlotViewSet',
    'AppointmentExceptionViewSet',
]