# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    ForumHomepageView,
    CategoryDetailView,
    TopicDetailView,
    TopicCreateView,
    PostCreateView,
    subscribe_topic,
    react_to_post,
    report_post,
)

from .web import (
    TopicUpdateView,
    PostUpdateView,
    moderate_topic,
    moderate_post,
)

# Exporter toutes les vues pour l'API mobile et web
__all__ = [
    'ForumHomepageView',
    'CategoryDetailView',
    'TopicDetailView',
    'TopicCreateView',
    'PostCreateView',
    'subscribe_topic',
    'react_to_post',
    'report_post',
    'TopicUpdateView',
    'PostUpdateView',
    'moderate_topic',
    'moderate_post',
]