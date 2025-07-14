# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    SchoolAPIListView,
    SchoolAPIDetailView,
    SchoolReviewAPIListView,
    CityAPIListView,
    SchoolTypeAPIListView
)

# Exporter toutes les vues pour l'API mobile
__all__ = [
    'SchoolAPIListView',
    'SchoolAPIDetailView',
    'SchoolReviewAPIListView',
    'CityAPIListView',
    'SchoolTypeAPIListView'
]