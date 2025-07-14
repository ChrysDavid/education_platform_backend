from django.test import TestCase
from django.urls import reverse, resolve

from apps.accounts.views import (
    UserRegistrationView, StudentRegistrationView, TeacherRegistrationView, AdvisorRegistrationView,
    UserProfileView, ChangePasswordView, ProfilePictureView, StudentProfileView,
    TeacherProfileView, AdvisorProfileView, RequestVerificationView, VerificationStatusView,
    UserListView, UserDetailView, PendingVerificationsView, ProcessVerificationView, 
    UserStatisticsView, PasswordResetRequestView, PasswordResetConfirmView
)


class UrlsTest(TestCase):
    """
    Tests pour les URL de l'application accounts.
    """
    
    def test_register_url(self):
        """
        Test que l'URL d'inscription standard résout vers la bonne vue.
        """
        url = reverse('accounts:register')
        self.assertEqual(resolve(url).func.view_class, UserRegistrationView)
    
    def test_register_student_url(self):
        """
        Test que l'URL d'inscription étudiant résout vers la bonne vue.
        """
        url = reverse('accounts:register_student')
        self.assertEqual(resolve(url).func.view_class, StudentRegistrationView)
    
    def test_register_teacher_url(self):
        """
        Test que l'URL d'inscription enseignant résout vers la bonne vue.
        """
        url = reverse('accounts:register_teacher')
        self.assertEqual(resolve(url).func.view_class, TeacherRegistrationView)
    
    def test_register_advisor_url(self):
        """
        Test que l'URL d'inscription conseiller résout vers la bonne vue.
        """
        url = reverse('accounts:register_advisor')
        self.assertEqual(resolve(url).func.view_class, AdvisorRegistrationView)
    
    def test_user_profile_url(self):
        """
        Test que l'URL de profil utilisateur résout vers la bonne vue.
        """
        url = reverse('accounts:user_profile')
        self.assertEqual(resolve(url).func.view_class, UserProfileView)
    
    def test_change_password_url(self):
        """
        Test que l'URL de changement de mot de passe résout vers la bonne vue.
        """
        url = reverse('accounts:change_password')
        self.assertEqual(resolve(url).func.view_class, ChangePasswordView)
    
    def test_profile_picture_url(self):
        """
        Test que l'URL de photo de profil résout vers la bonne vue.
        """
        url = reverse('accounts:profile_picture')
        self.assertEqual(resolve(url).func.view_class, ProfilePictureView)
    
    def test_student_profile_url(self):
        """
        Test que l'URL de profil étudiant résout vers la bonne vue.
        """
        url = reverse('accounts:student_profile')
        self.assertEqual(resolve(url).func.view_class, StudentProfileView)
    
    def test_teacher_profile_url(self):
        """
        Test que l'URL de profil enseignant résout vers la bonne vue.
        """
        url = reverse('accounts:teacher_profile')
        self.assertEqual(resolve(url).func.view_class, TeacherProfileView)
    
    def test_advisor_profile_url(self):
        """
        Test que l'URL de profil conseiller résout vers la bonne vue.
        """
        url = reverse('accounts:advisor_profile')
        self.assertEqual(resolve(url).func.view_class, AdvisorProfileView)
    
    def test_request_verification_url(self):
        """
        Test que l'URL de demande de vérification résout vers la bonne vue.
        """
        url = reverse('accounts:request_verification')
        self.assertEqual(resolve(url).func.view_class, RequestVerificationView)
    
    def test_verification_status_url(self):
        """
        Test que l'URL de statut de vérification résout vers la bonne vue.
        """
        url = reverse('accounts:verification_status')
        self.assertEqual(resolve(url).func.view_class, VerificationStatusView)
    
    def test_user_list_url(self):
        """
        Test que l'URL de liste d'utilisateurs résout vers la bonne vue.
        """
        url = reverse('accounts:user_list')
        self.assertEqual(resolve(url).func.view_class, UserListView)
    
    def test_user_detail_url(self):
        """
        Test que l'URL de détail d'utilisateur résout vers la bonne vue.
        """
        url = reverse('accounts:user_detail', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, UserDetailView)
    
    def test_pending_verifications_url(self):
        """
        Test que l'URL des vérifications en attente résout vers la bonne vue.
        """
        url = reverse('accounts:pending_verifications')
        self.assertEqual(resolve(url).func.view_class, PendingVerificationsView)
    
    def test_process_verification_url(self):
        """
        Test que l'URL de traitement de vérification résout vers la bonne vue.
        """
        url = reverse('accounts:process_verification', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, ProcessVerificationView)
    
    def test_user_statistics_url(self):
        """
        Test que l'URL des statistiques utilisateur résout vers la bonne vue.
        """
        url = reverse('accounts:user_statistics')
        self.assertEqual(resolve(url).func.view_class, UserStatisticsView)
    
    def test_password_reset_request_url(self):
        """
        Test que l'URL de demande de réinitialisation de mot de passe résout vers la bonne vue.
        """
        url = reverse('accounts:password_reset_request')
        self.assertEqual(resolve(url).func.view_class, PasswordResetRequestView)
    
    def test_password_reset_confirm_url(self):
        """
        Test que l'URL de confirmation de réinitialisation de mot de passe résout vers la bonne vue.
        """
        url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': 'test', 'token': 'test'})
        self.assertEqual(resolve(url).func.view_class, PasswordResetConfirmView)
