# apps/accounts/urls/web.py
from django.urls import path
from django.contrib.auth import views as auth_views
from ..views.web import (
    DashboardView,
    LoginView,
    RegisterView,
    ProfileView,
    PasswordChangeView,
    UserListView,
    UserDetailView,
    PendingVerificationsView,
    ProcessVerificationView,
    UserStatisticsView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

app_name = 'accounts'

urlpatterns = [

    # Routes d'authentification (site web)
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    
    # Routes d'inscription (site web)
    path('register/', RegisterView.as_view(), name='register'),
    path('register/student/', RegisterView.as_view(), {'user_type': 'student'}, name='register_student'),
    path('register/teacher/', RegisterView.as_view(), {'user_type': 'teacher'}, name='register_teacher'),
    path('register/advisor/', RegisterView.as_view(), {'user_type': 'advisor'}, name='register_advisor'),
    

    # Routes de gestion du profil (site web)
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/password/', PasswordChangeView.as_view(), name='password_change'),
    
    
    # Routes d'administration (site web - interface admin personnalisée)
    path('admin/dashboard/', DashboardView.as_view(), name='admin_dashboard'),
    path('admin/users/', UserListView.as_view(), name='user_list'),
    path('admin/users/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('admin/verification/', PendingVerificationsView.as_view(), name='pending_verifications'),
    path('admin/verification/<int:pk>/', ProcessVerificationView.as_view(), name='process_verification'),
    path('admin/statistics/', UserStatisticsView.as_view(), name='user_statistics'),
    
    # Routes de réinitialisation de mot de passe (site web)
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]