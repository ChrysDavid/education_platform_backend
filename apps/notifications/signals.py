from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import NotificationType, UserNotificationPreference, Notification

User = get_user_model()


@receiver(post_save, sender=User)
def create_default_notification_preferences(sender, instance, created, **kwargs):
    """
    Crée les préférences de notification par défaut pour un nouvel utilisateur.
    """
    if created:
        # Créer des préférences pour tous les types de notification actifs
        for notification_type in NotificationType.objects.filter(is_active=True):
            UserNotificationPreference.objects.create(
                user=instance,
                notification_type=notification_type,
                email_enabled=notification_type.default_user_preference,
                in_app_enabled=notification_type.default_user_preference,
                push_enabled=notification_type.default_user_preference
            )
        
        # Envoyer une notification de bienvenue
        from .services import NotificationService
        
        # Si un type de notification "welcome" existe, l'utiliser
        if NotificationType.objects.filter(code='welcome', is_active=True).exists():
            NotificationService.create_notification(
                user=instance,
                notification_type_code='welcome',
                context={
                    'first_name': instance.first_name,
                },
                action_url='/profile/',
                action_text=_('Voir mon profil')
            )


@receiver(post_save, sender=NotificationType)
def create_notification_preferences_for_new_type(sender, instance, created, **kwargs):
    """
    Crée les préférences de notification pour tous les utilisateurs
    quand un nouveau type de notification est créé.
    """
    if created and instance.is_active:
        # Récupérer tous les utilisateurs n'ayant pas de préférence pour ce type
        users_without_preference = User.objects.exclude(
            notification_preferences__notification_type=instance
        )
        
        # Créer des préférences pour ces utilisateurs
        preferences_to_create = [
            UserNotificationPreference(
                user=user,
                notification_type=instance,
                email_enabled=instance.default_user_preference,
                in_app_enabled=instance.default_user_preference,
                push_enabled=instance.default_user_preference
            )
            for user in users_without_preference
        ]
        
        if preferences_to_create:
            UserNotificationPreference.objects.bulk_create(preferences_to_create)