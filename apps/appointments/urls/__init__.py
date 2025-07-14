# Ce fichier permet l'importation depuis le dossier urls
# Par défaut, on peut importer directement les URLs mobiles
# car ce sont les plus utilisées par les autres parties du code

from .mobile import urlpatterns

__all__ = ['urlpatterns']