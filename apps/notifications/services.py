from django.db import transaction
from django.utils import timezone
from django.template import Template, Context
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import NotificationType, UserNotificationPreference, Notification, DeviceToken
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service pour gérer les notifications.
    """
    @classmethod
    def create_notification(cls, user, notification_type_code, context=None, related_object=None, 
                            action_url='', action_text='', send_now=True):
        """
        Crée une notification et l'envoie si demandé.
        
        Args:
            user: L'utilisateur destinataire de la notification
            notification_type_code: Le code du type de notification
            context: Dictionnaire de contexte pour rendre les templates
            related_object: Objet associé à la notification
            action_url: URL d'action
            action_text: Texte de l'action
            send_now: Si True, envoie la notification immédiatement
            
        Returns:
            La notification créée ou None si échec
        """
        try:
            notification_type = NotificationType.objects.get(code=notification_type_code, is_active=True)
        except NotificationType.DoesNotExist:
            logger.error(f"Type de notification inconnu: {notification_type_code}")
            return None
        
        if not context:
            context = {}
        
        # Ajouter l'utilisateur au contexte
        context['user'] = user
        django_context = Context(context)
        
        # Rendre les templates
        title_template = Template(notification_type.title_template)
        body_template = Template(notification_type.body_template)
        
        title = title_template.render(django_context)
        body = body_template.render(django_context)
        
        # Créer la notification
        with transaction.atomic():
            notification = Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=title,
                body=body,
                action_url=action_url,
                action_text=action_text,
                data=context,
                content_type=related_object._meta.app_label + '.' + related_object.__class__.__name__ if related_object else None,
                object_id=related_object.pk if related_object else None
            )
            
            # Envoyer la notification si demandé
            if send_now:
                cls.send_notification(notification)
                
            return notification
    
    @classmethod
    def send_notification(cls, notification):
        """
        Envoie une notification via tous les canaux configurés.
        
        Args:
            notification: La notification à envoyer
        """
        # Vérifier les préférences de l'utilisateur
        try:
            preferences = UserNotificationPreference.objects.get(
                user=notification.user,
                notification_type=notification.notification_type
            )
        except UserNotificationPreference.DoesNotExist:
            # Utiliser les paramètres par défaut
            preferences = UserNotificationPreference(
                user=notification.user,
                notification_type=notification.notification_type,
                email_enabled=notification.notification_type.default_user_preference,
                in_app_enabled=notification.notification_type.default_user_preference,
                push_enabled=notification.notification_type.default_user_preference
            )
        
        # Envoyer par email si activé
        if notification.notification_type.has_email and preferences.email_enabled:
            cls._send_email(notification)
        
        # Envoyer par push si activé
        if notification.notification_type.has_push and preferences.push_enabled:
            cls._send_push(notification)
        
        # In-app est déjà géré par la création de l'objet notification
    
    @classmethod
    def _send_email(cls, notification):
        """
        Envoie une notification par email.
        
        Args:
            notification: La notification à envoyer
        """
        try:
            # Rechercher un modèle d'email spécifique
            from .models import NotificationTemplate
            template = NotificationTemplate.objects.filter(
                notification_type=notification.notification_type,
                is_active=True
            ).first()
            
            if template and template.email_template:
                # Utiliser le modèle spécifique
                subject_template = Template(template.subject_template or notification.title)
                html_template = Template(template.email_template)
                
                context = Context(notification.data)
                subject = subject_template.render(context)
                html_content = html_template.render(context)
                
                # Version texte basique
                text_content = notification.body
                
                # Créer l'email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                # Utiliser un modèle par défaut
                subject = notification.title
                context = {
                    'notification': notification,
                    'user': notification.user,
                    'site_name': settings.SITE_NAME,
                    'site_url': settings.SITE_URL,
                }
                
                html_content = render_to_string('notifications/email/default_notification.html', context)
                text_content = notification.body
                
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[notification.user.email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            
            # Marquer l'email comme envoyé
            notification.sent_by_email = True
            notification.save(update_fields=['sent_by_email'])
            
        except Exception as e:
            logger.error(f"Erreur d'envoi d'email pour la notification {notification.pk}: {str(e)}")
    
    @classmethod
    def _send_push(cls, notification):
        """
        Envoie une notification push.
        
        Args:
            notification: La notification à envoyer
        """
        try:
            # Récupérer les tokens actifs de l'utilisateur
            tokens = DeviceToken.objects.filter(
                user=notification.user,
                is_active=True
            )
            
            if not tokens.exists():
                return
            
            # Configuration de base des notifications push
            push_data = {
                'title': notification.title,
                'body': notification.body,
                'icon': notification.notification_type.icon or 'default-icon',
                'click_action': notification.action_url or '',
                'notification_id': notification.pk,
            }
            
            # Implémenter ici la logique d'envoi via Firebase, OneSignal, etc.
            # Exemple pour Firebase Cloud Messaging:
            try:
                import firebase_admin
                from firebase_admin import messaging
                
                # Initialiser l'application Firebase si nécessaire
                if not firebase_admin._apps:
                    from firebase_admin import credentials
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                
                # Envoyer à chaque token
                for token in tokens:
                    # Adapter selon la plateforme
                    if token.platform == 'ios':
                        message = messaging.Message(
                            token=token.token,
                            notification=messaging.Notification(
                                title=notification.title,
                                body=notification.body,
                            ),
                            data=push_data,
                            apns=messaging.APNSConfig(
                                payload=messaging.APNSPayload(
                                    aps=messaging.Aps(
                                        badge=1,
                                        sound="default",
                                    )
                                )
                            )
                        )
                    else:  # Android ou Web
                        message = messaging.Message(
                            token=token.token,
                            notification=messaging.Notification(
                                title=notification.title,
                                body=notification.body,
                            ),
                            data=push_data,
                            android=messaging.AndroidConfig(
                                priority='high',
                                notification=messaging.AndroidNotification(
                                    icon='notification_icon',
                                    color='#427ef5',
                                    click_action=notification.action_url or '',
                                )
                            )
                        )
                    
                    # Envoyer
                    response = messaging.send(message)
                    logger.info(f"Notification push envoyée: {response}")
                    
                    # Mettre à jour la date de dernière utilisation du token
                    token.last_used_at = timezone.now()
                    token.save(update_fields=['last_used_at'])
                
                # Marquer comme envoyé
                notification.sent_by_push = True
                notification.save(update_fields=['sent_by_push'])
                
            except ImportError:
                logger.warning("Firebase non configuré - notifications push désactivées")
            except Exception as e:
                logger.error(f"Erreur d'envoi Firebase pour la notification {notification.pk}: {str(e)}")
                
        except Exception as e:
            logger.error(f"Erreur d'envoi push pour la notification {notification.pk}: {str(e)}")