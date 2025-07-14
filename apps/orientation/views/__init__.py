# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    AssessmentListView,
    AssessmentDetailView,
    TakeAssessmentView,
)

from .web import (
    AssessmentTypeListView,
    AssessmentTypeDetailView,
    AssessmentTypeCreateView,
    AssessmentTypeUpdateView,
    AssessmentTypeDeleteView,
    AssessmentQuestionCreateView,
    AssessmentQuestionUpdateView,
    AssessmentQuestionDeleteView,
    AssessmentCreateView,
    AssessmentUpdateView,
    AssessmentDeleteView,
)

# Exporter toutes les vues pour l'API mobile et web
__all__ = [
    'AssessmentListView',
    'AssessmentDetailView',
    'TakeAssessmentView',
    'AssessmentTypeListView',
    'AssessmentTypeDetailView',
    'AssessmentTypeCreateView',
    'AssessmentTypeUpdateView',
    'AssessmentTypeDeleteView',
    'AssessmentQuestionCreateView',
    'AssessmentQuestionUpdateView',
    'AssessmentQuestionDeleteView',
    'AssessmentCreateView',
    'AssessmentUpdateView',
    'AssessmentDeleteView',
]