from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils.text import slugify
from django.db.models import Avg
from django.core.cache import cache

from .models import (
    School, Department, Program, SchoolReview, SchoolMedia, SchoolEvent
)


@receiver(post_save, sender=School)
def create_school_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour l'école si aucun n'est fourni.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà
        while School.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        if slug != instance.slug:
            instance.slug = slug
            instance.save(update_fields=['slug'])


@receiver(post_save, sender=Department)
def create_department_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour le département si aucun n'est fourni.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà pour cette école
        while Department.objects.filter(
            school=instance.school, slug=slug
        ).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        if slug != instance.slug:
            instance.slug = slug
            instance.save(update_fields=['slug'])


@receiver(post_save, sender=Program)
def create_program_slug(sender, instance, created, **kwargs):
    """
    Crée automatiquement un slug pour le programme si aucun n'est fourni.
    """
    if created and not instance.slug:
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        
        # Vérifier si le slug existe déjà pour cette école
        while Program.objects.filter(
            school=instance.school, slug=slug
        ).exclude(pk=instance.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        if slug != instance.slug:
            instance.slug = slug
            instance.save(update_fields=['slug'])


@receiver(post_save, sender=SchoolReview)
def update_school_rating_cache(sender, instance, **kwargs):
    """
    Met à jour le cache de la note moyenne de l'école lorsqu'un avis est ajouté ou modifié.
    """
    # Recalculer la note moyenne
    avg_rating = SchoolReview.objects.filter(
        school=instance.school, is_public=True
    ).aggregate(Avg('rating'))['rating__avg']
    
    # Mettre à jour le cache
    cache_key = f'school_rating_{instance.school.id}'
    cache.set(cache_key, avg_rating, 86400)  # Cache pour 24 heures
    
    # Mise à jour du nombre d'avis
    review_count_key = f'school_review_count_{instance.school.id}'
    review_count = SchoolReview.objects.filter(
        school=instance.school, is_public=True
    ).count()
    cache.set(review_count_key, review_count, 86400)  # Cache pour 24 heures


@receiver(post_delete, sender=SchoolReview)
def handle_review_deletion(sender, instance, **kwargs):
    """
    Met à jour le cache lorsqu'un avis est supprimé.
    """
    # Recalculer la note moyenne
    avg_rating = SchoolReview.objects.filter(
        school=instance.school, is_public=True
    ).aggregate(Avg('rating'))['rating__avg']
    
    # Mettre à jour le cache
    cache_key = f'school_rating_{instance.school.id}'
    cache.set(cache_key, avg_rating, 86400)  # Cache pour 24 heures
    
    # Mise à jour du nombre d'avis
    review_count_key = f'school_review_count_{instance.school.id}'
    review_count = SchoolReview.objects.filter(
        school=instance.school, is_public=True
    ).count()
    cache.set(review_count_key, review_count, 86400)  # Cache pour 24 heures


@receiver(pre_delete, sender=SchoolMedia)
def delete_school_media_files(sender, instance, **kwargs):
    """
    Supprime les fichiers associés à un média lors de sa suppression.
    """
    # Supprimer le fichier principal
    if instance.file:
        instance.file.delete(False)
    
    # Supprimer la vignette
    if instance.thumbnail:
        instance.thumbnail.delete(False)


@receiver(pre_delete, sender=School)
def delete_school_media(sender, instance, **kwargs):
    """
    Supprime les fichiers associés à une école lors de sa suppression.
    """
    # Supprimer le logo
    if instance.logo:
        instance.logo.delete(False)
    
    # Supprimer l'image de couverture
    if instance.cover_image:
        instance.cover_image.delete(False)