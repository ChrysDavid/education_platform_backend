from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounts.models import User, Student, Teacher, Advisor, Administrator


class UserModelTest(TestCase):
    """
    Tests pour le modèle User.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'securepassword123',
            'type': 'student'
        }
    
    def test_create_user(self):
        """
        Test de création d'un utilisateur.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertEqual(user.type, self.user_data['type'])
        self.assertEqual(user.verification_status, 'unverified')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """
        Test de création d'un superutilisateur.
        """
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin.email, 'admin@example.com')
        self.assertEqual(admin.type, 'administrator')
        self.assertEqual(admin.verification_status, 'verified')
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_get_full_name(self):
        """
        Test de la méthode get_full_name.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'John Doe')
    
    def test_get_short_name(self):
        """
        Test de la méthode get_short_name.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'John')
    
    def test_is_verified(self):
        """
        Test de la méthode is_verified.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_verified())
        
        user.verification_status = 'verified'
        user.save()
        self.assertTrue(user.is_verified())
    
    def test_is_pending_verification(self):
        """
        Test de la méthode is_pending_verification.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertFalse(user.is_pending_verification())
        
        user.verification_status = 'pending'
        user.save()
        self.assertTrue(user.is_pending_verification())
    
    def test_request_verification(self):
        """
        Test de la méthode request_verification.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.verification_status, 'unverified')
        self.assertIsNone(user.verification_requested_date)
        
        user.request_verification()
        self.assertEqual(user.verification_status, 'pending')
        self.assertIsNotNone(user.verification_requested_date)
    
    def test_email_uniqueness(self):
        """
        Test de l'unicité de l'email.
        """
        User.objects.create_user(**self.user_data)
        
        with self.assertRaises(Exception):
            User.objects.create_user(**self.user_data)
    
    def test_user_str_representation(self):
        """
        Test de la représentation string de l'utilisateur.
        """
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'John Doe (test@example.com)')


class StudentModelTest(TestCase):
    """
    Tests pour le modèle Student.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='student@example.com',
            first_name='Student',
            last_name='Test',
            password='student123',
            type='student'
        )
    
    def test_student_creation(self):
        """
        Test de création d'un profil étudiant.
        """
        student = Student.objects.create(
            user=self.user,
            current_level='Licence 2',
            major='Informatique'
        )
        
        self.assertEqual(student.user, self.user)
        self.assertEqual(student.current_level, 'Licence 2')
        self.assertEqual(student.major, 'Informatique')
        self.assertEqual(student.interests, [])
        self.assertIsNone(student.average_grade)
    
    def test_student_str_representation(self):
        """
        Test de la représentation string de l'étudiant.
        """
        student = Student.objects.create(
            user=self.user,
            current_level='Licence 2',
            major='Informatique'
        )
        self.assertEqual(str(student), 'Étudiant: Student Test')


class TeacherModelTest(TestCase):
    """
    Tests pour le modèle Teacher.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='teacher@example.com',
            first_name='Teacher',
            last_name='Test',
            password='teacher123',
            type='teacher'
        )
    
    def test_teacher_creation(self):
        """
        Test de création d'un profil enseignant.
        """
        teacher = Teacher.objects.create(
            user=self.user,
            subjects=['Mathématiques', 'Physique'],
            qualifications='Doctorat en Sciences',
            years_of_experience=5
        )
        
        self.assertEqual(teacher.user, self.user)
        self.assertEqual(teacher.subjects, ['Mathématiques', 'Physique'])
        self.assertEqual(teacher.qualifications, 'Doctorat en Sciences')
        self.assertEqual(teacher.years_of_experience, 5)
        self.assertEqual(teacher.expertise_areas, [])
    
    def test_teacher_str_representation(self):
        """
        Test de la représentation string de l'enseignant.
        """
        teacher = Teacher.objects.create(
            user=self.user,
            subjects=['Mathématiques', 'Physique'],
            qualifications='Doctorat en Sciences',
            years_of_experience=5
        )
        self.assertEqual(str(teacher), 'Enseignant: Teacher Test')


class AdvisorModelTest(TestCase):
    """
    Tests pour le modèle Advisor.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='advisor@example.com',
            first_name='Advisor',
            last_name='Test',
            password='advisor123',
            type='advisor'
        )
    
    def test_advisor_creation(self):
        """
        Test de création d'un profil conseiller.
        """
        advisor = Advisor.objects.create(
            user=self.user,
            specialization='Orientation académique',
            organization='Cabinet de conseil',
            years_of_experience=3
        )
        
        self.assertEqual(advisor.user, self.user)
        self.assertEqual(advisor.specialization, 'Orientation académique')
        self.assertEqual(advisor.organization, 'Cabinet de conseil')
        self.assertEqual(advisor.years_of_experience, 3)
        self.assertEqual(advisor.expertise_areas, [])
    
    def test_advisor_str_representation(self):
        """
        Test de la représentation string du conseiller.
        """
        advisor = Advisor.objects.create(
            user=self.user,
            specialization='Orientation académique',
            organization='Cabinet de conseil',
            years_of_experience=3
        )
        self.assertEqual(str(advisor), 'Conseiller: Advisor Test')


class AdministratorModelTest(TestCase):
    """
    Tests pour le modèle Administrator.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        self.user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='Test',
            password='admin123',
            type='administrator'
        )
    
    def test_administrator_creation(self):
        """
        Test de création d'un profil administrateur.
        """
        admin = Administrator.objects.create(
            user=self.user,
            role='Responsable des comptes'
        )
        
        self.assertEqual(admin.user, self.user)
        self.assertEqual(admin.role, 'Responsable des comptes')
    
    def test_administrator_str_representation(self):
        """
        Test de la représentation string de l'administrateur.
        """
        admin = Administrator.objects.create(
            user=self.user,
            role='Responsable des comptes'
        )
        self.assertEqual(str(admin), 'Administrateur: Admin Test')
