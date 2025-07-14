# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    ConversationListView,
    ConversationDetailView,
    ConversationCreateView,
    DirectMessageCreateView,
    MessageCreateView,
    mark_message_as_read,
    mark_conversation_as_read,
    add_reaction,
)

from .web import (
    ConversationUpdateView,
    ConversationDeleteView,
    ParticipantAddView,
    ParticipantRemoveView,
    ParticipantUpdateView,
)

# Exporter toutes les vues pour l'API mobile et web
__all__ = [
    'ConversationListView',
    'ConversationDetailView',
    'ConversationCreateView',
    'DirectMessageCreateView',
    'MessageCreateView',
    'mark_message_as_read',
    'mark_conversation_as_read',
    'add_reaction',
    'ConversationUpdateView',
    'ConversationDeleteView',
    'ParticipantAddView',
    'ParticipantRemoveView',
    'ParticipantUpdateView',
]