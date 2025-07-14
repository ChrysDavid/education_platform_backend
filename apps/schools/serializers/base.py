# schools/serializers/base.py
from rest_framework import serializers

from ..models import (
    SchoolType, City, School, Department, Program,
    Facility, SchoolContact, SchoolReview, SchoolMedia, SchoolEvent
)


class SchoolTypeBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les types d'établissements.
    """
    class Meta:
        model = SchoolType
        fields = ['id', 'name', 'slug', 'description']


class CityBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les villes.
    """
    class Meta:
        model = City
        fields = [
            'id', 'name', 'region', 'zip_code', 'longitude', 
            'latitude', 'is_active'
        ]


class SchoolContactBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les contacts des établissements.
    """
    class Meta:
        model = SchoolContact
        fields = [
            'id', 'name', 'title', 'contact_type',
            'phone', 'email', 'description', 'is_active'
        ]


class FacilityBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les équipements des établissements.
    """
    class Meta:
        model = Facility
        fields = [
            'id', 'name', 'facility_type',
            'description', 'image', 'quantity', 'is_active'
        ]


class DepartmentBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les départements des établissements.
    """
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'slug', 'description', 'head_name',
            'is_active'
        ]


class ProgramBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les programmes académiques.
    """
    class Meta:
        model = Program
        fields = [
            'id', 'name', 'slug', 'code', 'description', 'duration',
            'level', 'degree_awarded', 'is_active', 'department',
            'admission_requirements', 'career_opportunities'
        ]


class SchoolReviewBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les évaluations des établissements.
    """
    class Meta:
        model = SchoolReview
        fields = [
            'id', 'user', 'rating', 'title', 'comment',
            'created_at', 'updated_at', 'is_verified', 'is_public'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_verified']


class SchoolMediaBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les médias des établissements.
    """
    class Meta:
        model = SchoolMedia
        fields = [
            'id', 'title', 'description', 'media_type',
            'file', 'thumbnail', 'created_at', 'is_public'
        ]
        read_only_fields = ['created_at']


class SchoolEventBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les événements des établissements.
    """
    class Meta:
        model = SchoolEvent
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'location', 'contact_email', 'contact_phone', 'image',
            'registration_url', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SchoolBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les établissements.
    """
    class Meta:
        model = School
        fields = [
            'id', 'name', 'slug', 'school_type', 'city', 'logo',
            'is_verified', 'is_active'
        ]