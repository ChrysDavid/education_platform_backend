# Ce fichier permet l'importation depuis le dossier views
# Importation des vues mobiles pour maintenir la compatibilité avec le code existant

from .mobile import (
    UserRegistrationView,
    StudentRegistrationView,
    TeacherRegistrationView,
    AdvisorRegistrationView,
    UserProfileView,
    ChangePasswordView,
    ProfilePictureView,
    StudentProfileView,
    TeacherProfileView,
    AdvisorProfileView,
    RequestVerificationView,
    VerificationStatusView,
    UserListView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

# Exporter toutes les vues pour l'API mobile
__all__ = [
    'UserRegistrationView',
    'StudentRegistrationView',
    'TeacherRegistrationView',
    'AdvisorRegistrationView',
    'UserProfileView',
    'ChangePasswordView',
    'ProfilePictureView',
    'StudentProfileView',
    'TeacherProfileView',
    'AdvisorProfileView',
    'RequestVerificationView',
    'VerificationStatusView',
    'UserListView',
    'PasswordResetRequestView',
    'PasswordResetConfirmView',
]