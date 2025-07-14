from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SchoolsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.schools'
    verbose_name = _('Établissements scolaires')
    
    def ready(self):
        """
        Importe les signaux lors du chargement de l'application pour
        s'assurer que les signaux sont connectés.
        """
        import apps.schools.signals  # noqa