from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.forum'
    verbose_name = _('Forum')
    
    def ready(self):
        import apps.forum.signals