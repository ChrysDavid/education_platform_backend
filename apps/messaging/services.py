from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

import logging
from .models import Conversation, ConversationParticipant, Message, MessageRead

User = get_user_model()
logger = logging.getLogger(__name__)


class MessagingService:
    """
    Service pour gérer la messagerie.
    """
    @classmethod
    def create_direct_conversation(cls, user_1, user_2):
        """
        Crée une conversation directe entre deux utilisateurs.
        Si une conversation existe déjà, la renvoie.
        
        Args:
            user_1: Premier utilisateur
            user_2: Deuxième utilisateur
            
        Returns:
            La conversation créée ou existante
        """
        # Vérifier si une conversation directe existe déjà
        direct_conversations = Conversation.objects.filter(
            conversation_type='direct'
        ).filter(
            participants__user=user_1
        ).filter(
            participants__user=user_2
        ).distinct()
        
        if direct_conversations.exists():
            return direct_conversations.first()
        
        # Créer une nouvelle conversation
        with transaction.atomic():
            conversation = Conversation.objects.create(
                conversation_type='direct',
                created_by=user_1
            )
            
            # Ajouter les participants
            conversation.add_participant(user_1)
            conversation.add_participant(user_2)
            
            return conversation
    
    @classmethod
    def send_direct_message(cls, sender, recipient, content, message_type='text'):
        """
        Envoie un message direct à un utilisateur.
        
        Args:
            sender: Utilisateur expéditeur
            recipient: Utilisateur destinataire
            content: Contenu du message
            message_type: Type de message (texte par défaut)
            
        Returns:
            Le message créé
        """
        # Créer ou récupérer la conversation
        conversation = cls.create_direct_conversation(sender, recipient)
        
        # Créer le message
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            message_type=message_type,
            content=content
        )
        
        # Marquer comme lu par l'expéditeur
        MessageRead.objects.create(message=message, user=sender)
        
        # Mettre à jour la dernière lecture de l'expéditeur
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=sender
        )
        participant.mark_as_read()
        
        # Mettre à jour la date du dernier message
        conversation.update_last_message_time()
        
        # Notifier le destinataire si nécessaire (via l'app notifications)
        try:
            from apps.notifications.services import NotificationService
            
            recipient_participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=recipient
            )
            
            if recipient_participant.notify_on_new_message:
                NotificationService.create_notification(
                    user=recipient,
                    notification_type_code='new_message',
                    context={
                        'sender_name': sender.get_full_name(),
                        'message_preview': content[:100] + ('...' if len(content) > 100 else ''),
                        'conversation_id': conversation.id
                    },
                    related_object=message,
                    action_url=f'/messaging/{conversation.id}/',
                    action_text=_('Voir le message'),
                    send_now=True
                )
        except ImportError:
            logger.warning("Module de notifications non disponible")
        except Exception as e:
            logger.error(f"Erreur lors de la notification: {str(e)}")
        
        return message
    
    @classmethod
    def create_group_conversation(cls, creator, title, participants=None, description=''):
        """
        Crée une conversation de groupe.
        
        Args:
            creator: Utilisateur créateur du groupe
            title: Titre du groupe
            participants: Liste des utilisateurs participants (en plus du créateur)
            description: Description du groupe
            
        Returns:
            La conversation créée
        """
        with transaction.atomic():
            conversation = Conversation.objects.create(
                title=title,
                conversation_type='group',
                is_group=True,
                group_description=description,
                created_by=creator
            )
            
            # Ajouter le créateur comme administrateur
            conversation.add_participant(creator, is_admin=True)
            
            # Ajouter les autres participants
            if participants:
                for user in participants:
                    if user != creator:
                        conversation.add_participant(user)
            
            # Ajouter un message système
            message = _(f"{creator.get_full_name()} a créé le groupe.")
            Message.objects.create(
                conversation=conversation,
                message_type='system',
                content=message
            )
            
            return conversation
    
    @classmethod
    def create_conversation_for_object(cls, obj, creator, title=None, participants=None):
        """
        Crée une conversation liée à un objet spécifique (ex: projet, événement).
        
        Args:
            obj: Objet associé à la conversation
            creator: Utilisateur créateur de la conversation
            title: Titre de la conversation (facultatif)
            participants: Liste des utilisateurs participants (en plus du créateur)
            
        Returns:
            La conversation créée
        """
        obj_type = ContentType.objects.get_for_model(obj)
        
        # Vérifier si une conversation existe déjà pour cet objet
        existing_conversation = Conversation.objects.filter(
            content_type=obj_type,
            object_id=obj.pk
        ).first()
        
        if existing_conversation:
            return existing_conversation
        
        # Déterminer le titre si non fourni
        if not title:
            if hasattr(obj, 'name'):
                title = obj.name
            elif hasattr(obj, 'title'):
                title = obj.title
            else:
                title = f"{obj.__class__.__name__} #{obj.pk}"
        
        # Créer la conversation
        with transaction.atomic():
            conversation = Conversation.objects.create(
                title=title,
                conversation_type='group',
                is_group=True,
                created_by=creator,
                content_type=obj_type,
                object_id=obj.pk
            )
            
            # Ajouter le créateur comme administrateur
            conversation.add_participant(creator, is_admin=True)
            
            # Ajouter les autres participants
            if participants:
                for user in participants:
                    if user != creator:
                        conversation.add_participant(user)
            
            # Ajouter un message système
            message = _(f"{creator.get_full_name()} a créé la conversation pour {title}.")
            Message.objects.create(
                conversation=conversation,
                message_type='system',
                content=message
            )
            
            return conversation