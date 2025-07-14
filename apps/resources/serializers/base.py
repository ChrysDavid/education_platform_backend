from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from ..models import (
    ResourceCategory, Resource, ResourceReview, ResourceComment,
    ResourceCollection, CollectionResource
)


class ResourceCategoryBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les catégories de ressources.
    """
    resource_count = serializers.IntegerField(read_only=True)
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon',
            'parent', 'order', 'resource_count', 'subcategories'
        ]
    
    def get_subcategories(self, obj):
        """Renvoie les sous-catégories actives."""
        subcategories = obj.subcategories.filter(is_active=True)
        if subcategories:
            return ResourceCategoryBaseSerializer(subcategories, many=True).data
        return []


class ResourceBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les ressources.
    """
    creator_name = serializers.SerializerMethodField()
    categories = ResourceCategoryBaseSerializer(many=True, read_only=True)
    rating = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'slug', 'description', 'created_by', 'creator_name',
            'resource_type', 'access_level', 'categories', 
            'created_at', 'view_count', 'download_count',
            'like_count', 'rating', 'tags', 'is_approved', 'is_featured'
        ]
    
    def get_creator_name(self, obj):
        """Renvoie le nom du créateur."""
        return obj.created_by.get_full_name()


class ResourceReviewBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les évaluations des ressources.
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceReview
        fields = [
            'id', 'resource', 'user', 'user_name', 'rating',
            'comment', 'created_at', 'updated_at', 'is_public'
        ]
        read_only_fields = ['user', 'resource', 'created_at', 'updated_at']
    
    def get_user_name(self, obj):
        """Renvoie le nom de l'utilisateur."""
        return obj.user.get_full_name()


class ResourceCommentBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les commentaires des ressources.
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceComment
        fields = [
            'id', 'resource', 'user', 'user_name', 'content',
            'parent', 'created_at', 'updated_at', 'is_edited',
            'is_public'
        ]
        read_only_fields = ['user', 'resource', 'created_at', 'updated_at', 'is_edited']
    
    def get_user_name(self, obj):
        """Renvoie le nom de l'utilisateur."""
        return obj.user.get_full_name()


class ResourceCollectionBaseSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les collections de ressources.
    """
    creator_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ResourceCollection
        fields = [
            'id', 'title', 'slug', 'description', 'created_by',
            'creator_name', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_creator_name(self, obj):
        """Renvoie le nom du créateur."""
        return obj.created_by.get_full_name()