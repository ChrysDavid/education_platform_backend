# apps/accounts/urls/mobile.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from ..views.mobile import (
    LogoutView,
    PupilRegistrationView,
    UserDetailAPIView,
    UserRegistrationView,
    StudentRegistrationView,
    TeacherRegistrationView,
    AdvisorRegistrationView,
    UserProfileView,
    ChangePasswordView,
    ProfilePictureView,
    StudentProfileView,
    PupilProfileView,
    TeacherProfileView,
    AdvisorProfileView,
    RequestVerificationView,
    UserTypeListView,
    VerificationStatusView,
    UserListView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = 'accounts_api'

urlpatterns = [
    # Routes d'authentification API
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
    
    # Routes d'inscription API
    path('register/', UserRegistrationView.as_view(), name='api_register'),
    path('register/student/', StudentRegistrationView.as_view(), name='api_register_student'),
    path('register/pupil/', PupilRegistrationView.as_view(), name='api_register_pupil'),
    path('register/teacher/', TeacherRegistrationView.as_view(), name='api_register_teacher'),
    path('register/advisor/', AdvisorRegistrationView.as_view(), name='api_register_advisor'),

    path('users/', UserListView.as_view(), name='api_user_list'),
    path('users/type/<str:user_type>/', UserTypeListView.as_view(), name='api_user_type_list'),
    path('users/profile/<int:pk>/', UserDetailAPIView.as_view(), name='api_user_detail'),
    
    # Routes de gestion du profil API
    path('profile/', UserProfileView.as_view(), name='api_user_profile'),
    path('profile/password/', ChangePasswordView.as_view(), name='api_change_password'),
    path('profile/picture/', ProfilePictureView.as_view(), name='api_profile_picture'),
    
    # Routes spécifiques au type d'utilisateur API
    path('profile/student/', StudentProfileView.as_view(), name='api_student_profile'),
    path('profile/pupil/', PupilProfileView.as_view(), name='api_pupil_profile'),
    path('profile/teacher/', TeacherProfileView.as_view(), name='api_teacher_profile'),
    path('profile/advisor/', AdvisorProfileView.as_view(), name='api_advisor_profile'),
    
    # Routes de vérification de compte API
    path('verification/request/', RequestVerificationView.as_view(), name='api_request_verification'),
    path('verification/status/', VerificationStatusView.as_view(), name='api_verification_status'),
    
    
    # Routes de réinitialisation de mot de passe API
    path('password/reset/', PasswordResetRequestView.as_view(), name='api_password_reset_request'),
    path('password/reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='api_password_reset_confirm'),
]