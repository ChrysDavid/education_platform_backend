from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appointments'
    verbose_name = _('Rendez-vous')

    def ready(self):
        # Import des signaux lors du chargement de l'application
        import apps.appointments.signals