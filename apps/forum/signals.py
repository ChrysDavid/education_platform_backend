from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Post, Topic, TopicSubscription


@receiver(post_save, sender=Post)
def handle_new_post(sender, instance, created, **kwargs):
    """
    Signal pour gérer les nouveaux messages.
    - Mettre à jour la date de dernière activité du sujet
    - Notifier les abonnés au sujet
    """
    if created:
        # Mettre à jour la date de dernière activité du sujet
        topic = instance.topic
        topic.update_last_activity()
        
        # Si ce n'est pas le premier message du sujet (pour éviter la double notification)
        first_post = topic.posts.order_by('created_at').first()
        if first_post != instance:
            # Notifier les abonnés, sauf l'auteur du message
            subscribers = TopicSubscription.objects.filter(
                topic=topic,
                notify_on_new_post=True
            ).exclude(
                user=instance.author
            ).select_related('user')
            
            # Notifier chaque abonné
            try:
                from apps.notifications.services import NotificationService
                
                for subscription in subscribers:
                    NotificationService.create_notification(
                        user=subscription.user,
                        notification_type_code='forum_new_post',
                        context={
                            'topic_title': topic.title,
                            'category_name': topic.category.name,
                            'post_content': instance.content[:100] + ('...' if len(instance.content) > 100 else ''),
                            'author_name': instance.author.get_full_name() if instance.author else 'Système'
                        },
                        related_object=instance,
                        action_url=instance.get_absolute_url(),
                        action_text=_('Voir le message')
                    )
            except ImportError:
                # Le module notifications n'est pas disponible
                pass
            except Exception as e:
                # Une erreur s'est produite lors de l'envoi des notifications
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la notification des abonnés : {str(e)}")


@receiver(post_save, sender=Topic)
def handle_new_topic(sender, instance, created, **kwargs):
    """
    Signal pour gérer les nouveaux sujets.
    - Abonner automatiquement l'auteur au sujet
    """
    if created and instance.author:
        # Abonner automatiquement l'auteur au sujet
        TopicSubscription.objects.get_or_create(
            topic=instance,
            user=instance.author,
            defaults={'notify_on_new_post': True}
        )