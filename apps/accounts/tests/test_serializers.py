from django.test import TestCase
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User, Student, Teacher, Advisor, Administrator
from apps.accounts.serializers import (
    UserSerializer, UserDetailSerializer, StudentProfileSerializer,
    TeacherProfileSerializer, AdvisorProfileSerializer, ProfilePictureSerializer,
    UserRegistrationSerializer, StudentRegistrationSerializer,
    TeacherRegistrationSerializer, AdvisorRegistrationSerializer,
    ChangePasswordSerializer
)


class UserSerializerTest(TestCase):
    """
    Tests pour le sérialiseur UserSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user_data = {
            'email': 'user@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '1234567890',
            'type': 'student',
            'verification_status': 'unverified'
        }
        self.user = User.objects.create_user(
            email=self.user_data['email'],
            password='password123',
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name'],
            phone_number=self.user_data['phone_number'],
            type=self.user_data['type']
        )
    
    def test_user_serializer(self):
        """
        Test de sérialisation d'un utilisateur.
        """
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        self.assertEqual(data['email'], self.user_data['email'])
        self.assertEqual(data['first_name'], self.user_data['first_name'])
        self.assertEqual(data['last_name'], self.user_data['last_name'])
        self.assertEqual(data['phone_number'], self.user_data['phone_number'])
        self.assertEqual(data['type'], self.user_data['type'])
        self.assertEqual(data['verification_status'], self.user_data['verification_status'])
        
        # Vérification que le mot de passe n'est pas inclus dans la sérialisation
        self.assertNotIn('password', data)
    
    def test_user_detail_serializer(self):
        """
        Test de sérialisation détaillée d'un utilisateur.
        """
        serializer = UserDetailSerializer(instance=self.user)
        data = serializer.data
        
        # Vérifier que les champs de base sont présents
        self.assertEqual(data['email'], self.user_data['email'])
        self.assertEqual(data['first_name'], self.user_data['first_name'])
        
        # Vérifier que les champs de détail supplémentaires sont présents
        self.assertIn('verification_requested_date', data)
        self.assertIn('verification_completed_date', data)


class StudentProfileSerializerTest(TestCase):
    """
    Tests pour le sérialiseur StudentProfileSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='student@example.com',
            password='password123',
            first_name='Student',
            last_name='Test',
            type='student'
        )
        self.student = Student.objects.create(
            user=self.user,
            current_level='Licence 2',
            major='Informatique',
            interests=['Programmation', 'IA']
        )
    
    def test_student_profile_serializer(self):
        """
        Test de sérialisation d'un profil étudiant.
        """
        serializer = StudentProfileSerializer(instance=self.student)
        data = serializer.data
        
        self.assertEqual(data['current_level'], 'Licence 2')
        self.assertEqual(data['major'], 'Informatique')
        self.assertEqual(data['interests'], ['Programmation', 'IA'])
        
        # Vérifier que l'utilisateur associé est correctement sérialisé
        self.assertEqual(data['user']['email'], 'student@example.com')
        self.assertEqual(data['user']['first_name'], 'Student')
        self.assertEqual(data['user']['last_name'], 'Test')


class TeacherProfileSerializerTest(TestCase):
    """
    Tests pour le sérialiseur TeacherProfileSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='teacher@example.com',
            password='password123',
            first_name='Teacher',
            last_name='Test',
            type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.user,
            subjects=['Mathématiques', 'Physique'],
            qualifications='Doctorat en Sciences',
            years_of_experience=5
        )
    
    def test_teacher_profile_serializer(self):
        """
        Test de sérialisation d'un profil enseignant.
        """
        serializer = TeacherProfileSerializer(instance=self.teacher)
        data = serializer.data
        
        self.assertEqual(data['subjects'], ['Mathématiques', 'Physique'])
        self.assertEqual(data['qualifications'], 'Doctorat en Sciences')
        self.assertEqual(data['years_of_experience'], 5)
        
        # Vérifier que l'utilisateur associé est correctement sérialisé
        self.assertEqual(data['user']['email'], 'teacher@example.com')
        self.assertEqual(data['user']['first_name'], 'Teacher')
        self.assertEqual(data['user']['last_name'], 'Test')


class AdvisorProfileSerializerTest(TestCase):
    """
    Tests pour le sérialiseur AdvisorProfileSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='advisor@example.com',
            password='password123',
            first_name='Advisor',
            last_name='Test',
            type='advisor'
        )
        self.advisor = Advisor.objects.create(
            user=self.user,
            specialization='Orientation académique',
            organization='Cabinet de conseil',
            years_of_experience=3,
            expertise_areas=['Orientation scolaire', 'Conseil carrière']
        )
    
    def test_advisor_profile_serializer(self):
        """
        Test de sérialisation d'un profil conseiller.
        """
        serializer = AdvisorProfileSerializer(instance=self.advisor)
        data = serializer.data
        
        self.assertEqual(data['specialization'], 'Orientation académique')
        self.assertEqual(data['organization'], 'Cabinet de conseil')
        self.assertEqual(data['years_of_experience'], 3)
        self.assertEqual(data['expertise_areas'], ['Orientation scolaire', 'Conseil carrière'])
        
        # Vérifier que l'utilisateur associé est correctement sérialisé
        self.assertEqual(data['user']['email'], 'advisor@example.com')
        self.assertEqual(data['user']['first_name'], 'Advisor')
        self.assertEqual(data['user']['last_name'], 'Test')


class UserRegistrationSerializerTest(TestCase):
    """
    Tests pour le sérialiseur UserRegistrationSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.registration_data = {
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone_number': '1234567890',
            'type': 'student'
        }
    
    def test_user_registration_serializer_validation(self):
        """
        Test de validation des données d'inscription.
        """
        serializer = UserRegistrationSerializer(data=self.registration_data)
        self.assertTrue(serializer.is_valid())
    
    def test_password_mismatch_validation(self):
        """
        Test de validation avec des mots de passe qui ne correspondent pas.
        """
        data = self.registration_data.copy()
        data['password_confirm'] = 'differentpass'
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
    def test_existing_email_validation(self):
        """
        Test de validation avec un email déjà existant.
        """
        # Créer un utilisateur avec l'email testé
        User.objects.create_user(
            email='newuser@example.com',
            password='existingpass',
            first_name='Existing',
            last_name='User',
            type='student'
        )
        
        serializer = UserRegistrationSerializer(data=self.registration_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_create_user(self):
        """
        Test de création d'un utilisateur via le sérialiseur.
        """
        serializer = UserRegistrationSerializer(data=self.registration_data)
        if serializer.is_valid():
            user = serializer.save()
            
            self.assertEqual(user.email, self.registration_data['email'])
            self.assertEqual(user.first_name, self.registration_data['first_name'])
            self.assertEqual(user.last_name, self.registration_data['last_name'])
            self.assertEqual(user.phone_number, self.registration_data['phone_number'])
            self.assertEqual(user.type, self.registration_data['type'])
            self.assertEqual(user.verification_status, 'unverified')
            
            # Vérifier que le mot de passe a été correctement hashé
            self.assertTrue(user.check_password(self.registration_data['password']))
        else:
            self.fail(f"La validation du sérialiseur a échoué: {serializer.errors}")


class StudentRegistrationSerializerTest(TestCase):
    """
    Tests pour le sérialiseur StudentRegistrationSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
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
    
    def test_student_registration_serializer_validation(self):
        """
        Test de validation des données d'inscription d'un étudiant.
        """
        serializer = StudentRegistrationSerializer(data=self.student_data)
        self.assertTrue(serializer.is_valid())
    
    def test_create_student(self):
        """
        Test de création d'un étudiant via le sérialiseur.
        """
        serializer = StudentRegistrationSerializer(data=self.student_data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Vérifier que l'utilisateur a été créé
            self.assertEqual(user.email, self.student_data['email'])
            self.assertEqual(user.type, 'student')
            
            # Vérifier que le profil étudiant a été créé
            self.assertTrue(hasattr(user, 'student_profile'))
            self.assertEqual(user.student_profile.current_level, self.student_data['current_level'])
            self.assertEqual(user.student_profile.major, self.student_data['major'])
            self.assertEqual(user.student_profile.interests, self.student_data['interests'])
        else:
            self.fail(f"La validation du sérialiseur a échoué: {serializer.errors}")


class ChangePasswordSerializerTest(TestCase):
    """
    Tests pour le sérialiseur ChangePasswordSerializer.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='user@example.com',
            password='currentpass123',
            first_name='Password',
            last_name='Test',
            type='student'
        )
        self.password_data = {
            'old_password': 'currentpass123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        }
        self.request = type('MockRequest', (), {'user': self.user})
    
    def test_change_password_serializer_validation(self):
        """
        Test de validation des données de changement de mot de passe.
        """
        serializer = ChangePasswordSerializer(
            data=self.password_data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
    
    def test_wrong_old_password_validation(self):
        """
        Test de validation avec un ancien mot de passe incorrect.
        """
        data = self.password_data.copy()
        data['old_password'] = 'wrongpass'
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
    
    def test_password_mismatch_validation(self):
        """
        Test de validation avec des nouveaux mots de passe qui ne correspondent pas.
        """
        data = self.password_data.copy()
        data['confirm_password'] = 'differentpass'
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)
    
    def test_change_password(self):
        """
        Test de changement de mot de passe via le sérialiseur.
        """
        serializer = ChangePasswordSerializer(
            data=self.password_data,
            context={'request': self.request}
        )
        if serializer.is_valid():
            serializer.save()
            
            # Rafraîchir l'utilisateur depuis la base de données
            self.user.refresh_from_db()
            
            # Vérifier que le mot de passe a été changé
            self.assertFalse(self.user.check_password('currentpass123'))
            self.assertTrue(self.user.check_password('newpass456'))
        else:
            self.fail(f"La validation du sérialiseur a échoué: {serializer.errors}")
