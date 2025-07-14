# apps/accounts/services.py
from venv import logger
from django.db import IntegrityError
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

from .models import User, Student, Teacher, Advisor, Administrator
from apps.notifications.models import Notification  # À importer si le modèle existe


class AccountService:
    """
    Service pour gérer les opérations liées aux comptes utilisateurs.
    """
    
    @staticmethod
    def register_user(user_data, user_type_data=None):
        """
        Inscrit un nouvel utilisateur avec son profil spécifique.
        
        Args:
            user_data (dict): Données de base de l'utilisateur
            user_type_data (dict, optional): Données spécifiques au type d'utilisateur
            
        Returns:
            User: L'utilisateur créé
        """
        # Création de l'utilisateur de base
        user = User.objects.create_user(
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            phone_number=user_data.get('phone_number', ''),
            date_of_birth=user_data.get('date_of_birth'),
            address=user_data.get('address', ''),
            city=user_data.get('city', ''),
            type=user_data['type'],
            verification_status='unverified'
        )
        
        # Création du profil spécifique si des données sont fournies
        if user_type_data:
            if user.type == 'student':
                student = Student.objects.get(user=user)
                for key, value in user_type_data.items():
                    setattr(student, key, value)
                student.save()
            elif user.type == 'teacher':
                teacher = Teacher.objects.get(user=user)
                for key, value in user_type_data.items():
                    setattr(teacher, key, value)
                teacher.save()
            elif user.type == 'advisor':
                advisor = Advisor.objects.get(user=user)
                for key, value in user_type_data.items():
                    setattr(advisor, key, value)
                advisor.save()
            elif user.type == 'administrator':
                admin = Administrator.objects.get(user=user)
                for key, value in user_type_data.items():
                    setattr(admin, key, value)
                admin.save()
        
        # Envoyer un email de bienvenue
        if settings.SEND_WELCOME_EMAIL:
            try:
                AccountService.send_welcome_email(user)
            except Exception as e:
                # Journaliser l'erreur mais continuer
                print(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
        
        return user
    
    @staticmethod
    def update_user_profile(user, user_data, user_type_data=None):
        """
        Met à jour le profil d'un utilisateur existant.
        
        Args:
            user (User): L'utilisateur à mettre à jour
            user_data (dict): Nouvelles données de base
            user_type_data (dict, optional): Nouvelles données spécifiques au type
            
        Returns:
            User: L'utilisateur mis à jour
        """
        # Mise à jour des données de base
        for key, value in user_data.items():
            if key not in ['password', 'email', 'type']:  # Ne pas mettre à jour ces champs
                setattr(user, key, value)
        user.save()
        
        # Mise à jour du profil spécifique
        if user_type_data:
            if user.type == 'student' and hasattr(user, 'student_profile'):
                for key, value in user_type_data.items():
                    setattr(user.student_profile, key, value)
                user.student_profile.save()
            elif user.type == 'teacher' and hasattr(user, 'teacher_profile'):
                for key, value in user_type_data.items():
                    setattr(user.teacher_profile, key, value)
                user.teacher_profile.save()
            elif user.type == 'advisor' and hasattr(user, 'advisor_profile'):
                for key, value in user_type_data.items():
                    setattr(user.advisor_profile, key, value)
                user.advisor_profile.save()
            elif user.type == 'administrator' and hasattr(user, 'administrator_profile'):
                for key, value in user_type_data.items():
                    setattr(user.administrator_profile, key, value)
                user.administrator_profile.save()
        
        return user
    
    @staticmethod
    def request_verification(user):
        """
        Initie le processus de vérification d'un utilisateur.
        
        Args:
            user (User): L'utilisateur demandant la vérification
            
        Returns:
            bool: True si la demande a été créée avec succès
        """
        # Vérifier que l'utilisateur n'est pas déjà vérifié ou en attente
        if user.verification_status in ['verified', 'pending']:
            return False
        
        # Mettre à jour le statut de l'utilisateur
        user.verification_status = 'pending'
        user.verification_requested_date = timezone.now()
        user.save(update_fields=['verification_status', 'verification_requested_date'])
        
        # Créer une notification pour les administrateurs
        try:
            admins = User.objects.filter(type='administrator', is_active=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    content=f"Nouvelle demande de vérification de {user.get_full_name()} ({user.email}).",
                    notification_type="verification_request"
                )
        except Exception:
            # Si le modèle Notification n'est pas disponible ou en cas d'erreur
            pass
        
        return True
    
    @staticmethod
    def verify_user(user, admin, approved=True, notes=''):
        """
        Approuve ou rejette la demande de vérification d'un utilisateur.
        
        Args:
            user (User): L'utilisateur à vérifier
            admin (User): L'administrateur effectuant la vérification
            approved (bool): Approuver ou rejeter la vérification
            notes (str): Notes de vérification
            
        Returns:
            bool: True si la vérification a été effectuée avec succès
        """
        # Vérifier que l'utilisateur est en attente de vérification
        if user.verification_status != 'pending':
            return False
        
        # Mettre à jour le statut et les notes
        user.verification_status = 'verified' if approved else 'rejected'
        user.verification_completed_date = timezone.now()
        user.verification_notes = notes
        user.save(update_fields=[
            'verification_status', 'verification_completed_date', 'verification_notes'
        ])
        
        # Notifier l'utilisateur
        try:
            status_text = "vérifiée" if approved else "rejetée"
            content = f"Votre demande de vérification a été {status_text}."
            
            if not approved and notes:
                content += f" Raison: {notes}"
            
            Notification.objects.create(
                user=user,
                content=content,
                notification_type="verification_result"
            )
        except Exception:
            # Si le modèle Notification n'est pas disponible ou en cas d'erreur
            pass
        
        # Envoyer un email de notification
        try:
            subject = "Résultat de votre demande de vérification"
            template = 'emails/verification_approved.html' if approved else 'emails/verification_rejected.html'
            context = {
                'user': user,
                'notes': notes
            }
            
            html_message = render_to_string(template, context)
            
            send_mail(
                subject=subject,
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
        except Exception as e:
            # Journaliser l'erreur mais continuer
            print(f"Erreur lors de l'envoi de l'email de vérification: {e}")
        
        return True
    
    @staticmethod
    def send_welcome_email(user):
        """
        Envoie un email de bienvenue à un nouvel utilisateur.
        
        Args:
            user (User): L'utilisateur qui vient de s'inscrire
            
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        subject = "Bienvenue sur notre plateforme éducative"
        context = {
            'user': user,
            'platform_name': settings.PLATFORM_NAME,
            'contact_email': settings.CONTACT_EMAIL
        }
        
        html_message = render_to_string('emails/welcome.html', context)
        
        return send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
    

    @staticmethod
    def register_advisor(user_data, advisor_data, files=None):
        """
        Inscrit un nouveau conseiller avec son profil complet.
        """
        try:
            # Vérifier si l'utilisateur existe déjà
            if User.objects.filter(email=user_data['email']).exists():
                user = User.objects.get(email=user_data['email'])
                if hasattr(user, 'advisor_profile'):
                    raise ValueError("Un profil conseiller existe déjà pour cet utilisateur")
            
            # Création de l'utilisateur de base
            user = User.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone_number=user_data.get('phone_number', ''),
                date_of_birth=user_data.get('date_of_birth'),
                address=user_data.get('address', ''),
                city=user_data.get('city', ''),
                type='advisor',
                verification_status='pending'
            )
            
            # Gestion des fichiers
            identity_doc = files.get('identity_document') if files else None
            portfolio_file = files.get('portfolio') if files else None
            cert_docs = files.get('certification_documents', []) if files else []
            
            # Création du profil conseiller
            advisor = Advisor.objects.create(
                user=user,
                organization=advisor_data['organization'],
                specialization=advisor_data['specialization'],
                years_of_experience=advisor_data.get('years_of_experience', 0),
                professional_license=advisor_data.get('professional_license', ''),
                certifications=advisor_data.get('certifications', []),
                geographical_areas=advisor_data.get('geographical_areas', []),
                rates=advisor_data.get('rates', {}),
                portfolio_link=advisor_data.get('portfolio_link', ''),
                identity_document=identity_doc,
                portfolio=portfolio_file,
                certification_documents=[doc.name for doc in cert_docs] if cert_docs else []
            )
            
            # Envoyer un email de bienvenue si configuré
            if settings.SEND_WELCOME_EMAIL:
                try:
                    AccountService.send_welcome_email(user)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi de l'email de bienvenue: {e}")
            
            return user, advisor
        except IntegrityError as e:
            logger.error(f"Erreur d'intégrité lors de la création du conseiller: {e}")
            raise ValueError("Erreur lors de la création du profil conseiller")
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'inscription du conseiller: {e}")
            raise











    @staticmethod
    def send_password_reset_email(user, token):
        """
        Envoie un email de réinitialisation de mot de passe.
        
        Args:
            user (User): L'utilisateur demandant la réinitialisation
            token (str): Le token de réinitialisation
            
        Returns:
            bool: True si l'email a été envoyé avec succès
        """
        subject = "Réinitialisation de votre mot de passe"
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        context = {
            'user': user,
            'platform_name': settings.PLATFORM_NAME,
            'reset_url': f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        }
        
        html_message = render_to_string('emails/password_reset.html', context)
        
        return send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
    
    @staticmethod
    def get_user_stats():
        """
        Récupère des statistiques sur les utilisateurs.
        
        Returns:
            dict: Statistiques des utilisateurs
        """
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Statistiques par type
        students_count = User.objects.filter(type='student').count()
        teachers_count = User.objects.filter(type='teacher').count()
        advisors_count = User.objects.filter(type='advisor').count()
        admins_count = User.objects.filter(type='administrator').count()
        
        # Statistiques de vérification
        verified_count = User.objects.filter(verification_status='verified').count()
        pending_count = User.objects.filter(verification_status='pending').count()
        rejected_count = User.objects.filter(verification_status='rejected').count()
        unverified_count = User.objects.filter(verification_status='unverified').count()
        
        # Statistiques temporelles
        now = timezone.now()
        month_ago = now - timezone.timedelta(days=30)
        
        new_users_this_month = User.objects.filter(date_joined__gte=month_ago).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'students_count': students_count,
            'teachers_count': teachers_count,
            'advisors_count': advisors_count,
            'admins_count': admins_count,
            'verified_count': verified_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'unverified_count': unverified_count,
            'new_users_this_month': new_users_this_month,
        }