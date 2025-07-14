from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .base import (
    ResourceBaseSerializer, ResourceCategoryBaseSerializer, 
    ResourceReviewBaseSerializer, ResourceCommentBaseSerializer, 
    ResourceCollectionBaseSerializer
)
from ..models import Resource, ResourceReview, ResourceComment, ResourceCollection, CollectionResource


class WebResourceCategorySerializer(ResourceCategoryBaseSerializer):
    """
    Sérialiseur web pour les catégories de ressources.
    Ajoute des champs spécifiques à l'interface web si nécessaire.
    """
    pass


class WebResourceSerializer(ResourceBaseSerializer):
    """
    Sérialiseur web pour les ressources.
    """
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta(ResourceBaseSerializer.Meta):
        fields = ResourceBaseSerializer.Meta.fields + [
            'file_url', 'thumbnail_url', 'external_url', 
            'language', 'duration', 'author_name', 'source', 'license'
        ]
    
    def get_file_url(self, obj):
        """Renvoie l'URL du fichier."""
        if obj.file:
            return obj.file.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Renvoie l'URL de la vignette."""
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class WebResourceReviewSerializer(ResourceReviewBaseSerializer):
    """
    Sérialiseur web pour les évaluations de ressources.
    """
    def validate(self, data):
        """Vérifie que l'utilisateur n'a pas déjà évalué cette ressource."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            resource_id = self.context['view'].kwargs.get('pk')
            if resource_id and ResourceReview.objects.filter(
                resource_id=resource_id, user=request.user
            ).exists():
                raise serializers.ValidationError(_("Vous avez déjà évalué cette ressource."))
        return data


class WebResourceCommentSerializer(ResourceCommentBaseSerializer):
    """
    Sérialiseur web pour les commentaires de ressources.
    """
    replies = serializers.SerializerMethodField()
    
    class Meta(ResourceCommentBaseSerializer.Meta):
        fields = ResourceCommentBaseSerializer.Meta.fields + ['replies']
    
    def get_replies(self, obj):
        """Renvoie les réponses à ce commentaire."""
        replies = ResourceComment.objects.filter(
            parent=obj, is_public=True
        ).select_related('user')
        return WebResourceCommentSerializer(replies, many=True).data


class WebCollectionResourceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur web pour les ressources dans une collection.
    """
    resource = WebResourceSerializer(read_only=True)
    
    class Meta:
        model = CollectionResource
        fields = ['resource', 'order', 'added_at']


class WebResourceCollectionSerializer(ResourceCollectionBaseSerializer):
    """
    Sérialiseur web pour les collections de ressources.
    """
    resources = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    
    class Meta(ResourceCollectionBaseSerializer.Meta):
        fields = ResourceCollectionBaseSerializer.Meta.fields + [
            'resources', 'cover_url'
        ]
    
    def get_resources(self, obj):
        """Renvoie les ressources de la collection avec leur ordre."""
        collection_resources = CollectionResource.objects.filter(
            collection=obj
        ).select_related('resource').order_by('order')
        return WebCollectionResourceSerializer(collection_resources, many=True).data
    
    def get_cover_url(self, obj):
        """Renvoie l'URL de l'image de couverture."""
        if obj.cover_image:
            return obj.cover_image.url
        return None


class WebResourceDetailSerializer(WebResourceSerializer):
    """
    Sérialiseur détaillé pour les ressources (web).
    """
    reviews = WebResourceReviewSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()
    
    class Meta(WebResourceSerializer.Meta):
        fields = WebResourceSerializer.Meta.fields + [
            'reviews', 'comments', 'collections'
        ]
    
    def get_comments(self, obj):
        """Renvoie les commentaires de premier niveau de la ressource."""
        comments = ResourceComment.objects.filter(
            resource=obj, parent=None, is_public=True
        ).select_related('user')
        return WebResourceCommentSerializer(comments, many=True).data
    
    def get_collections(self, obj):
        """Renvoie les collections publiques contenant cette ressource."""
        collections = ResourceCollection.objects.filter(
            resources=obj, is_public=True
        ).select_related('created_by')
        return WebResourceCollectionSerializer(collections, many=True).data