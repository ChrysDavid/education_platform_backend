from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Message, MessageRead


@receiver(post_save, sender=Message)
def handle_new_message(sender, instance, created, **kwargs):
    """
    Signal pour gérer les nouveaux messages.
    - Marque automatiquement le message comme lu par l'expéditeur
    - Met à jour la date de dernière lecture de l'expéditeur
    - Envoie une notification aux autres participants si nécessaire
    """
    if created:
        # Pour les messages systèmes, ne rien faire de spécial
        if instance.message_type == 'system' or not instance.sender:
            return
        
        # Marquer le message comme lu par l'expéditeur
        MessageRead.objects.get_or_create(message=instance, user=instance.sender)
        
        # Mettre à jour la date de dernière lecture de l'expéditeur
        from .models import ConversationParticipant
        try:
            participant = ConversationParticipant.objects.get(
                conversation=instance.conversation,
                user=instance.sender
            )
            participant.last_read_at = timezone.now()
            participant.save(update_fields=['last_read_at'])
        except ConversationParticipant.DoesNotExist:
            pass
        
        # Notifier les autres participants si nécessaire
        try:
            from apps.notifications.services import NotificationService
            
            # Récupérer les participants à notifier
            other_participants = ConversationParticipant.objects.filter(
                conversation=instance.conversation
            ).exclude(
                user=instance.sender
            ).filter(
                notify_on_new_message=True
            ).select_related('user')
            
            for participant in other_participants:
                # Préparer le titre de la notification
                if instance.conversation.title:
                    notification_title = f"Nouveau message dans {instance.conversation.title}"
                elif instance.conversation.conversation_type == 'direct':
                    notification_title = f"Nouveau message de {instance.sender.get_full_name()}"
                else:
                    notification_title = "Nouveau message"
                
                # Créer la notification
                NotificationService.create_notification(
                    user=participant.user,
                    notification_type_code='new_message',
                    title=notification_title,
                    body=instance.content[:100] + ('...' if len(instance.content) > 100 else ''),
                    related_object=instance,
                    action_url=f'/messaging/{instance.conversation.id}/',
                    action_text='Voir le message'
                )
        except ImportError:
            # Le module notifications n'est pas disponible
            pass
        except Exception as e:
            # Une erreur s'est produite lors de l'envoi des notifications
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi de notifications de nouveau message: {str(e)}")