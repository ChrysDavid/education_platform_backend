from django.test import TestCase

from apps.accounts.models import User, Student, Teacher, Advisor
from apps.accounts.managers import (
    VerifiedUserManager, PendingVerificationManager,
    StudentManager, TeacherManager, AdvisorManager
)


class VerifiedUserManagerTest(TestCase):
    """
    Tests pour le gestionnaire VerifiedUserManager.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des utilisateurs avec différents statuts de vérification
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='password123',
            first_name='Verified',
            last_name='User',
            type='student',
            verification_status='verified'
        )
        
        self.pending_user = User.objects.create_user(
            email='pending@example.com',
            password='password123',
            first_name='Pending',
            last_name='User',
            type='student',
            verification_status='pending'
        )
        
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='password123',
            first_name='Unverified',
            last_name='User',
            type='student',
            verification_status='unverified'
        )
        
        self.rejected_user = User.objects.create_user(
            email='rejected@example.com',
            password='password123',
            first_name='Rejected',
            last_name='User',
            type='student',
            verification_status='rejected'
        )
        
        # Créer une instance du gestionnaire
        self.verified_manager = VerifiedUserManager()
        self.verified_manager.model = User
    
    def test_get_queryset(self):
        """
        Test que get_queryset retourne uniquement les utilisateurs vérifiés.
        """
        queryset = self.verified_manager.get_queryset()
        
        # Vérifier que seul l'utilisateur vérifié est dans le queryset
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.verified_user, queryset)
        self.assertNotIn(self.pending_user, queryset)
        self.assertNotIn(self.unverified_user, queryset)
        self.assertNotIn(self.rejected_user, queryset)


class PendingVerificationManagerTest(TestCase):
    """
    Tests pour le gestionnaire PendingVerificationManager.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des utilisateurs avec différents statuts de vérification
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='password123',
            first_name='Verified',
            last_name='User',
            type='student',
            verification_status='verified'
        )
        
        self.pending_user = User.objects.create_user(
            email='pending@example.com',
            password='password123',
            first_name='Pending',
            last_name='User',
            type='student',
            verification_status='pending'
        )
        
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='password123',
            first_name='Unverified',
            last_name='User',
            type='student',
            verification_status='unverified'
        )
        
        self.rejected_user = User.objects.create_user(
            email='rejected@example.com',
            password='password123',
            first_name='Rejected',
            last_name='User',
            type='student',
            verification_status='rejected'
        )
        
        # Créer une instance du gestionnaire
        self.pending_manager = PendingVerificationManager()
        self.pending_manager.model = User
    
    def test_get_queryset(self):
        """
        Test que get_queryset retourne uniquement les utilisateurs en attente de vérification.
        """
        queryset = self.pending_manager.get_queryset()
        
        # Vérifier que seul l'utilisateur en attente est dans le queryset
        self.assertEqual(queryset.count(), 1)
        self.assertIn(self.pending_user, queryset)
        self.assertNotIn(self.verified_user, queryset)
        self.assertNotIn(self.unverified_user, queryset)
        self.assertNotIn(self.rejected_user, queryset)


class StudentManagerTest(TestCase):
    """
    Tests pour le gestionnaire StudentManager.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des étudiants avec différentes caractéristiques
        self.user1 = User.objects.create_user(
            email='student1@example.com',
            password='password123',
            first_name='Student1',
            last_name='User',
            type='student',
            verification_status='verified'
        )
        self.student1 = Student.objects.get(user=self.user1)
        self.student1.current_level = 'Licence 1'
        self.student1.save()
        
        self.user2 = User.objects.create_user(
            email='student2@example.com',
            password='password123',
            first_name='Student2',
            last_name='User',
            type='student',
            verification_status='verified'
        )
        self.student2 = Student.objects.get(user=self.user2)
        self.student2.current_level = 'Licence 2'
        self.student2.save()
        
        self.user3 = User.objects.create_user(
            email='student3@example.com',
            password='password123',
            first_name='Student3',
            last_name='User',
            type='student',
            verification_status='unverified'
        )
        self.student3 = Student.objects.get(user=self.user3)
        self.student3.current_level = 'Licence 1'
        self.student3.save()
        
        # Créer une instance du gestionnaire
        self.student_manager = StudentManager()
        self.student_manager.model = Student
    
    def test_get_by_level(self):
        """
        Test que get_by_level retourne les étudiants du niveau spécifié.
        """
        # Rechercher les étudiants de Licence 1
        queryset = self.student_manager.get_by_level('Licence 1')
        
        # Vérifier que les bons étudiants sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.student1, queryset)
        self.assertIn(self.student3, queryset)
        self.assertNotIn(self.student2, queryset)
    
    def test_get_verified(self):
        """
        Test que get_verified retourne uniquement les étudiants vérifiés.
        """
        # Rechercher les étudiants vérifiés
        queryset = self.student_manager.get_verified()
        
        # Vérifier que seuls les étudiants vérifiés sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.student1, queryset)
        self.assertIn(self.student2, queryset)
        self.assertNotIn(self.student3, queryset)


class TeacherManagerTest(TestCase):
    """
    Tests pour le gestionnaire TeacherManager.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des enseignants avec différentes caractéristiques
        self.user1 = User.objects.create_user(
            email='teacher1@example.com',
            password='password123',
            first_name='Teacher1',
            last_name='User',
            type='teacher',
            verification_status='verified'
        )
        self.teacher1 = Teacher.objects.get(user=self.user1)
        self.teacher1.subjects = ['Mathématiques', 'Physique']
        self.teacher1.years_of_experience = 5
        self.teacher1.save()
        
        self.user2 = User.objects.create_user(
            email='teacher2@example.com',
            password='password123',
            first_name='Teacher2',
            last_name='User',
            type='teacher',
            verification_status='verified'
        )
        self.teacher2 = Teacher.objects.get(user=self.user2)
        self.teacher2.subjects = ['Biologie', 'Chimie']
        self.teacher2.years_of_experience = 3
        self.teacher2.save()
        
        self.user3 = User.objects.create_user(
            email='teacher3@example.com',
            password='password123',
            first_name='Teacher3',
            last_name='User',
            type='teacher',
            verification_status='unverified'
        )
        self.teacher3 = Teacher.objects.get(user=self.user3)
        self.teacher3.subjects = ['Mathématiques', 'Informatique']
        self.teacher3.years_of_experience = 2
        self.teacher3.save()
        
        # Créer une instance du gestionnaire
        self.teacher_manager = TeacherManager()
        self.teacher_manager.model = Teacher
    
    def test_get_by_subject(self):
        """
        Test que get_by_subject retourne les enseignants de la matière spécifiée.
        """
        # Rechercher les enseignants de Mathématiques
        queryset = self.teacher_manager.get_by_subject('Mathématiques')
        
        # Vérifier que les bons enseignants sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.teacher1, queryset)
        self.assertIn(self.teacher3, queryset)
        self.assertNotIn(self.teacher2, queryset)
    
    def test_get_by_experience(self):
        """
        Test que get_by_experience retourne les enseignants avec au moins l'expérience spécifiée.
        """
        # Rechercher les enseignants avec au moins 3 ans d'expérience
        queryset = self.teacher_manager.get_by_experience(3)
        
        # Vérifier que les bons enseignants sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.teacher1, queryset)
        self.assertIn(self.teacher2, queryset)
        self.assertNotIn(self.teacher3, queryset)
    
    def test_get_verified(self):
        """
        Test que get_verified retourne uniquement les enseignants vérifiés.
        """
        # Rechercher les enseignants vérifiés
        queryset = self.teacher_manager.get_verified()
        
        # Vérifier que seuls les enseignants vérifiés sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.teacher1, queryset)
        self.assertIn(self.teacher2, queryset)
        self.assertNotIn(self.teacher3, queryset)


class AdvisorManagerTest(TestCase):
    """
    Tests pour le gestionnaire AdvisorManager.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des conseillers avec différentes caractéristiques
        self.user1 = User.objects.create_user(
            email='advisor1@example.com',
            password='password123',
            first_name='Advisor1',
            last_name='User',
            type='advisor',
            verification_status='verified'
        )
        self.advisor1 = Advisor.objects.get(user=self.user1)
        self.advisor1.specialization = 'Orientation académique'
        self.advisor1.expertise_areas = ['Orientation scolaire', 'Conseil carrière']
        self.advisor1.years_of_experience = 7
        self.advisor1.save()
        
        self.user2 = User.objects.create_user(
            email='advisor2@example.com',
            password='password123',
            first_name='Advisor2',
            last_name='User',
            type='advisor',
            verification_status='verified'
        )
        self.advisor2 = Advisor.objects.get(user=self.user2)
        self.advisor2.specialization = 'Orientation professionnelle'
        self.advisor2.expertise_areas = ['Réorientation', 'Préparation entretien']
        self.advisor2.years_of_experience = 4
        self.advisor2.save()
        
        self.user3 = User.objects.create_user(
            email='advisor3@example.com',
            password='password123',
            first_name='Advisor3',
            last_name='User',
            type='advisor',
            verification_status='unverified'
        )
        self.advisor3 = Advisor.objects.get(user=self.user3)
        self.advisor3.specialization = 'Orientation académique'
        self.advisor3.expertise_areas = ['Orientation scolaire', 'Études à l\'étranger']
        self.advisor3.years_of_experience = 2
        self.advisor3.save()
        
        # Créer une instance du gestionnaire
        self.advisor_manager = AdvisorManager()
        self.advisor_manager.model = Advisor
    
    def test_get_by_specialization(self):
        """
        Test que get_by_specialization retourne les conseillers de la spécialisation spécifiée.
        """
        # Rechercher les conseillers d'orientation académique
        queryset = self.advisor_manager.get_by_specialization('Orientation académique')
        
        # Vérifier que les bons conseillers sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.advisor1, queryset)
        self.assertIn(self.advisor3, queryset)
        self.assertNotIn(self.advisor2, queryset)
    
    def test_get_by_experience(self):
        """
        Test que get_by_experience retourne les conseillers avec au moins l'expérience spécifiée.
        """
        # Rechercher les conseillers avec au moins 4 ans d'expérience
        queryset = self.advisor_manager.get_by_experience(4)
        
        # Vérifier que les bons conseillers sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.advisor1, queryset)
        self.assertIn(self.advisor2, queryset)
        self.assertNotIn(self.advisor3, queryset)
    
    def test_get_by_expertise(self):
        """
        Test que get_by_expertise retourne les conseillers avec l'expertise spécifiée.
        """
        # Rechercher les conseillers experts en orientation scolaire
        queryset = self.advisor_manager.get_by_expertise('Orientation scolaire')
        
        # Vérifier que les bons conseillers sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.advisor1, queryset)
        self.assertIn(self.advisor3, queryset)
        self.assertNotIn(self.advisor2, queryset)
    
    def test_get_verified(self):
        """
        Test que get_verified retourne uniquement les conseillers vérifiés.
        """
        # Rechercher les conseillers vérifiés
        queryset = self.advisor_manager.get_verified()
        
        # Vérifier que seuls les conseillers vérifiés sont dans le queryset
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.advisor1, queryset)
        self.assertIn(self.advisor2, queryset)
        self.assertNotIn(self.advisor3, queryset)