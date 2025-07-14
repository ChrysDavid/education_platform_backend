from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings


class ResourceCategory(models.Model):
    """
    Modèle représentant une catégorie de ressources pédagogiques.
    """
    name = models.CharField(_('nom'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True, help_text=_('Nom de l\'icône CSS'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('catégorie parente')
    )
    order = models.PositiveIntegerField(_('ordre'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('catégorie de ressource')
        verbose_name_plural = _('catégories de ressource')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def resource_count(self):
        """
        Retourne le nombre de ressources dans cette catégorie.
        """
        return self.resources.filter(is_active=True).count()


class Resource(models.Model):
    """
    Modèle représentant une ressource pédagogique.
    """
    TYPE_CHOICES = (
        ('document', _('Document')),
        ('image', _('Image')),
        ('video', _('Vidéo')),
        ('audio', _('Audio')),
        ('link', _('Lien externe')),
        ('exercise', _('Exercice')),
        ('lesson', _('Leçon')),
        ('quiz', _('Quiz')),
        ('other', _('Autre')),
    )
    
    ACCESS_LEVEL_CHOICES = (
        ('public', _('Public')),
        ('verified', _('Utilisateurs vérifiés')),
        ('students', _('Étudiants')),
        ('teachers', _('Enseignants')),
        ('advisors', _('Conseillers')),
        ('private', _('Privé (créateur uniquement)')),
    )
    
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_('description'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resources',
        verbose_name=_('créé par')
    )
    resource_type = models.CharField(_('type de ressource'), max_length=20, choices=TYPE_CHOICES)
    access_level = models.CharField(_('niveau d\'accès'), max_length=20, choices=ACCESS_LEVEL_CHOICES, default='public')
    categories = models.ManyToManyField(
        ResourceCategory,
        related_name='resources',
        verbose_name=_('catégories')
    )
    file = models.FileField(_('fichier'), upload_to='resources/', blank=True, null=True)
    external_url = models.URLField(_('URL externe'), blank=True, null=True)
    thumbnail = models.ImageField(_('vignette'), upload_to='resource_thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    
    # Métadonnées
    tags = models.JSONField(_('tags'), default=list, blank=True)
    language = models.CharField(_('langue'), max_length=10, blank=True)
    duration = models.PositiveIntegerField(_('durée (minutes)'), null=True, blank=True)
    author_name = models.CharField(_('nom de l\'auteur'), max_length=255, blank=True)
    source = models.CharField(_('source'), max_length=255, blank=True)
    license = models.CharField(_('licence'), max_length=100, blank=True)
    
    # Statistiques
    view_count = models.PositiveIntegerField(_('nombre de vues'), default=0)
    download_count = models.PositiveIntegerField(_('nombre de téléchargements'), default=0)
    like_count = models.PositiveIntegerField(_('nombre de j\'aime'), default=0)
    
    # État
    is_approved = models.BooleanField(_('approuvée'), default=False)
    is_featured = models.BooleanField(_('mise en avant'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    
    class Meta:
        verbose_name = _('ressource')
        verbose_name_plural = _('ressources')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resource_type']),
            models.Index(fields=['access_level']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Vérifier si le slug existe déjà
            while Resource.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def increment_view_count(self):
        """
        Incrémente le compteur de vues de la ressource.
        """
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        """
        Incrémente le compteur de téléchargements de la ressource.
        """
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def toggle_like(self, user):
        """
        Ajoute ou retire un j'aime pour un utilisateur.
        """
        like, created = ResourceLike.objects.get_or_create(resource=self, user=user)
        if not created:  # L'utilisateur a déjà aimé cette ressource
            like.delete()
            self.like_count = max(0, self.like_count - 1)
        else:  # Nouvel aime
            self.like_count += 1
        
        self.save(update_fields=['like_count'])
        return created  # True si ajouté, False si retiré
    
    @property
    def file_size(self):
        """
        Retourne la taille du fichier en octets.
        """
        if self.file and hasattr(self.file, 'size'):
            return self.file.size
        return 0
    
    @property
    def file_extension(self):
        """
        Retourne l'extension du fichier.
        """
        if self.file:
            name = self.file.name
            return name.split('.')[-1].lower() if '.' in name else ''
        return ''
    
    @property
    def rating(self):
        """
        Calcule la note moyenne de cette ressource.
        """
        ratings = self.reviews.all()
        if not ratings:
            return 0
        return sum(r.rating for r in ratings) / len(ratings)


class ResourceReview(models.Model):
    """
    Modèle représentant une évaluation d'une ressource.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('ressource')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_reviews',
        verbose_name=_('utilisateur')
    )
    rating = models.PositiveSmallIntegerField(
        _('note'),
        choices=[(i, i) for i in range(1, 6)]
    )
    comment = models.TextField(_('commentaire'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_public = models.BooleanField(_('public'), default=True)
    
    class Meta:
        verbose_name = _('évaluation de ressource')
        verbose_name_plural = _('évaluations de ressource')
        ordering = ['-created_at']
        unique_together = ('resource', 'user')
    
    def __str__(self):
        return f"Évaluation de {self.user.get_full_name()} pour {self.resource.title}"


class ResourceLike(models.Model):
    """
    Modèle représentant un j'aime sur une ressource.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('ressource')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_likes',
        verbose_name=_('utilisateur')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('j\'aime')
        verbose_name_plural = _('j\'aime')
        unique_together = ('resource', 'user')
    
    def __str__(self):
        return f"J'aime de {self.user.get_full_name()} pour {self.resource.title}"


class ResourceComment(models.Model):
    """
    Modèle représentant un commentaire sur une ressource.
    """
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('ressource')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_comments',
        verbose_name=_('utilisateur')
    )
    content = models.TextField(_('contenu'))
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('commentaire parent')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_edited = models.BooleanField(_('édité'), default=False)
    is_public = models.BooleanField(_('public'), default=True)
    
    class Meta:
        verbose_name = _('commentaire')
        verbose_name_plural = _('commentaires')
        ordering = ['created_at']
    
    def __str__(self):
        return f"Commentaire de {self.user.get_full_name()} sur {self.resource.title}"


class ResourceCollection(models.Model):
    """
    Modèle représentant une collection de ressources.
    """
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_('description'), blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resource_collections',
        verbose_name=_('créé par')
    )
    resources = models.ManyToManyField(
        Resource,
        through='CollectionResource',
        related_name='collections',
        verbose_name=_('ressources')
    )
    cover_image = models.ImageField(_('image de couverture'), upload_to='collection_covers/', blank=True, null=True)
    is_public = models.BooleanField(_('public'), default=True)
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('collection de ressources')
        verbose_name_plural = _('collections de ressources')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            
            # Vérifier si le slug existe déjà
            while ResourceCollection.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class CollectionResource(models.Model):
    """
    Modèle intermédiaire pour gérer l'ordre des ressources dans une collection.
    """
    collection = models.ForeignKey(
        ResourceCollection,
        on_delete=models.CASCADE,
        verbose_name=_('collection')
    )
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        verbose_name=_('ressource')
    )
    order = models.PositiveIntegerField(_('ordre'), default=0)
    added_at = models.DateTimeField(_('ajouté le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('ressource de collection')
        verbose_name_plural = _('ressources de collection')
        ordering = ['order']
        unique_together = ('collection', 'resource')
    
    def __str__(self):
        return f"{self.resource.title} dans {self.collection.title}"