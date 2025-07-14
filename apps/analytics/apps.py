from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = _('Analytique')
    
    def ready(self):
        # Import des signaux lors du chargement de l'application
        import apps.analytics.signals