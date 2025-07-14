from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import User, Student, Teacher, Advisor, Pupil, Administrator
from apps.notifications.models import Notification  # Importation supposée, peut nécessiter un ajustement





@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not instance.is_staff:
        if instance.type == 'student' and not hasattr(instance, 'student_profile'):
            Student.objects.create(user=instance)
        elif instance.type == 'teacher' and not hasattr(instance, 'teacher_profile'):
            Teacher.objects.create(user=instance)
        

        



        


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    """
    Envoie une notification de bienvenue à l'utilisateur lors de sa création.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance,
                content="Bienvenue sur la plateforme ! Complétez votre profil pour une meilleure expérience.",
                notification_type="welcome"
            )
        except Exception:
            # Gérer le cas où le modèle Notification n'est pas disponible
            pass


@receiver(post_save, sender=Student)
def notify_student_profile_creation(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsque le profil étudiant est créé.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance.user,
                content="Votre profil étudiant a été créé avec succès.",
                notification_type="profile_created"
            )
        except Exception:
            pass



@receiver(post_save, sender=Pupil)
def notify_pupil_profile_creation(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsque le profil élève est créé.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance.user,
                content="Votre profil élève a été créé avec succès.",
                notification_type="profile_created"
            )
        except Exception:
            pass




@receiver(post_save, sender=Teacher)
def notify_teacher_profile_creation(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsque le profil enseignant est créé.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance.user,
                content="Votre profil enseignant a été créé avec succès.",
                notification_type="profile_created"
            )
        except Exception:
            pass


@receiver(post_save, sender=Advisor)
def notify_advisor_profile_creation(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsque le profil conseiller est créé.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance.user,
                content="Votre profil conseiller a été créé avec succès.",
                notification_type="profile_created"
            )
        except Exception:
            pass


@receiver(post_save, sender=Administrator)
def notify_admin_profile_creation(sender, instance, created, **kwargs):
    """
    Envoie une notification lorsque le profil administrateur est créé.
    """
    if created:
        try:
            Notification.objects.create(
                user=instance.user,
                content="Votre profil administrateur a été créé avec succès.",
                notification_type="profile_created"
            )
        except Exception:
            pass



@receiver(post_save, sender=User)
def handle_new_user_verification(sender, instance, created, **kwargs):
    """
    Gère le statut de vérification pour les nouveaux utilisateurs.
    """
    if created:
        # Pour les nouveaux utilisateurs non-admins, définir le statut 'unverified'
        if not instance.is_staff and not instance.is_superuser:
            instance.verification_status = 'unverified'
            instance.save(update_fields=['verification_status'])