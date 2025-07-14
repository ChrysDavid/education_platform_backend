# schools/serializers/web.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import (
    SchoolType, City, School, Department, Program,
    Facility, SchoolContact, SchoolReview, SchoolMedia, SchoolEvent
)
from .base import (
    SchoolTypeBaseSerializer, CityBaseSerializer, SchoolContactBaseSerializer,
    FacilityBaseSerializer, DepartmentBaseSerializer, ProgramBaseSerializer,
    SchoolReviewBaseSerializer, SchoolMediaBaseSerializer, SchoolEventBaseSerializer,
    SchoolBaseSerializer
)


class SchoolTypeWebSerializer(SchoolTypeBaseSerializer):
    """
    Sérialiseur pour l'interface web des types d'établissements.
    """
    school_count = serializers.SerializerMethodField()
    
    class Meta(SchoolTypeBaseSerializer.Meta):
        fields = SchoolTypeBaseSerializer.Meta.fields + ['school_count']
    
    def get_school_count(self, obj):
        """Retourne le nombre d'écoles de ce type."""
        return obj.schools.count()


class CityWebSerializer(CityBaseSerializer):
    """
    Sérialiseur pour l'interface web des villes.
    """
    school_count = serializers.SerializerMethodField()
    
    class Meta(CityBaseSerializer.Meta):
        fields = CityBaseSerializer.Meta.fields + ['school_count']
    
    def get_school_count(self, obj):
        """Retourne le nombre d'écoles dans cette ville."""
        return obj.schools.count()


class SchoolContactWebSerializer(SchoolContactBaseSerializer):
    """
    Sérialiseur pour l'interface web des contacts des établissements.
    """
    contact_type_display = serializers.CharField(source='get_contact_type_display', read_only=True)
    
    class Meta(SchoolContactBaseSerializer.Meta):
        fields = SchoolContactBaseSerializer.Meta.fields + ['contact_type_display']


class FacilityWebSerializer(FacilityBaseSerializer):
    """
    Sérialiseur pour l'interface web des équipements des établissements.
    """
    facility_type_display = serializers.CharField(source='get_facility_type_display', read_only=True)
    
    class Meta(FacilityBaseSerializer.Meta):
        fields = FacilityBaseSerializer.Meta.fields + ['facility_type_display']


class DepartmentWebSerializer(DepartmentBaseSerializer):
    """
    Sérialiseur pour l'interface web des départements des établissements.
    """
    program_count = serializers.SerializerMethodField()
    
    class Meta(DepartmentBaseSerializer.Meta):
        fields = DepartmentBaseSerializer.Meta.fields + ['program_count']
    
    def get_program_count(self, obj):
        """Retourne le nombre de programmes dans ce département."""
        return obj.programs.count()


class ProgramWebSerializer(ProgramBaseSerializer):
    """
    Sérialiseur pour l'interface web des programmes académiques.
    """
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta(ProgramBaseSerializer.Meta):
        fields = ProgramBaseSerializer.Meta.fields + ['department_name']


class SchoolReviewWebSerializer(SchoolReviewBaseSerializer):
    """
    Sérialiseur pour l'interface web des évaluations des établissements.
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta(SchoolReviewBaseSerializer.Meta):
        fields = SchoolReviewBaseSerializer.Meta.fields + ['user_name']
    
    def get_user_name(self, obj):
        """Retourne le nom complet de l'utilisateur."""
        return obj.user.get_full_name()


class SchoolMediaWebSerializer(SchoolMediaBaseSerializer):
    """
    Sérialiseur pour l'interface web des médias des établissements.
    """
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta(SchoolMediaBaseSerializer.Meta):
        fields = SchoolMediaBaseSerializer.Meta.fields + [
            'media_type_display', 'file_url', 'thumbnail_url'
        ]
    
    def get_file_url(self, obj):
        """Retourne l'URL du fichier."""
        if obj.file:
            return obj.file.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Retourne l'URL de la vignette."""
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class SchoolEventWebSerializer(SchoolEventBaseSerializer):
    """
    Sérialiseur pour l'interface web des événements des établissements.
    """
    is_past = serializers.BooleanField(read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta(SchoolEventBaseSerializer.Meta):
        fields = SchoolEventBaseSerializer.Meta.fields + [
            'image_url', 'is_past', 'is_ongoing'
        ]
    
    def get_image_url(self, obj):
        """Retourne l'URL de l'image."""
        if obj.image:
            return obj.image.url
        return None


class SchoolListWebSerializer(SchoolBaseSerializer):
    """
    Sérialiseur pour l'interface web de la liste des établissements (version légère).
    """
    school_type_name = serializers.CharField(source='school_type.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    
    class Meta(SchoolBaseSerializer.Meta):
        fields = SchoolBaseSerializer.Meta.fields + [
            'school_type_name', 'city_name', 'logo_url', 'average_rating'
        ]
    
    def get_average_rating(self, obj):
        """Calcule la note moyenne de l'établissement."""
        reviews = obj.reviews.filter(is_public=True)
        if not reviews.exists():
            return None
        return sum(review.rating for review in reviews) / reviews.count()
    
    def get_logo_url(self, obj):
        """Retourne l'URL du logo."""
        if obj.logo:
            return obj.logo.url
        return None


class SchoolDetailWebSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour l'interface web des établissements.
    """
    school_type = SchoolTypeWebSerializer(read_only=True)
    city = CityWebSerializer(read_only=True)
    departments = DepartmentWebSerializer(many=True, read_only=True)
    programs = ProgramWebSerializer(many=True, read_only=True)
    facilities = FacilityWebSerializer(many=True, read_only=True)
    contacts = SchoolContactWebSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    media = SchoolMediaWebSerializer(many=True, read_only=True)
    events = SchoolEventWebSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = '__all__'
    
    def get_reviews(self, obj):
        """Retourne uniquement les avis publics."""
        reviews = obj.reviews.filter(is_public=True)
        return SchoolReviewWebSerializer(reviews, many=True).data
    
    def get_average_rating(self, obj):
        """Calcule la note moyenne de l'établissement."""
        reviews = obj.reviews.filter(is_public=True)
        if not reviews.exists():
            return None
        return sum(review.rating for review in reviews) / reviews.count()
    
    def get_review_count(self, obj):
        """Retourne le nombre d'avis publics."""
        return obj.reviews.filter(is_public=True).count()
    
    def get_logo_url(self, obj):
        """Retourne l'URL du logo."""
        if obj.logo:
            return obj.logo.url
        return None
    
    def get_cover_image_url(self, obj):
        """Retourne l'URL de l'image de couverture."""
        if obj.cover_image:
            return obj.cover_image.url
        return None


class SchoolCreateUpdateWebSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'interface web de création et de mise à jour des établissements.
    """
    class Meta:
        model = School
        exclude = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validation personnalisée."""
        # Exemple de validation: vérifier que l'année de fondation est cohérente
        founded_year = data.get('founded_year')
        if founded_year and founded_year > 2023:
            raise serializers.ValidationError({
                'founded_year': _("L'année de fondation ne peut pas être dans le futur.")
            })
        return data