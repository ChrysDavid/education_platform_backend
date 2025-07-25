from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.resources'
    verbose_name = _('Ressources')
    
    def ready(self):
        import apps.resources.signals