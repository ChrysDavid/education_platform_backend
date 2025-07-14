from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import user_logged_in, user_logged_out
from django.contrib.auth.signals import user_login_failed
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from .models import UserActivity, AnalyticsEvent

# Suivi des connexions/déconnexions
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Enregistre une activité lorsqu'un utilisateur se connecte.
    """
    if hasattr(settings, 'TRACK_USER_ACTIVITY') and settings.TRACK_USER_ACTIVITY:
        UserActivity.log(
            user=user,
            action_type='login',
            action_detail='Connexion réussie',
            request=request
        )
        
        # Également suivre comme un événement analytique
        AnalyticsEvent.track(
            event_name='login',
            user=user,
            request=request
        )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Enregistre une activité lorsqu'un utilisateur se déconnecte.
    """
    if user and hasattr(settings, 'TRACK_USER_ACTIVITY') and settings.TRACK_USER_ACTIVITY:
        UserActivity.log(
            user=user,
            action_type='logout',
            action_detail='Déconnexion',
            request=request
        )
        
        # Également suivre comme un événement analytique
        AnalyticsEvent.track(
            event_name='logout',
            user=user,
            request=request
        )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """
    Enregistre une tentative de connexion échouée.
    """
    if hasattr(settings, 'TRACK_USER_ACTIVITY') and settings.TRACK_USER_ACTIVITY:
        # Essayer de trouver l'utilisateur par nom d'utilisateur/email
        User = get_user_model()
        username = credentials.get('username', '')
        email = credentials.get('email', username)
        
        user = None
        try:
            # Utiliser l'email ou le nom d'utilisateur pour trouver l'utilisateur
            if '@' in email:
                user = User.objects.filter(email=email).first()
            else:
                user = User.objects.filter(username=username).first()
        except Exception:
            pass
        
        # Créer l'entrée d'activité avec ou sans utilisateur
        UserActivity.log(
            user=user,
            action_type='login',
            action_detail='Tentative de connexion échouée',
            request=request,
            data={
                'username': username,
                'email': email
            }
        )
        
        # Suivre l'événement analytique
        AnalyticsEvent.track(
            event_name='login_failed',
            user=user,
            properties={
                'username': username,
                'email': email
            },
            request=request
        )

# Suivi des modifications utilisateur
@receiver(post_save, sender=get_user_model())
def log_user_updated(sender, instance, created, **kwargs):
    """
    Enregistre une activité lorsqu'un utilisateur est créé ou mis à jour.
    """
    if hasattr(settings, 'TRACK_USER_ACTIVITY') and settings.TRACK_USER_ACTIVITY:
        action_type = 'create' if created else 'update'
        action_detail = f"Utilisateur {'créé' if created else 'mis à jour'}"
        
        UserActivity.log(
            user=instance,
            action_type=action_type,
            action_detail=action_detail,
            related_object=instance
        )
        
        # Suivre l'événement analytique
        AnalyticsEvent.track(
            event_name=f"user_{action_type}",
            user=instance,
            properties={
                'user_id': instance.id,
                'email': instance.email,
                'is_staff': instance.is_staff,
                'is_active': instance.is_active,
                'date_joined': instance.date_joined.isoformat()
            }
        )

# Signal pour les autres modèles à suivre
def log_object_activity(sender, instance, created, **kwargs):
    """
    Fonction générique pour enregistrer l'activité sur n'importe quel modèle.
    
    Utilisez @receiver(post_save, sender=YourModel) avec cette fonction
    pour suivre l'activité de n'importe quel modèle.
    """
    if hasattr(settings, 'TRACK_USER_ACTIVITY') and settings.TRACK_USER_ACTIVITY:
        try:
            # Déterminer le responsable de l'action
            user = None
            
            # Vérifier si l'instance a un attribut créateur ou modifieur
            if hasattr(instance, 'created_by'):
                user = instance.created_by
            elif hasattr(instance, 'updated_by'):
                user = instance.updated_by
            elif hasattr(instance, 'user'):
                user = instance.user
            
            # Déterminer le type d'action et le détail
            action_type = 'create' if created else 'update'
            model_name = instance._meta.verbose_name
            
            UserActivity.log(
                user=user,
                action_type=action_type,
                action_detail=f"{model_name} {'créé' if created else 'mis à jour'} - ID: {instance.pk}",
                related_object=instance
            )
        except Exception as e:
            # Ne pas échouer si le suivi échoue
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du suivi de l'activité : {e}")

# Vous pouvez connecter ce signal à tous les modèles que vous souhaitez suivre
# Par exemple:
# @receiver(post_save, sender=School)
# def log_school_activity(sender, instance, created, **kwargs):
#     log_object_activity(sender, instance, created, **kwargs)