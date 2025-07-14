from rest_framework import serializers

from .base import (
    ResourceBaseSerializer, ResourceCategoryBaseSerializer, 
    ResourceReviewBaseSerializer, ResourceCommentBaseSerializer, 
    ResourceCollectionBaseSerializer
)
from ..models import Resource, ResourceReview, ResourceComment, ResourceCollection, CollectionResource


class MobileResourceCategorySerializer(ResourceCategoryBaseSerializer):
    """
    Sérialiseur mobile pour les catégories de ressources.
    Personnalise les champs pour l'application mobile.
    """
    pass


class MobileResourceSerializer(ResourceBaseSerializer):
    """
    Sérialiseur mobile pour les ressources.
    """
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta(ResourceBaseSerializer.Meta):
        fields = ResourceBaseSerializer.Meta.fields + [
            'file_url', 'thumbnail_url'
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


class MobileResourceReviewSerializer(ResourceReviewBaseSerializer):
    """
    Sérialiseur mobile pour les évaluations de ressources.
    """
    pass


class MobileResourceCommentSerializer(ResourceCommentBaseSerializer):
    """
    Sérialiseur mobile pour les commentaires de ressources.
    """
    replies = serializers.SerializerMethodField()
    
    class Meta(ResourceCommentBaseSerializer.Meta):
        fields = ResourceCommentBaseSerializer.Meta.fields + ['replies']
    
    def get_replies(self, obj):
        """Renvoie les réponses à ce commentaire."""
        replies = ResourceComment.objects.filter(
            parent=obj, is_public=True
        ).select_related('user')
        return MobileResourceCommentSerializer(replies, many=True).data


class MobileCollectionResourceSerializer(serializers.ModelSerializer):
    """
    Sérialiseur mobile pour les ressources dans une collection.
    """
    resource = MobileResourceSerializer(read_only=True)
    
    class Meta:
        model = CollectionResource
        fields = ['resource', 'order', 'added_at']


class MobileResourceCollectionSerializer(ResourceCollectionBaseSerializer):
    """
    Sérialiseur mobile pour les collections de ressources.
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
        return MobileCollectionResourceSerializer(collection_resources, many=True).data
    
    def get_cover_url(self, obj):
        """Renvoie l'URL de l'image de couverture."""
        if obj.cover_image:
            return obj.cover_image.url
        return None


class MobileResourceDetailSerializer(MobileResourceSerializer):
    """
    Sérialiseur détaillé pour les ressources (mobile).
    """
    reviews = MobileResourceReviewSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()
    
    class Meta(MobileResourceSerializer.Meta):
        fields = MobileResourceSerializer.Meta.fields + [
            'reviews', 'comments', 'collections', 
            'external_url', 'language', 'duration', 
            'author_name', 'source', 'license'
        ]
    
    def get_comments(self, obj):
        """Renvoie les commentaires de premier niveau de la ressource."""
        comments = ResourceComment.objects.filter(
            resource=obj, parent=None, is_public=True
        ).select_related('user')
        return MobileResourceCommentSerializer(comments, many=True).data
    
    def get_collections(self, obj):
        """Renvoie les collections publiques contenant cette ressource."""
        collections = ResourceCollection.objects.filter(
            resources=obj, is_public=True
        ).select_related('created_by')
        return MobileResourceCollectionSerializer(collections, many=True).data