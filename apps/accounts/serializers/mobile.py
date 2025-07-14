# accounts/serializers/mobile.py
import json
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password

from ..models import User, Student, Teacher, Advisor, Pupil, Administrator
from .base import (
    UserBaseSerializer, 
    StudentBaseSerializer, 
    TeacherBaseSerializer,
    AdvisorBaseSerializer,
    AdministratorBaseSerializer
)


class UserSerializer(UserBaseSerializer):
    """
    Sérialiseur pour l'API mobile du modèle User avec des informations de base.
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


class UserDetailSerializer(UserSerializer):
    """
    Sérialiseur détaillé pour l'API mobile avec tous les champs.
    """
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'verification_requested_date', 'verification_completed_date'
        ]
        read_only_fields = UserSerializer.Meta.read_only_fields + [
            'verification_requested_date', 'verification_completed_date'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Sérialiseur pour le changement de mot de passe via l'API mobile.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Le mot de passe actuel est incorrect."))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"confirm_password": _("Les mots de passe ne correspondent pas.")}
            )
        validate_password(data['new_password'], self.context['request'].user)
        return data

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil étudiant dans l'API mobile.
    """
    user = UserSerializer(read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Student
        fields = [
            'user', 'current_level', 'school', 'school_name',
            'major', 'interests', 'average_grade'
        ]
        read_only_fields = ['user', 'school_name', 'average_grade']



class PupilProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil élève dans l'API mobile.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Pupil
        fields = [
            'user', 'school_name', 'current_level', 'specialization',
            'legal_guardian_name', 'legal_guardian_phone',
            'second_guardian_name', 'second_guardian_phone',
            'cafeteria', 'dietary_restrictions', 'school_transport',
            'transport_details', 'medical_information', 'school_insurance',
            'exit_permissions', 'siblings_at_school', 'desired_activities'
        ]
        read_only_fields = ['user']



class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil enseignant dans l'API mobile.
    """
    user = UserSerializer(read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Teacher
        fields = [
            'user', 'school', 'school_name', 'subjects',
            'qualifications', 'years_of_experience', 'expertise_areas'
        ]
        read_only_fields = ['user', 'school_name']


class AdvisorProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil conseiller dans l'API mobile.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Advisor
        fields = [
            'user', 'specialization', 'organization',
            'years_of_experience', 'expertise_areas'
        ]
        read_only_fields = ['user']


class AdministratorProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil administrateur dans l'API mobile.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Administrator
        fields = ['user', 'role']
        read_only_fields = ['user']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription d'un utilisateur via l'API mobile.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'first_name', 'last_name', 
            'phone_number', 'date_of_birth', 'address', 'city', 'type'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'type': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": _("Les mots de passe ne correspondent pas.")})
        
        return attrs
    
    def create(self, validated_data):
        # IMPORTANT: Supprimer password_confirm AVANT de créer l'utilisateur
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        
        # Créer l'utilisateur sans le mot de passe
        user = User(**validated_data)
        user.set_password(password)
        user.verification_status = 'unverified'
        user.save()
        
        return user


class StudentRegistrationSerializer(UserRegistrationSerializer):
    """
    Sérialiseur pour l'inscription d'un étudiant via l'API mobile.
    """
    current_level = serializers.CharField(required=True)
    major = serializers.CharField(required=False)
    interests = serializers.ListField(child=serializers.CharField(), required=False)
    
    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + ['current_level', 'major', 'interests']
    
    def validate(self, attrs):
        attrs = super().validate(attrs)
        
        # S'assurer que le type est 'student'
        attrs['type'] = 'student'
        
        return attrs
    
    def create(self, validated_data):
        # Extraire les données spécifiques à Student
        student_data = {
            'current_level': validated_data.pop('current_level', ''),
            'major': validated_data.pop('major', ''),
            'interests': validated_data.pop('interests', [])
        }

        # Créer l'utilisateur (le profil Student sera créé automatiquement)
        user = super().create(validated_data)

        # Mettre à jour le profil Student existant
        student = user.student_profile
        for key, value in student_data.items():
            setattr(student, key, value)
        student.save()

        return user










from django.db import transaction
from rest_framework import serializers
from ..models import Teacher, User


class TeacherRegistrationSerializer(UserRegistrationSerializer):
    # Champs spécifiques à l'enseignant
    institution_name = serializers.CharField(required=True)
    subjects = serializers.ListField(child=serializers.CharField(), required=True)
    highest_degree = serializers.CharField(required=True)
    years_of_experience = serializers.IntegerField(required=True)
    teaching_type = serializers.ListField(child=serializers.CharField(), required=True)
    qualifications = serializers.CharField(required=True)
    identity_document = serializers.FileField(required=True)
    degree_document = serializers.FileField(required=True)
    cv = serializers.FileField(required=True)

    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + [
            'institution_name', 'subjects', 'highest_degree',
            'years_of_experience', 'teaching_type', 'qualifications',
            'identity_document', 'degree_document', 'cv'
        ]

    def validate(self, data):
        """Validation supplémentaire avant la création"""
        if data.get('years_of_experience', 0) < 0:
            raise serializers.ValidationError({
                'years_of_experience': "Le nombre d'années d'expérience ne peut pas être négatif"
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        # Extraire les fichiers
        identity_document = validated_data.pop('identity_document')
        degree_document = validated_data.pop('degree_document')
        cv = validated_data.pop('cv')
        
        # Extraire les données de l'enseignant
        teacher_data = {
            'institution_name': validated_data.pop('institution_name'),
            'subjects': validated_data.pop('subjects'),
            'highest_degree': validated_data.pop('highest_degree'),
            'years_of_experience': validated_data.pop('years_of_experience'),
            'teaching_type': validated_data.pop('teaching_type'),
            'qualifications': validated_data.pop('qualifications'),
        }

        # Créer l'utilisateur
        user = super().create(validated_data)

        # Vérifier si un profil enseignant existe déjà
        if hasattr(user, 'teacher_profile'):
            teacher = user.teacher_profile
            # Mettre à jour les champs existants
            for key, value in teacher_data.items():
                setattr(teacher, key, value)
        else:
            # Créer un nouveau profil enseignant
            teacher = Teacher.objects.create(
                user=user,
                **teacher_data
            )

        # Gérer les fichiers
        teacher.identity_document = identity_document
        teacher.degree_document = degree_document
        teacher.cv = cv
        teacher.save()

        return user
















# accounts/serializers/mobile.py

class PupilRegistrationSerializer(UserRegistrationSerializer):
    """
    Sérialiseur pour l'inscription d'un élève via l'API mobile.
    """
    # Champs obligatoires
    school_name = serializers.CharField(required=True, max_length=255)
    current_level = serializers.CharField(required=True, max_length=100)
    legal_guardian_name = serializers.CharField(required=True, max_length=150)
    legal_guardian_phone = serializers.CharField(required=True, max_length=20)
    
    # Champs optionnels
    specialization = serializers.CharField(required=False, allow_blank=True, max_length=100)
    second_guardian_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    second_guardian_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    cafeteria = serializers.BooleanField(required=False, default=False)
    dietary_restrictions = serializers.CharField(required=False, allow_blank=True)
    school_transport = serializers.BooleanField(required=False, default=False)
    transport_details = serializers.CharField(required=False, allow_blank=True)
    medical_information = serializers.CharField(required=False, allow_blank=True)
    school_insurance = serializers.CharField(required=False, allow_blank=True, max_length=255)
    exit_permissions = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    siblings_at_school = serializers.CharField(required=False, allow_blank=True)
    desired_activities = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    communication_preferences = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + [
            'school_name', 'current_level', 'specialization',
            'legal_guardian_name', 'legal_guardian_phone',
            'second_guardian_name', 'second_guardian_phone',
            'cafeteria', 'dietary_restrictions', 'school_transport',
            'transport_details', 'medical_information', 'school_insurance',
            'exit_permissions', 'siblings_at_school', 'desired_activities',
            'communication_preferences'
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # S'assurer que le type est 'pupil'
        attrs['type'] = 'pupil'
        return attrs

    def create(self, validated_data):
        # Extraire les données spécifiques à Pupil
        pupil_data = {
            'school_name': validated_data.pop('school_name'),
            'current_level': validated_data.pop('current_level'),
            'specialization': validated_data.pop('specialization', ''),
            'legal_guardian_name': validated_data.pop('legal_guardian_name'),
            'legal_guardian_phone': validated_data.pop('legal_guardian_phone'),
            'second_guardian_name': validated_data.pop('second_guardian_name', ''),
            'second_guardian_phone': validated_data.pop('second_guardian_phone', ''),
            'cafeteria': validated_data.pop('cafeteria', False),
            'dietary_restrictions': validated_data.pop('dietary_restrictions', ''),
            'school_transport': validated_data.pop('school_transport', False),
            'transport_details': validated_data.pop('transport_details', ''),
            'medical_information': validated_data.pop('medical_information', ''),
            'school_insurance': validated_data.pop('school_insurance', ''),
            'exit_permissions': validated_data.pop('exit_permissions', []),
            'siblings_at_school': validated_data.pop('siblings_at_school', ''),
            'desired_activities': validated_data.pop('desired_activities', []),
        }
        
        # Créer l'utilisateur
        user = super().create(validated_data)
        
        # Créer le profil Pupil
        Pupil.objects.create(user=user, **pupil_data)
        
        return user



# Alternative plus sûre : Utiliser create_user de Django
class PupilRegistrationSerializerAlternative(UserRegistrationSerializer):
    """
    Version alternative utilisant create_user de Django
    """
    # ... mêmes champs que PupilRegistrationSerializer ...
    
    def create(self, validated_data):
        # Extraire les données spécifiques à Pupil
        pupil_data = {
            'school_name': validated_data.pop('school_name'),
            'current_level': validated_data.pop('current_level'),
            'legal_guardian_name': validated_data.pop('legal_guardian_name'),
            'legal_guardian_phone': validated_data.pop('legal_guardian_phone'),
            'second_guardian_name': validated_data.pop('second_guardian_name', ''),
            'second_guardian_phone': validated_data.pop('second_guardian_phone', ''),
            'cafeteria': validated_data.pop('cafeteria', False),
            'dietary_restrictions': validated_data.pop('dietary_restrictions', ''),
            'school_transport': validated_data.pop('school_transport', False),
            'transport_details': validated_data.pop('transport_details', ''),
            'medical_information': validated_data.pop('medical_information', ''),
            'school_insurance': validated_data.pop('school_insurance', ''),
            'exit_permissions': validated_data.pop('exit_permissions', []),
            'siblings_at_school': validated_data.pop('siblings_at_school', ''),
            'desired_activities': validated_data.pop('desired_activities', []),
        }
        
        # Supprimer password_confirm et extraire le password
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        
        # Utiliser create_user pour créer l'utilisateur de manière sécurisée
        user = User.objects.create_user(
            password=password,
            verification_status='unverified',
            **validated_data
        )
        
        # Créer le profil Pupil
        Pupil.objects.create(user=user, **pupil_data)
        
        return user



















class AdvisorRegistrationSerializer(UserRegistrationSerializer):
    """
    Sérialiseur pour l'inscription d'un conseiller via l'API mobile.
    """
    # Champs spécifiques au conseiller
    organization = serializers.CharField(required=True)
    specialization = serializers.CharField(required=True)
    years_of_experience = serializers.IntegerField(required=False, default=0)
    professional_license = serializers.CharField(required=False, allow_blank=True)
    certifications = serializers.ListField(child=serializers.CharField(), required=False)
    geographical_areas = serializers.ListField(child=serializers.CharField(), required=False)
    rates = serializers.DictField(required=False)
    portfolio_link = serializers.URLField(required=False, allow_blank=True)
    
    # Fichiers
    identity_document = serializers.FileField(required=True)
    portfolio = serializers.FileField(required=False)
    certification_documents = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )

    class Meta(UserRegistrationSerializer.Meta):
        fields = UserRegistrationSerializer.Meta.fields + [
            'organization', 'specialization', 'years_of_experience',
            'professional_license', 'certifications', 'geographical_areas',
            'rates', 'portfolio_link', 'identity_document', 'portfolio',
            'certification_documents'
        ]

    def validate(self, data):
        """Validation supplémentaire avant la création"""
        if data.get('years_of_experience', 0) < 0:
            raise serializers.ValidationError({
                'years_of_experience': "Le nombre d'années d'expérience ne peut pas être négatif"
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        # Extraire les fichiers
        identity_document = validated_data.pop('identity_document', None)
        portfolio = validated_data.pop('portfolio', None)
        certification_documents = validated_data.pop('certification_documents', [])
        
        # Extraire les données du conseiller
        advisor_data = {
            'organization': validated_data.pop('organization'),
            'specialization': validated_data.pop('specialization'),
            'years_of_experience': validated_data.pop('years_of_experience', 0),
            'professional_license': validated_data.pop('professional_license', ''),
            'certifications': validated_data.pop('certifications', []),
            'geographical_areas': validated_data.pop('geographical_areas', []),
            'rates': validated_data.pop('rates', {}),
            'portfolio_link': validated_data.pop('portfolio_link', ''),
        }

        # Créer l'utilisateur
        user = super().create(validated_data)

        # Créer le profil conseiller
        advisor = Advisor.objects.create(
            user=user,
            **advisor_data
        )

        # Gérer les fichiers
        if identity_document:
            advisor.identity_document = identity_document
        if portfolio:
            advisor.portfolio = portfolio
        if certification_documents:
            advisor.certification_documents = [doc.name for doc in certification_documents]
        
        advisor.save()

        return user


















class ProfilePictureSerializer(serializers.Serializer):
    """
    Sérialiseur pour la mise à jour de la photo de profil via l'API mobile.
    """
    profile_picture = serializers.ImageField(required=True)
    
    def update(self, instance, validated_data):
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.save()
        return instance
    



class PupilProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Pupil
        fields = [
            'user', 'school_name', 'current_level', 
            'legal_guardian_name', 'legal_guardian_phone',
        ]
        extra_kwargs = {
            'user': {'required': True},
            'school_name': {'required': True},
            'current_level': {'required': True},
            'legal_guardian_name': {'required': True},
            'legal_guardian_phone': {'required': True},
        }