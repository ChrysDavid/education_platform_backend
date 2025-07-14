from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.accounts.models import User, Student, Teacher, Advisor
from apps.accounts.permissions import (
    IsOwnerOrAdmin, IsVerified, IsTeacher, IsAdvisor,
    IsStudent, IsAdministrator, IsVerifiedTeacher,
    IsVerifiedAdvisor, IsVerifiedStudent, ReadOnly
)


class PermissionsTest(TestCase):
    """
    Tests pour les permissions personnalisées de l'application accounts.
    """
    
    def setUp(self):
        """
        Configuration initiale pour les tests.
        """
        # Créer des utilisateurs de test pour chaque type
        self.student = User.objects.create_user(
            email='student@example.com',
            password='studentpass',
            first_name='Student',
            last_name='User',
            type='student'
        )
        Student.objects.get(user=self.student)  # Créé automatiquement via signal
        
        self.teacher = User.objects.create_user(
            email='teacher@example.com',
            password='teacherpass',
            first_name='Teacher',
            last_name='User',
            type='teacher'
        )
        Teacher.objects.get(user=self.teacher)  # Créé automatiquement via signal
        
        self.advisor = User.objects.create_user(
            email='advisor@example.com',
            password='advisorpass',
            first_name='Advisor',
            last_name='User',
            type='advisor'
        )
        Advisor.objects.get(user=self.advisor)  # Créé automatiquement via signal
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            type='administrator'
        )
        
        # Définir des utilisateurs vérifiés
        self.verified_student = User.objects.create_user(
            email='verified.student@example.com',
            password='studentpass',
            first_name='Verified',
            last_name='Student',
            type='student',
            verification_status='verified'
        )
        Student.objects.get(user=self.verified_student)  # Créé automatiquement via signal
        
        self.verified_teacher = User.objects.create_user(
            email='verified.teacher@example.com',
            password='teacherpass',
            first_name='Verified',
            last_name='Teacher',
            type='teacher',
            verification_status='verified'
        )
        Teacher.objects.get(user=self.verified_teacher)  # Créé automatiquement via signal
        
        self.verified_advisor = User.objects.create_user(
            email='verified.advisor@example.com',
            password='advisorpass',
            first_name='Verified',
            last_name='Advisor',
            type='advisor',
            verification_status='verified'
        )
        Advisor.objects.get(user=self.verified_advisor)  # Créé automatiquement via signal
        
        # Créer une factory de requête
        self.factory = APIRequestFactory()
    
    def _get_request(self, user=None):
        """
        Crée une requête avec un utilisateur authentifié si fourni.
        """
        request = self.factory.get('/')
        if user:
            request.user = user
        return request
    
    def test_is_owner_or_admin_permission(self):
        """
        Test de la permission IsOwnerOrAdmin.
        """
        permission = IsOwnerOrAdmin()
        
        # Objet avec un attribut user (exemple: profil étudiant)
        student_profile = Student.objects.get(user=self.student)
        
        # L'utilisateur est le propriétaire de l'objet
        request = self._get_request(self.student)
        self.assertTrue(permission.has_object_permission(request, None, student_profile))
        
        # L'utilisateur n'est pas le propriétaire de l'objet
        request = self._get_request(self.teacher)
        self.assertFalse(permission.has_object_permission(request, None, student_profile))
        
        # L'administrateur a accès même s'il n'est pas le propriétaire
        request = self._get_request(self.admin)
        self.assertTrue(permission.has_object_permission(request, None, student_profile))
        
        # L'objet est l'utilisateur lui-même
        request = self._get_request(self.student)
        self.assertTrue(permission.has_object_permission(request, None, self.student))
    
    def test_is_verified_permission(self):
        """
        Test de la permission IsVerified.
        """
        permission = IsVerified()
        
        # Utilisateur non vérifié
        request = self._get_request(self.student)
        self.assertFalse(permission.has_permission(request, None))
        
        # Utilisateur vérifié
        request = self._get_request(self.verified_student)
        self.assertTrue(permission.has_permission(request, None))
        
        # Administrateur (toujours autorisé)
        request = self._get_request(self.admin)
        self.assertTrue(permission.has_permission(request, None))
    
    def test_is_teacher_permission(self):
        """
        Test de la permission IsTeacher.
        """
        permission = IsTeacher()
        
        # Utilisateur enseignant
        request = self._get_request(self.teacher)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non enseignant
        request = self._get_request(self.student)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_advisor_permission(self):
        """
        Test de la permission IsAdvisor.
        """
        permission = IsAdvisor()
        
        # Utilisateur conseiller
        request = self._get_request(self.advisor)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non conseiller
        request = self._get_request(self.student)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_student_permission(self):
        """
        Test de la permission IsStudent.
        """
        permission = IsStudent()
        
        # Utilisateur étudiant
        request = self._get_request(self.student)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non étudiant
        request = self._get_request(self.teacher)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_administrator_permission(self):
        """
        Test de la permission IsAdministrator.
        """
        permission = IsAdministrator()
        
        # Utilisateur administrateur
        request = self._get_request(self.admin)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non administrateur
        request = self._get_request(self.student)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_verified_teacher_permission(self):
        """
        Test de la permission IsVerifiedTeacher.
        """
        permission = IsVerifiedTeacher()
        
        # Enseignant non vérifié
        request = self._get_request(self.teacher)
        self.assertFalse(permission.has_permission(request, None))
        
        # Enseignant vérifié
        request = self._get_request(self.verified_teacher)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non enseignant mais vérifié
        request = self._get_request(self.verified_student)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_verified_advisor_permission(self):
        """
        Test de la permission IsVerifiedAdvisor.
        """
        permission = IsVerifiedAdvisor()
        
        # Conseiller non vérifié
        request = self._get_request(self.advisor)
        self.assertFalse(permission.has_permission(request, None))
        
        # Conseiller vérifié
        request = self._get_request(self.verified_advisor)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non conseiller mais vérifié
        request = self._get_request(self.verified_student)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_is_verified_student_permission(self):
        """
        Test de la permission IsVerifiedStudent.
        """
        permission = IsVerifiedStudent()
        
        # Étudiant non vérifié
        request = self._get_request(self.student)
        self.assertFalse(permission.has_permission(request, None))
        
        # Étudiant vérifié
        request = self._get_request(self.verified_student)
        self.assertTrue(permission.has_permission(request, None))
        
        # Utilisateur non étudiant mais vérifié
        request = self._get_request(self.verified_teacher)
        self.assertFalse(permission.has_permission(request, None))
    
    def test_read_only_permission(self):
        """
        Test de la permission ReadOnly.
        """
        permission = ReadOnly()
        
        # Requête en lecture (GET)
        request = self.factory.get('/')
        self.assertTrue(permission.has_permission(request, None))
        
        # Requête en écriture (POST)
        request = self.factory.post('/')
        self.assertFalse(permission.has_permission(request, None))
        
        # Requête en écriture (PUT)
        request = self.factory.put('/')
        self.assertFalse(permission.has_permission(request, None))
        
        # Requête en écriture (DELETE)
        request = self.factory.delete('/')
        self.assertFalse(permission.has_permission(request, None))