from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.utils.text import slugify

from .models import (
    Resource, ResourceCategory, ResourceReview, ResourceComment,
    ResourceLike, ResourceCollection, CollectionResource
)


@receiver(post_save, sender=Resource)
def create_resource_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour la ressource si nécessaire.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.title)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà
        while Resource.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug
        instance.save(update_fields=['slug'])


@receiver(post_save, sender=ResourceCategory)
def create_category_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour la catégorie si nécessaire.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà
        while ResourceCategory.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug
        instance.save(update_fields=['slug'])


@receiver(post_save, sender=ResourceCollection)
def create_collection_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour la collection si nécessaire.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.title)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà
        while ResourceCollection.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        instance.slug = slug
        instance.save(update_fields=['slug'])


@receiver(post_save, sender=ResourceReview)
@receiver(post_delete, sender=ResourceReview)
def update_resource_rating_cache(sender, instance, **kwargs):
    """
    Met à jour le cache de la note moyenne de la ressource.
    """
    resource = instance.resource
    cache_key = f'resource_rating_{resource.id}'
    
    # Calculer la nouvelle note moyenne
    reviews = ResourceReview.objects.filter(resource=resource, is_public=True)
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()
    else:
        avg_rating = 0
    
    # Mettre à jour le cache
    cache.set(cache_key, avg_rating, 86400)  # Cache pour 24 heures


@receiver(pre_delete, sender=Resource)
def delete_resource_files(sender, instance, **kwargs):
    """
    Supprime les fichiers associés à une ressource lors de sa suppression.
    """
    if instance.file:
        instance.file.delete(False)
    
    if instance.thumbnail:
        instance.thumbnail.delete(False)


@receiver(pre_delete, sender=ResourceCollection)
def delete_collection_cover(sender, instance, **kwargs):
    """
    Supprime l'image de couverture d'une collection lors de sa suppression.
    """
    if instance.cover_image:
        instance.cover_image.delete(False)


@receiver(post_save, sender=ResourceLike)
@receiver(post_delete, sender=ResourceLike)
def update_resource_like_count(sender, instance, **kwargs):
    """
    Met à jour le compteur de j'aime d'une ressource.
    """
    resource = instance.resource
    resource.like_count = ResourceLike.objects.filter(resource=resource).count()
    resource.save(update_fields=['like_count'])