# apps/accounts/views/mobile.py
from venv import logger
import json
from django.forms import ValidationError
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404

from ..models import User, Student, Teacher, Advisor, Pupil
from ..serializers.mobile import (
    PupilRegistrationSerializer, UserSerializer, UserDetailSerializer, ChangePasswordSerializer,
    StudentProfileSerializer, TeacherProfileSerializer, AdvisorProfileSerializer,
    UserRegistrationSerializer, StudentRegistrationSerializer,
    TeacherRegistrationSerializer, AdvisorRegistrationSerializer,
    ProfilePictureSerializer, PupilProfileSerializer
)
from ..permissions import (
    IsOwnerOrAdmin, IsAdministrator, IsVerified,
    IsStudent, IsTeacher, IsAdvisor, IsPupil
)
from ..services import AccountService



import logging


logger = logging.getLogger(__name__)






class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class UserRegistrationView(generics.CreateAPIView):
    """
    Vue pour l'inscription d'un utilisateur standard.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("Inscription réussie. Veuillez vous connecter.")},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




class UserTypeListView(generics.ListAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]  # Doit être présent
    
    def get_queryset(self):
        user_type = self.kwargs['user_type']
        return User.objects.filter(type=user_type, is_active=True)
    



class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    lookup_field = 'pk'









class PupilRegistrationView(generics.CreateAPIView):
    serializer_class = PupilRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.save()
            
            return Response({
                "success": True,
                "message": "Inscription réussie",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "type": user.type
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription: {str(e)}")
            return Response({
                "success": False,
                "message": str(e),
                "errors": serializer.errors if 'serializer' in locals() else None
            }, status=status.HTTP_400_BAD_REQUEST)
    









class StudentRegistrationView(generics.CreateAPIView):
    serializer_class = StudentRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                
                return Response(
                    {
                        "message": _("Inscription réussie."),
                        "user": UserSerializer(user).data,
                        "token": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        },
                    },
                    status=status.HTTP_201_CREATED
                )
            except IntegrityError:
                return Response(
                    {"message": _("Un profil étudiant existe déjà pour cet utilisateur.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"message": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class PupilProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil élève de l'utilisateur.
    """
    serializer_class = PupilProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsPupil]
    
    def get_object(self):
        return get_object_or_404(Pupil, user=self.request.user)










class TeacherRegistrationView(generics.CreateAPIView):
    """
    Vue pour l'inscription d'un enseignant avec profil complet.
    Gère la création de l'utilisateur et du profil enseignant en une transaction atomique.
    """
    serializer_class = TeacherRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        logger.info(f"Tentative d'inscription enseignant: {request.data.keys()}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Données invalides lors de l'inscription: {serializer.errors}")
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                    "message": _("Données d'inscription invalides")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user = serializer.save()
                
                # Envoyer un email de confirmation
                try:
                    from ..services import AccountService
                    AccountService.send_welcome_email(user)
                except Exception as email_error:
                    logger.warning(f"Échec de l'envoi de l'email de bienvenue: {email_error}")
                    # Ne pas faire échouer l'inscription si l'email ne peut pas être envoyé
                
                logger.info(f"Inscription réussie pour l'utilisateur: {user.email}")
                
                # Générer les tokens JWT
                refresh = RefreshToken.for_user(user)
                
                return Response(
                            {
                                "success": True,
                                "message": _("Inscription réussie."),
                                "user": {
                                    "id": user.id,
                                    "email": user.email,
                                    "first_name": user.first_name,
                                    "last_name": user.last_name,
                                    "type": user.type,
                                    "verification_status": user.verification_status,
                                },
                                "tokens": {
                                    "refresh": str(refresh),
                                    "access": str(refresh.access_token),
                                }
                            },
                            status=status.HTTP_201_CREATED,
                            content_type="application/json"
                        )
        
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'enseignant: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": _("Erreur lors de la création du compte"),
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        



















class AdvisorRegistrationView(generics.CreateAPIView):
    """
    Vue pour l'inscription d'un conseiller avec profil complet.
    """
    serializer_class = AdvisorRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        logger.info(f"Tentative d'inscription conseiller: {request.data.keys()}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Données invalides lors de l'inscription: {serializer.errors}")
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors,
                    "message": _("Données d'inscription invalides")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                user = serializer.save()
                
                # Envoyer un email de confirmation
                try:
                    from ..services import AccountService
                    AccountService.send_welcome_email(user)
                except Exception as email_error:
                    logger.warning(f"Échec de l'envoi de l'email de bienvenue: {email_error}")
                
                logger.info(f"Inscription réussie pour le conseiller: {user.email}")
                
                # Générer les tokens JWT
                refresh = RefreshToken.for_user(user)
                
                return Response(
                    {
                        "success": True,
                        "message": _("Inscription réussie."),
                        "user": {
                            "id": user.id,
                            "email": user.email,
                            "first_name": user.first_name,
                            "last_name": user.last_name,
                            "type": user.type,
                            "verification_status": user.verification_status,
                        },
                        "tokens": {
                            "refresh": str(refresh),
                            "access": str(refresh.access_token),
                        }
                    },
                    status=status.HTTP_201_CREATED,
                    content_type="application/json"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du conseiller: {str(e)}")
            return Response(
                {
                    "success": False,
                    "message": _("Erreur lors de la création du compte"),
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )












class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil de l'utilisateur actuel.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("Inscription réussie.")},
                status=status.HTTP_201_CREATED
            )
        print(serializer.errors)  # 🔥 Ajoute ceci pour voir l'erreur dans la console Django
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """
    Vue pour permettre à l'utilisateur de changer son mot de passe.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("Votre mot de passe a été modifié avec succès.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilePictureView(APIView):
    """
    Vue pour permettre à l'utilisateur de télécharger ou mettre à jour sa photo de profil.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        serializer = ProfilePictureSerializer(data=request.data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": _("Photo de profil mise à jour avec succès.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil étudiant de l'utilisateur.
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    
    def get_object(self):
        return get_object_or_404(Student, user=self.request.user)


class TeacherProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil enseignant de l'utilisateur.
    """
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]
    
    def get_object(self):
        return get_object_or_404(Teacher, user=self.request.user)


class AdvisorProfileView(generics.RetrieveUpdateAPIView):
    """
    Vue pour récupérer et mettre à jour le profil conseiller de l'utilisateur.
    """
    serializer_class = AdvisorProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdvisor]
    
    def get_object(self):
        return get_object_or_404(Advisor, user=self.request.user)


class RequestVerificationView(APIView):
    """
    Vue pour demander la vérification du compte utilisateur.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Vérifier si l'utilisateur est déjà vérifié ou en attente
        if user.verification_status == 'verified':
            return Response(
                {"message": _("Votre compte est déjà vérifié.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif user.verification_status == 'pending':
            return Response(
                {"message": _("Votre demande de vérification est déjà en cours de traitement.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Soumettre la demande de vérification
        success = AccountService.request_verification(user)
        
        if success:
            return Response(
                {"message": _("Votre demande de vérification a été soumise avec succès. Un administrateur la traitera prochainement.")},
                status=status.HTTP_200_OK
            )
        return Response(
            {"message": _("Impossible de soumettre votre demande de vérification. Veuillez réessayer plus tard.")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VerificationStatusView(APIView):
    """
    Vue pour consulter le statut de vérification de l'utilisateur actuel.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        data = {
            "status": user.verification_status,
            "status_display": user.get_verification_status_display(),
            "requested_date": user.verification_requested_date,
            "completed_date": user.verification_completed_date,
            "notes": user.verification_notes if user.verification_status == 'rejected' else None
        }
        
        return Response(data, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    Vue pour lister tous les utilisateurs (pour les administrateurs).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdministrator]
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filtrage par type d'utilisateur
        user_type = self.request.query_params.get('type')
        if user_type:
            queryset = queryset.filter(type=user_type)
        
        # Filtrage par statut de vérification
        verification_status = self.request.query_params.get('verification_status')
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        # Recherche par nom ou email
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                first_name__icontains=search_query
            ) | queryset.filter(
                last_name__icontains=search_query
            ) | queryset.filter(
                email__icontains=search_query
            )
        
        return queryset




class PasswordResetRequestView(APIView):
    """
    Vue pour demander une réinitialisation de mot de passe.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"message": _("L'adresse e-mail est requise.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            
            # Envoyer l'email de réinitialisation
            success = AccountService.send_password_reset_email(user, token)
            
            if success:
                return Response(
                    {"message": _("Un email de réinitialisation de mot de passe a été envoyé à votre adresse email.")},
                    status=status.HTTP_200_OK
                )
            return Response(
                {"message": _("Impossible d'envoyer l'email de réinitialisation. Veuillez réessayer plus tard.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except User.DoesNotExist:
            # Pour des raisons de sécurité, ne pas révéler que l'utilisateur n'existe pas
            return Response(
                {"message": _("Si cette adresse email est associée à un compte, un email de réinitialisation sera envoyé.")},
                status=status.HTTP_200_OK
            )


class PasswordResetConfirmView(APIView):
    """
    Vue pour confirmer et effectuer la réinitialisation du mot de passe.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, uidb64, token):
        try:
            # Décodage de l'UID
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            # Vérification du token
            if not default_token_generator.check_token(user, token):
                return Response(
                    {"message": _("Le lien de réinitialisation de mot de passe est invalide ou a expiré.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupération et validation du nouveau mot de passe
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')
            
            if not new_password or not confirm_password:
                return Response(
                    {"message": _("Veuillez fournir un nouveau mot de passe et sa confirmation.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_password != confirm_password:
                return Response(
                    {"message": _("Les mots de passe ne correspondent pas.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mise à jour du mot de passe
            user.set_password(new_password)
            user.save()
            
            return Response(
                {"message": _("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")},
                status=status.HTTP_200_OK
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"message": _("Le lien de réinitialisation de mot de passe est invalide.")},
                status=status.HTTP_400_BAD_REQUEST
            )


# Classes API supplémentaires pour les fonctionnalités mobiles spécifiques

class UserVerificationDocumentsView(APIView):
    """
    Vue pour gérer les documents de vérification des utilisateurs.
    Permet l'upload et la gestion des documents requis pour la vérification.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request):
        # Récupérer les documents de vérification de l'utilisateur
        from ..models import VerificationDocument
        documents = VerificationDocument.objects.filter(user=request.user)
        
        # Sérialiser et retourner les documents
        from ..serializers.mobile import VerificationDocumentSerializer
        serializer = VerificationDocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        # Ajouter un nouveau document de vérification
        from ..serializers.mobile import VerificationDocumentSerializer
        serializer = VerificationDocumentSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": _("Document de vérification ajouté avec succès.")},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeviceRegistrationView(APIView):
    """
    Vue pour enregistrer un appareil mobile pour les notifications push.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        device_token = request.data.get('device_token')
        device_type = request.data.get('device_type')  # 'ios' ou 'android'
        
        if not device_token or not device_type:
            return Response(
                {"message": _("Le token et le type d'appareil sont requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enregistrer le token de l'appareil
        from ..models import UserDevice
        
        # Suppression des anciens tokens pour cet utilisateur et ce type d'appareil
        UserDevice.objects.filter(user=request.user, device_type=device_type).delete()
        
        # Création d'un nouveau token
        UserDevice.objects.create(
            user=request.user,
            device_token=device_token,
            device_type=device_type
        )
        
        return Response(
            {"message": _("Appareil enregistré avec succès pour les notifications.")},
            status=status.HTTP_201_CREATED
        )


class UserNotificationsView(generics.ListAPIView):
    """
    Vue pour récupérer les notifications de l'utilisateur connecté.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        from ..serializers.mobile import NotificationSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        from apps.notifications.models import Notification
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


class MarkNotificationAsReadView(APIView):
    """
    Vue pour marquer une notification comme lue.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        from apps.notifications.models import Notification
        
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            
            return Response(
                {"message": _("Notification marquée comme lue.")},
                status=status.HTTP_200_OK
            )
        except Notification.DoesNotExist:
            return Response(
                {"message": _("Notification non trouvée.")},
                status=status.HTTP_404_NOT_FOUND
            )