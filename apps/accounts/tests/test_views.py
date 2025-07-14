from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

from apps.accounts.models import User, Student, Teacher, Advisor


class UserRegistrationViewTest(TestCase):
    """
    Tests pour la vue d'inscription des utilisateurs.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.user_data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'type': 'student'
        }
    
    def test_user_registration_success(self):
        """
        Test d'inscription réussie d'un utilisateur.
        """
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'newuser@example.com')
    
    def test_user_registration_with_existing_email(self):
        """
        Test d'inscription avec un email déjà utilisé.
        """
        # Créer un premier utilisateur
        User.objects.create_user(
            email='newuser@example.com',
            password='existingpass',
            first_name='Existing',
            last_name='User',
            type='student'
        )
        
        # Tenter de créer un autre utilisateur avec le même email
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)
    
    def test_user_registration_password_mismatch(self):
        """
        Test d'inscription avec des mots de passe qui ne correspondent pas.
        """
        self.user_data['password_confirm'] = 'differentpass'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
    
    def test_user_registration_missing_fields(self):
        """
        Test d'inscription avec des champs manquants.
        """
        # Supprimer le champ 'first_name'
        del self.user_data['first_name']
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


class StudentRegistrationViewTest(TestCase):
    """
    Tests pour la vue d'inscription des étudiants.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.register_url = reverse('accounts:register_student')
        self.student_data = {
            'email': 'student@example.com',
            'password': 'studentpass123',
            'password_confirm': 'studentpass123',
            'first_name': 'Student',
            'last_name': 'Test',
            'type': 'student',
            'current_level': 'Licence 1',
            'major': 'Informatique',
            'interests': ['Programmation', 'Intelligence artificielle']
        }
    
    def test_student_registration_success(self):
        """
        Test d'inscription réussie d'un étudiant.
        """
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.student_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 1)
        
        student = Student.objects.get()
        self.assertEqual(student.current_level, 'Licence 1')
        self.assertEqual(student.major, 'Informatique')
        self.assertEqual(student.interests, ['Programmation', 'Intelligence artificielle'])
    
    def test_student_registration_missing_specific_fields(self):
        """
        Test d'inscription d'un étudiant avec des champs spécifiques manquants.
        """
        # Supprimer le champ 'current_level'
        del self.student_data['current_level']
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.student_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Student.objects.count(), 0)


class TeacherRegistrationViewTest(TestCase):
    """
    Tests pour la vue d'inscription des enseignants.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.register_url = reverse('accounts:register_teacher')
        self.teacher_data = {
            'email': 'teacher@example.com',
            'password': 'teacherpass123',
            'password_confirm': 'teacherpass123',
            'first_name': 'Teacher',
            'last_name': 'Test',
            'type': 'teacher',
            'subjects': ['Mathématiques', 'Physique'],
            'qualifications': 'Doctorat en Sciences',
            'years_of_experience': 5,
            'expertise_areas': ['Préparation aux examens', 'Soutien scolaire']
        }
    
    def test_teacher_registration_success(self):
        """
        Test d'inscription réussie d'un enseignant.
        """
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.teacher_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Teacher.objects.count(), 1)
        
        teacher = Teacher.objects.get()
        self.assertEqual(teacher.subjects, ['Mathématiques', 'Physique'])
        self.assertEqual(teacher.qualifications, 'Doctorat en Sciences')
        self.assertEqual(teacher.years_of_experience, 5)
        self.assertEqual(teacher.expertise_areas, ['Préparation aux examens', 'Soutien scolaire'])
    
    def test_teacher_registration_missing_specific_fields(self):
        """
        Test d'inscription d'un enseignant avec des champs spécifiques manquants.
        """
        # Supprimer le champ 'subjects'
        del self.teacher_data['subjects']
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.teacher_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Teacher.objects.count(), 0)


class AdvisorRegistrationViewTest(TestCase):
    """
    Tests pour la vue d'inscription des conseillers.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.register_url = reverse('accounts:register_advisor')
        self.advisor_data = {
            'email': 'advisor@example.com',
            'password': 'advisorpass123',
            'password_confirm': 'advisorpass123',
            'first_name': 'Advisor',
            'last_name': 'Test',
            'type': 'advisor',
            'specialization': 'Orientation académique',
            'organization': 'Cabinet de conseil',
            'years_of_experience': 3,
            'expertise_areas': ['Orientation scolaire', 'Conseil carrière']
        }
    
    def test_advisor_registration_success(self):
        """
        Test d'inscription réussie d'un conseiller.
        """
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.advisor_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Advisor.objects.count(), 1)
        
        advisor = Advisor.objects.get()
        self.assertEqual(advisor.specialization, 'Orientation académique')
        self.assertEqual(advisor.organization, 'Cabinet de conseil')
        self.assertEqual(advisor.years_of_experience, 3)
        self.assertEqual(advisor.expertise_areas, ['Orientation scolaire', 'Conseil carrière'])
    
    def test_advisor_registration_missing_specific_fields(self):
        """
        Test d'inscription d'un conseiller avec des champs spécifiques manquants.
        """
        # Supprimer le champ 'specialization'
        del self.advisor_data['specialization']
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.advisor_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Advisor.objects.count(), 0)


class UserProfileViewTest(TestCase):
    """
    Tests pour la vue de profil utilisateur.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.profile_url = reverse('accounts:user_profile')
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            first_name='Profile',
            last_name='Test',
            type='student'
        )
        
        # Authentifier le client
        self.client.force_authenticate(user=self.user)
    
    def test_get_profile(self):
        """
        Test de récupération du profil utilisateur.
        """
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
        self.assertEqual(response.data['first_name'], 'Profile')
        self.assertEqual(response.data['last_name'], 'Test')
        self.assertEqual(response.data['type'], 'student')
    
    def test_update_profile(self):
        """
        Test de mise à jour du profil utilisateur.
        """
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Profile',
            'phone_number': '1234567890'
        }
        
        response = self.client.patch(
            self.profile_url,
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Rafraîchir l'utilisateur depuis la base de données
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Profile')
        self.assertEqual(self.user.phone_number, '1234567890')
    
    def test_unauthorised_access(self):
        """
        Test d'accès non autorisé au profil.
        """
        # Déconnecter l'utilisateur
        self.client.force_authenticate(user=None)
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordViewTest(TestCase):
    """
    Tests pour la vue de changement de mot de passe.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.client = APIClient()
        self.change_password_url = reverse('accounts:change_password')
        
        # Créer un utilisateur
        self.user = User.objects.create_user(
            email='user@example.com',
            password='currentpass123',
            first_name='Password',
            last_name='Test',
            type='student'
        )
        
        # Authentifier le client
        self.client.force_authenticate(user=self.user)
    
    def test_change_password_success(self):
        """
        Test de changement de mot de passe réussi.
        """
        data = {
            'old_password': 'currentpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        
        response = self.client.put(
            self.change_password_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Rafraîchir l'utilisateur depuis la base de données
        self.user.refresh_from_db()
        
        # Vérifier que le mot de passe a été changé
        self.assertTrue(self.user.check_password('newpass456'))
    
    def test_change_password_wrong_current(self):
        """
        Test de changement de mot de passe avec un mot de passe actuel incorrect.
        """
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        
        response = self.client.put(
            self.change_password_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Rafraîchir l'utilisateur depuis la base de données
        self.user.refresh_from_db()
        
        # Vérifier que le mot de passe n'a pas été changé
        self.assertTrue(self.user.check_password('currentpass123'))
    
    def test_change_password_mismatch(self):
        """
        Test de changement de mot de passe avec des nouveaux mots de passe qui ne correspondent pas.
        """
        data = {
            'old_password': 'currentpass123',
            'new_password': 'newpass456',
            'confirm_password': 'differentpass'
        }
        
        response = self.client.put(
            self.change_password_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Rafraîchir l'utilisateur depuis la base de données
        self.user.refresh_from_db()
        
        # Vérifier que le mot de passe n'a pas été changé
        self.assertTrue(self.user.check_password('currentpass123'))
