# Ce fichier permet l'importation depuis le dossier serializers
# Importation des sérialiseurs de base pour être accessibles directement
from .base import (
    UserBaseSerializer,
)

# Importation des sérialiseurs pour le web
from .web import (
    UserWebSerializer,
    StudentWebSerializer,
    TeacherWebSerializer,
    AdvisorWebSerializer,
    AdministratorWebSerializer,
)

# Importation des sérialiseurs pour l'API mobile
from .mobile import (
    UserSerializer,
    UserDetailSerializer,
    ChangePasswordSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    AdvisorProfileSerializer,
    AdministratorProfileSerializer,
    UserRegistrationSerializer,
    StudentRegistrationSerializer,
    TeacherRegistrationSerializer,
    AdvisorRegistrationSerializer,
    ProfilePictureSerializer,
)