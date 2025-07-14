# accounts/serializers/base.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import User, Student, Teacher, Advisor, Administrator


class UserBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle User avec les informations essentielles.
    Utilisé comme base pour les autres sérialiseurs spécifiques.
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'type', 'verification_status'
        ]
        read_only_fields = ['id', 'verification_status']


class StudentBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Student.
    """
    class Meta:
        model = Student
        fields = ['current_level', 'major', 'interests', 'average_grade']
        read_only_fields = ['average_grade']


class TeacherBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Teacher.
    """
    class Meta:
        model = Teacher
        fields = ['subjects', 'qualifications', 'years_of_experience', 'expertise_areas']


class AdvisorBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Advisor.
    """
    class Meta:
        model = Advisor
        fields = ['specialization', 'organization', 'years_of_experience', 'expertise_areas']


class AdministratorBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Administrator.
    """
    class Meta:
        model = Administrator
        fields = ['role']