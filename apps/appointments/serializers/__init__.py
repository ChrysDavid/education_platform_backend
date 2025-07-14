# Ce fichier permet l'importation depuis le dossier serializers
# Importation des sérialiseurs mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AvailabilitySerializer,
    NextAvailableSlotSerializer,
)

from .web import (
    AppointmentSlotSerializer,
    AppointmentExceptionSerializer,
)

from .base import (
    AppointmentReminderSerializer,
)

__all__ = [
    'AppointmentSerializer',
    'AppointmentCreateSerializer',
    'AppointmentUpdateSerializer',
    'AvailabilitySerializer',
    'NextAvailableSlotSerializer',
    'AppointmentSlotSerializer',
    'AppointmentExceptionSerializer',
    'AppointmentReminderSerializer',
]