# accounts/serializers/web.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from ..models import User, Student, Teacher, Advisor, Administrator
from .base import (
    UserBaseSerializer, 
    StudentBaseSerializer, 
    TeacherBaseSerializer,
    AdvisorBaseSerializer,
    AdministratorBaseSerializer
)


class UserWebSerializer(UserBaseSerializer):
    """
    Sérialiseur pour l'interface web du modèle User.
    """
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + [
            'phone_number', 'date_of_birth', 'profile_picture', 
            'address', 'city', 'date_joined', 'verification_status_display',
            'type_display', 'is_active'
        ]
        read_only_fields = UserBaseSerializer.Meta.read_only_fields + [
            'date_joined', 'is_active'
        ]


class UserDetailWebSerializer(UserWebSerializer):
    """
    Sérialiseur détaillé pour l'interface web avec tous les champs.
    """
    class Meta(UserWebSerializer.Meta):
        fields = UserWebSerializer.Meta.fields + [
            'verification_requested_date', 'verification_completed_date', 'verification_notes'
        ]
        read_only_fields = UserWebSerializer.Meta.read_only_fields + [
            'verification_requested_date', 'verification_completed_date'
        ]


class StudentWebSerializer(StudentBaseSerializer):
    """
    Sérialiseur pour l'interface web du modèle Student.
    """
    user = UserWebSerializer(read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta(StudentBaseSerializer.Meta):
        fields = ['user', 'school', 'school_name'] + StudentBaseSerializer.Meta.fields
        read_only_fields = ['user', 'school_name'] + StudentBaseSerializer.Meta.read_only_fields


class TeacherWebSerializer(TeacherBaseSerializer):
    """
    Sérialiseur pour l'interface web du modèle Teacher.
    """
    user = UserWebSerializer(read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta(TeacherBaseSerializer.Meta):
        fields = ['user', 'school', 'school_name'] + TeacherBaseSerializer.Meta.fields
        read_only_fields = ['user', 'school_name']


class AdvisorWebSerializer(AdvisorBaseSerializer):
    """
    Sérialiseur pour l'interface web du modèle Advisor.
    """
    user = UserWebSerializer(read_only=True)
    
    class Meta(AdvisorBaseSerializer.Meta):
        fields = ['user'] + AdvisorBaseSerializer.Meta.fields
        read_only_fields = ['user']


class AdministratorWebSerializer(AdministratorBaseSerializer):
    """
    Sérialiseur pour l'interface web du modèle Administrator.
    """
    user = UserWebSerializer(read_only=True)
    
    class Meta(AdministratorBaseSerializer.Meta):
        fields = ['user'] + AdministratorBaseSerializer.Meta.fields
        read_only_fields = ['user']