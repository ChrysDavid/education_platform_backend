from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from .models import Appointment, AppointmentReminder

@receiver(post_save, sender=Appointment)
def create_appointment_reminders(sender, instance, created, **kwargs):
    """
    Crée automatiquement des rappels pour un rendez-vous à la création.
    """
    if created:
        # Créer un rappel 24 heures avant
        AppointmentReminder.objects.create(
            appointment=instance,
            reminder_type='email',
            minutes_before=24 * 60  # 24 heures en minutes
        )
        
        # Créer un rappel 1 heure avant
        AppointmentReminder.objects.create(
            appointment=instance,
            reminder_type='all',
            minutes_before=60  # 1 heure en minutes
        )

@receiver(pre_save, sender=Appointment)
def update_appointment_status_on_reschedule(sender, instance, **kwargs):
    """
    Met à jour le statut du rendez-vous si la date a été modifiée.
    """
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            if old_instance.schedule_time != instance.schedule_time:
                # La date a été modifiée, marquer comme reporté
                if instance.status == 'confirmed':
                    instance.status = 'rescheduled'
        except Appointment.DoesNotExist:
            pass  # Nouvel objet, rien à faire

@receiver(pre_save, sender=Appointment)
def calculate_end_time(sender, instance, **kwargs):
    """
    Calcule automatiquement l'heure de fin si elle n'est pas spécifiée.
    """
    import datetime
    if instance.schedule_time and not instance.end_time:
        instance.end_time = instance.schedule_time + datetime.timedelta(minutes=instance.duration_minutes)

@receiver(post_save, sender=Appointment)
def notify_users_on_status_change(sender, instance, created, **kwargs):
    """
    Envoie des notifications aux utilisateurs lors des changements de statut.
    """
    # Ce signal est un point d'extension pour intégrer avec l'application de notifications
    if not created and hasattr(settings, 'ENABLE_APPOINTMENT_NOTIFICATIONS') and settings.ENABLE_APPOINTMENT_NOTIFICATIONS:
        try:
            # Importer ici pour éviter les dépendances circulaires
            from apps.notifications.services import create_notification
            
            old_instance = getattr(instance, '_old_instance', None)
            if old_instance and old_instance.status != instance.status:
                # Le statut a changé, envoyer des notifications
                
                # Notification pour le demandeur
                create_notification(
                    user=instance.requester,
                    notification_type='appointment_status_changed',
                    title=f"Statut du rendez-vous modifié: {instance.get_status_display()}",
                    body=f"Le statut de votre rendez-vous '{instance.title}' avec {instance.recipient.get_full_name()} a été modifié à {instance.get_status_display()}.",
                    data={
                        'appointment_id': instance.id,
                        'status': instance.status,
                        'schedule_time': instance.schedule_time.isoformat(),
                    },
                    related_object=instance
                )
                
                # Notification pour le destinataire
                create_notification(
                    user=instance.recipient,
                    notification_type='appointment_status_changed',
                    title=f"Statut du rendez-vous modifié: {instance.get_status_display()}",
                    body=f"Le statut du rendez-vous '{instance.title}' avec {instance.requester.get_full_name()} a été modifié à {instance.get_status_display()}.",
                    data={
                        'appointment_id': instance.id,
                        'status': instance.status,
                        'schedule_time': instance.schedule_time.isoformat(),
                    },
                    related_object=instance
                )
        except ImportError:
            # L'application de notifications n'est pas disponible
            pass
        except Exception as e:
            # Enregistrer l'erreur mais ne pas interrompre la sauvegarde
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'envoi des notifications de rendez-vous: {e}")

# Capturer l'état précédent de l'instance pour les comparaisons
@receiver(pre_save, sender=Appointment)
def store_old_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = Appointment.objects.get(pk=instance.pk)
        except Appointment.DoesNotExist:
            pass