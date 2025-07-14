from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    """
    Modèle représentant une catégorie de forum.
    """
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True)
    color = models.CharField(_('couleur'), max_length=20, blank=True, help_text=_('Code couleur hexadécimal'))
    
    # Paramètres
    order = models.PositiveIntegerField(_('ordre'), default=0)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Permissions
    requires_verification = models.BooleanField(_('nécessite une vérification'), default=False, 
                              help_text=_('Si activé, seuls les utilisateurs vérifiés peuvent publier dans cette catégorie'))
    authorized_groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groupes autorisés'),
        blank=True,
        help_text=_('Si spécifié, seuls les membres de ces groupes peuvent voir cette catégorie')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('catégorie')
        verbose_name_plural = _('catégories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'slug': self.slug})
    
    @property
    def topic_count(self):
        """Nombre de sujets dans cette catégorie"""
        return self.topics.count()
    
    @property
    def post_count(self):
        """Nombre de messages dans cette catégorie"""
        return Post.objects.filter(topic__category=self).count()
    
    @property
    def last_post(self):
        """Dernier message dans cette catégorie"""
        return Post.objects.filter(topic__category=self).order_by('-created_at').first()


class Topic(models.Model):
    """
    Modèle représentant un sujet de discussion.
    """
    STATUS_CHOICES = (
        ('open', _('Ouvert')),
        ('closed', _('Fermé')),
        ('pinned', _('Épinglé')),
        ('hidden', _('Caché')),
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name=_('catégorie')
    )
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='forum_topics',
        verbose_name=_('auteur')
    )
    
    # Statut
    status = models.CharField(_('statut'), max_length=10, choices=STATUS_CHOICES, default='open')
    
    # Tags
    tags = models.JSONField(_('tags'), default=list, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    last_activity_at = models.DateTimeField(_('dernière activité le'), auto_now_add=True)
    view_count = models.PositiveIntegerField(_('nombre de vues'), default=0)
    
    class Meta:
        verbose_name = _('sujet')
        verbose_name_plural = _('sujets')
        ordering = ['-last_activity_at']
        unique_together = ['category', 'slug']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            
            # S'assurer que le slug est unique dans la catégorie
            original_slug = self.slug
            counter = 1
            while Topic.objects.filter(category=self.category, slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
                
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('forum:topic_detail', kwargs={
            'category_slug': self.category.slug,
            'topic_slug': self.slug
        })
    
    def increment_view_count(self):
        """Incrémente le compteur de vues"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def update_last_activity(self):
        """Met à jour la date de dernière activité"""
        self.last_activity_at = timezone.now()
        self.save(update_fields=['last_activity_at'])
    
    @property
    def post_count(self):
        """Nombre de messages dans ce sujet"""
        return self.posts.count()
    
    @property
    def last_post(self):
        """Dernier message dans ce sujet"""
        return self.posts.order_by('-created_at').first()
    
    @property
    def first_post(self):
        """Premier message (message initial) dans ce sujet"""
        return self.posts.order_by('created_at').first()
    
    @property
    def is_closed(self):
        """Indique si le sujet est fermé"""
        return self.status == 'closed'
    
    @property
    def is_pinned(self):
        """Indique si le sujet est épinglé"""
        return self.status == 'pinned'
    
    @property
    def is_hidden(self):
        """Indique si le sujet est caché"""
        return self.status == 'hidden'


class Post(models.Model):
    """
    Modèle représentant un message dans un sujet.
    """
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('sujet')
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='forum_posts',
        verbose_name=_('auteur')
    )
    content = models.TextField(_('contenu'))
    
    # Statut
    is_hidden = models.BooleanField(_('caché'), default=False)
    is_edited = models.BooleanField(_('édité'), default=False)
    
    # Paramètres
    is_solution = models.BooleanField(_('est une solution'), default=False,
                               help_text=_('Indique si ce message a été marqué comme solution au sujet'))
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.author.get_full_name() if self.author else 'Utilisateur supprimé'} - {self.topic.title[:30]}"
    
    def get_absolute_url(self):
        return f"{self.topic.get_absolute_url()}#post-{self.id}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # Enregistrer le message
        super().save(*args, **kwargs)
        
        # Mettre à jour la date de dernière activité du sujet
        if is_new:
            self.topic.update_last_activity()
    
    def mark_as_solution(self):
        """Marque ce message comme solution au sujet"""
        # Démarquer tout autre message éventuellement marqué comme solution
        self.topic.posts.filter(is_solution=True).update(is_solution=False)
        
        # Marquer ce message comme solution
        self.is_solution = True
        self.save(update_fields=['is_solution'])


class PostReaction(models.Model):
    """
    Modèle représentant une réaction à un message.
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('message')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_reactions',
        verbose_name=_('utilisateur')
    )
    reaction = models.CharField(_('réaction'), max_length=50)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('réaction')
        verbose_name_plural = _('réactions')
        unique_together = ['post', 'user', 'reaction']
    
    def __str__(self):
        return f"{self.user.get_full_name()} a réagi '{self.reaction}' au message de {self.post.author.get_full_name() if self.post.author else 'Utilisateur supprimé'}"


class TopicSubscription(models.Model):
    """
    Modèle représentant l'abonnement d'un utilisateur à un sujet.
    """
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('sujet')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_subscriptions',
        verbose_name=_('utilisateur')
    )
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    # Paramètres de notification
    notify_on_new_post = models.BooleanField(_('notifier pour les nouveaux messages'), default=True)
    
    class Meta:
        verbose_name = _('abonnement')
        verbose_name_plural = _('abonnements')
        unique_together = ['topic', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} abonné à '{self.topic.title}'"


class TopicView(models.Model):
    """
    Modèle représentant la consultation d'un sujet par un utilisateur.
    """
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name=_('sujet')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_views',
        verbose_name=_('utilisateur')
    )
    viewed_at = models.DateTimeField(_('consulté le'), auto_now=True)
    
    class Meta:
        verbose_name = _('vue de sujet')
        verbose_name_plural = _('vues de sujets')
        unique_together = ['topic', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} a consulté '{self.topic.title}'"


class PostReport(models.Model):
    """
    Modèle représentant un signalement de message inapproprié.
    """
    STATUS_CHOICES = (
        ('pending', _('En attente')),
        ('reviewing', _('En cours de revue')),
        ('resolved', _('Résolu')),
        ('rejected', _('Rejeté')),
    )
    
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('message')
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='forum_reports',
        verbose_name=_('signaleur')
    )
    reason = models.TextField(_('raison'))
    
    # Traitement
    status = models.CharField(_('statut'), max_length=10, choices=STATUS_CHOICES, default='pending')
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_forum_reports',
        verbose_name=_('traité par')
    )
    resolution_notes = models.TextField(_('notes de résolution'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('signalement')
        verbose_name_plural = _('signalements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Signalement de {self.reporter.get_full_name()} - {self.get_status_display()}"