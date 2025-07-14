from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class NotificationType(models.Model):
    """
    Modèle pour les différents types de notifications.
    """
    code = models.CharField(_('code'), max_length=100, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Modèles de message
    title_template = models.CharField(_('modèle de titre'), max_length=255)
    body_template = models.TextField(_('modèle de corps'))
    
    # Options de livraison
    has_email = models.BooleanField(_('envoi par email'), default=True)
    has_in_app = models.BooleanField(_('envoi dans l\'application'), default=True)
    has_push = models.BooleanField(_('envoi par notification push'), default=False)
    
    # Icône et couleur pour l'affichage
    icon = models.CharField(_('icône'), max_length=50, blank=True)
    color = models.CharField(_('couleur'), max_length=20, blank=True)
    
    # Paramètres
    is_active = models.BooleanField(_('actif'), default=True)
    default_user_preference = models.BooleanField(_('préférence utilisateur par défaut'), default=True)
    
    # Pour l'ordre d'affichage dans les paramètres
    order = models.PositiveIntegerField(_('ordre'), default=0)
    
    class Meta:
        verbose_name = _('type de notification')
        verbose_name_plural = _('types de notification')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class UserNotificationPreference(models.Model):
    """
    Modèle pour les préférences de notification des utilisateurs.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('utilisateur')
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='user_preferences',
        verbose_name=_('type de notification')
    )
    
    # Préférences par canal
    email_enabled = models.BooleanField(_('email activé'), default=True)
    in_app_enabled = models.BooleanField(_('notifications in-app activées'), default=True)
    push_enabled = models.BooleanField(_('notifications push activées'), default=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('préférence de notification')
        verbose_name_plural = _('préférences de notification')
        unique_together = ('user', 'notification_type')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.notification_type.name}"


class Notification(models.Model):
    """
    Modèle pour les notifications envoyées aux utilisateurs.
    """
    STATUS_CHOICES = (
        ('unread', _('Non lue')),
        ('read', _('Lue')),
        ('archived', _('Archivée')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('utilisateur')
    )
    
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notifications',
        verbose_name=_('type de notification')
    )
    
    # Contenu
    title = models.CharField(_('titre'), max_length=255)
    body = models.TextField(_('corps'))
    
    # Référence à l'objet lié (polymorphique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('type de contenu')
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Paramètres d'action
    action_url = models.CharField(_('URL d\'action'), max_length=255, blank=True)
    action_text = models.CharField(_('texte d\'action'), max_length=100, blank=True)
    
    # Métadonnées supplémentaires
    data = models.JSONField(_('données'), default=dict, blank=True)
    
    # États et dates
    status = models.CharField(_('statut'), max_length=10, choices=STATUS_CHOICES, default='unread')
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    read_at = models.DateTimeField(_('lu le'), null=True, blank=True)
    archived_at = models.DateTimeField(_('archivé le'), null=True, blank=True)
    
    # Suivi de livraison
    sent_by_email = models.BooleanField(_('envoyé par email'), default=False)
    sent_by_push = models.BooleanField(_('envoyé par notification push'), default=False)
    
    class Meta:
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()} ({self.get_status_display()})"
    
    def mark_as_read(self):
        """
        Marque la notification comme lue.
        """
        if self.status == 'unread':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_unread(self):
        """
        Marque la notification comme non lue.
        """
        self.status = 'unread'
        self.read_at = None
        self.save(update_fields=['status', 'read_at'])
    
    def archive(self):
        """
        Archive la notification.
        """
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save(update_fields=['status', 'archived_at'])
    
    @property
    def is_read(self):
        """
        Indique si la notification a été lue.
        """
        return self.status == 'read'
    
    @property
    def is_archived(self):
        """
        Indique si la notification a été archivée.
        """
        return self.status == 'archived'


class NotificationTemplate(models.Model):
    """
    Modèle pour les modèles de notifications.
    """
    code = models.CharField(_('code'), max_length=100, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    subject_template = models.CharField(_('modèle de sujet d\'email'), max_length=255, blank=True)
    email_template = models.TextField(_('modèle d\'email'), blank=True)
    
    title_template = models.CharField(_('modèle de titre'), max_length=255)
    body_template = models.TextField(_('modèle de corps'))
    
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name=_('type de notification')
    )
    
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('modèle de notification')
        verbose_name_plural = _('modèles de notification')
        ordering = ['notification_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.notification_type.name})"


class DeviceToken(models.Model):
    """
    Modèle pour les tokens des appareils pour les notifications push.
    """
    PLATFORM_CHOICES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_tokens',
        verbose_name=_('utilisateur')
    )
    
    token = models.CharField(_('token'), max_length=255)
    platform = models.CharField(_('plateforme'), max_length=10, choices=PLATFORM_CHOICES)
    device_name = models.CharField(_('nom de l\'appareil'), max_length=255, blank=True)
    
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    last_used_at = models.DateTimeField(_('dernière utilisation'), auto_now=True)
    
    class Meta:
        verbose_name = _('token d\'appareil')
        verbose_name_plural = _('tokens d\'appareil')
        unique_together = ('user', 'token')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.device_name} ({self.platform})"