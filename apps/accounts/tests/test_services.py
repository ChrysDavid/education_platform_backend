from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import timedelta

from apps.accounts.models import User, Student, Teacher, Advisor, Administrator
from apps.accounts.services import AccountService


class AccountServiceTest(TestCase):
    """
    Tests pour le service AccountService.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user_data = {
            'email': 'user@example.com',
            'password': 'securepass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',
            'type': 'student'
        }
        
        self.student_data = {
            'current_level': 'Licence 2',
            'major': 'Informatique',
            'interests': ['Programmation', 'IA']
        }
    
    def test_register_user_basic(self):
        """
        Test d'inscription d'un utilisateur de base.
        """
        with patch('apps.accounts.services.AccountService.send_welcome_email') as mock_send_email:
            # Configurer le mock pour simuler l'envoi d'email
            mock_send_email.return_value = True
            
            # Créer un utilisateur via le service
            user = AccountService.register_user(self.user_data)
            
            # Vérifier que l'utilisateur a été créé correctement
            self.assertEqual(user.email, self.user_data['email'])
            self.assertEqual(user.first_name, self.user_data['first_name'])
            self.assertEqual(user.last_name, self.user_data['last_name'])
            self.assertEqual(user.phone_number, self.user_data['phone_number'])
            self.assertEqual(user.type, self.user_data['type'])
            self.assertEqual(user.verification_status, 'unverified')
            
            # Vérifier que le mot de passe a été correctement hashé
            self.assertTrue(user.check_password(self.user_data['password']))
            
            # Vérifier que le profil étudiant a été créé automatiquement
            self.assertTrue(hasattr(user, 'student_profile'))
            
            # Vérifier que l'email de bienvenue a été envoyé
            mock_send_email.assert_called_once_with(user)
    
    def test_register_user_with_profile_data(self):
        """
        Test d'inscription d'un utilisateur avec des données de profil spécifiques.
        """
        with patch('apps.accounts.services.AccountService.send_welcome_email'):
            # Créer un utilisateur avec des données de profil spécifiques
            user = AccountService.register_user(self.user_data, self.student_data)
            
            # Vérifier que le profil a été créé avec les bonnes données
            self.assertEqual(user.student_profile.current_level, self.student_data['current_level'])
            self.assertEqual(user.student_profile.major, self.student_data['major'])
            self.assertEqual(user.student_profile.interests, self.student_data['interests'])
    
    def test_update_user_profile(self):
        """
        Test de mise à jour du profil utilisateur.
        """
        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)
        Student.objects.get(user=user)  # Le profil étudiant est créé automatiquement via le signal
        
        # Préparer les données de mise à jour
        update_user_data = {
            'first_name': 'Updated',
            'last_name': 'Profile',
            'phone_number': '9876543210'
        }
        
        update_student_data = {
            'current_level': 'Licence 3',
            'major': 'Sciences des Données'
        }
        
        # Mettre à jour le profil via le service
        updated_user = AccountService.update_user_profile(
            user,
            update_user_data,
            update_student_data
        )
        
        # Rafraîchir l'utilisateur depuis la base de données
        user.refresh_from_db()
        
        # Vérifier que l'utilisateur a été mis à jour correctement
        self.assertEqual(user.first_name, update_user_data['first_name'])
        self.assertEqual(user.last_name, update_user_data['last_name'])
        self.assertEqual(user.phone_number, update_user_data['phone_number'])
        
        # Vérifier que le profil étudiant a été mis à jour correctement
        self.assertEqual(user.student_profile.current_level, update_student_data['current_level'])
        self.assertEqual(user.student_profile.major, update_student_data['major'])
    
    def test_request_verification(self):
        """
        Test de demande de vérification.
        """
        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)
        
        # Soumettre une demande de vérification
        with patch('apps.accounts.services.Notification.objects.create') as mock_notification:
            # Configurer le mock pour simuler la création de notification
            mock_notification.return_value = MagicMock()
            
            result = AccountService.request_verification(user)
            
            # Vérifier que la demande a été traitée avec succès
            self.assertTrue(result)
            
            # Rafraîchir l'utilisateur depuis la base de données
            user.refresh_from_db()
            
            # Vérifier que le statut a été mis à jour
            self.assertEqual(user.verification_status, 'pending')
            self.assertIsNotNone(user.verification_requested_date)
    
    def test_verify_user_success(self):
        """
        Test de vérification d'un utilisateur avec succès.
        """
        # Créer un utilisateur en attente de vérification
        user = User.objects.create_user(**self.user_data)
        user.verification_status = 'pending'
        user.verification_requested_date = timezone.now()
        user.save()
        
        # Créer un administrateur
        admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            type='administrator'
        )
        
        # Approuver la demande de vérification
        with patch('apps.accounts.services.Notification.objects.create'):
            with patch('apps.accounts.services.send_mail'):
                result = AccountService.verify_user(
                    user=user,
                    admin=admin,
                    approved=True,
                    notes='Approuvé après vérification des documents.'
                )
                
                # Vérifier que la vérification a été traitée avec succès
                self.assertTrue(result)
                
                # Rafraîchir l'utilisateur depuis la base de données
                user.refresh_from_db()
                
                # Vérifier que le statut a été mis à jour
                self.assertEqual(user.verification_status, 'verified')
                self.assertIsNotNone(user.verification_completed_date)
                self.assertEqual(user.verification_notes, 'Approuvé après vérification des documents.')
    
    def test_verify_user_rejection(self):
        """
        Test de rejet de la vérification d'un utilisateur.
        """
        # Créer un utilisateur en attente de vérification
        user = User.objects.create_user(**self.user_data)
        user.verification_status = 'pending'
        user.verification_requested_date = timezone.now()
        user.save()
        
        # Créer un administrateur
        admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            type='administrator'
        )
        
        # Rejeter la demande de vérification
        with patch('apps.accounts.services.Notification.objects.create'):
            with patch('apps.accounts.services.send_mail'):
                result = AccountService.verify_user(
                    user=user,
                    admin=admin,
                    approved=False,
                    notes='Documents incomplets ou invalides.'
                )
                
                # Vérifier que la vérification a été traitée avec succès
                self.assertTrue(result)
                
                # Rafraîchir l'utilisateur depuis la base de données
                user.refresh_from_db()
                
                # Vérifier que le statut a été mis à jour
                self.assertEqual(user.verification_status, 'rejected')
                self.assertIsNotNone(user.verification_completed_date)
                self.assertEqual(user.verification_notes, 'Documents incomplets ou invalides.')
    
    def test_verify_user_invalid_status(self):
        """
        Test de vérification d'un utilisateur avec un statut invalide.
        """
        # Créer un utilisateur non en attente de vérification
        user = User.objects.create_user(**self.user_data)
        user.verification_status = 'unverified'  # Pas en attente
        user.save()
        
        # Créer un administrateur
        admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            type='administrator'
        )
        
        # Tenter de vérifier l'utilisateur
        result = AccountService.verify_user(
            user=user,
            admin=admin,
            approved=True
        )
        
        # Vérifier que la vérification a échoué
        self.assertFalse(result)
        
        # Rafraîchir l'utilisateur depuis la base de données
        user.refresh_from_db()
        
        # Vérifier que le statut n'a pas été modifié
        self.assertEqual(user.verification_status, 'unverified')
    
    @patch('apps.accounts.services.send_mail')
    def test_send_welcome_email(self, mock_send_mail):
        """
        Test d'envoi d'un email de bienvenue.
        """
        # Configurer le mock pour simuler l'envoi d'email
        mock_send_mail.return_value = 1
        
        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)
        
        # Envoyer un email de bienvenue
        result = AccountService.send_welcome_email(user)
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
    
    @patch('apps.accounts.services.send_mail')
    def test_send_password_reset_email(self, mock_send_mail):
        """
        Test d'envoi d'un email de réinitialisation de mot de passe.
        """
        # Configurer le mock pour simuler l'envoi d'email
        mock_send_mail.return_value = 1
        
        # Créer un utilisateur
        user = User.objects.create_user(**self.user_data)
        
        # Envoyer un email de réinitialisation de mot de passe
        result = AccountService.send_password_reset_email(user, 'some-token')
        
        # Vérifier que l'email a été envoyé
        self.assertTrue(result)
        mock_send_mail.assert_called_once()
    
    def test_get_user_stats(self):
        """
        Test de récupération des statistiques utilisateur.
        """
        # Créer plusieurs utilisateurs de différents types
        User.objects.create_user(
            email='student1@example.com',
            password='pass123',
            first_name='Student1',
            last_name='Test',
            type='student',
            verification_status='verified'
        )
        
        User.objects.create_user(
            email='student2@example.com',
            password='pass123',
            first_name='Student2',
            last_name='Test',
            type='student',
            verification_status='pending'
        )
        
        User.objects.create_user(
            email='teacher@example.com',
            password='pass123',
            first_name='Teacher',
            last_name='Test',
            type='teacher',
            verification_status='verified'
        )
        
        User.objects.create_user(
            email='advisor@example.com',
            password='pass123',
            first_name='Advisor',
            last_name='Test',
            type='advisor',
            verification_status='unverified'
        )
        
        # Récupérer les statistiques
        stats = AccountService.get_user_stats()
        
        # Vérifier que les statistiques sont correctes
        self.assertEqual(stats['total_users'], 4)
        self.assertEqual(stats['students_count'], 2)
        self.assertEqual(stats['teachers_count'], 1)
        self.assertEqual(stats['advisors_count'], 1)
        self.assertEqual(stats['verified_count'], 2)
        self.assertEqual(stats['pending_count'], 1)
        self.assertEqual(stats['unverified_count'], 1)
