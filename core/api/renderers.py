from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
import json

class PrettyJSONRenderer(JSONRenderer):
    """
    Rendu JSON avec indentation pour une meilleure lisibilité.
    """
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        # Indenter le JSON pour une meilleure lisibilité
        return json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
            sort_keys=True
        ).encode('utf-8')

class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    Rendu d'API navigable personnalisé.
    """
    
    def get_default_renderer(self, view):
        # Utiliser le rendu JSON indenté par défaut
        return PrettyJSONRenderer()
    
    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        
        # Personnaliser le contexte si nécessaire
        context['brand_name'] = 'Plateforme Éducative'
        context['api_name'] = 'API de la Plateforme Éducative'
        
        return context