from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Conversation(models.Model):
    """
    Modèle représentant une conversation entre plusieurs utilisateurs.
    """
    CONVERSATION_TYPE_CHOICES = (
        ('direct', _('Message direct')),
        ('group', _('Groupe')),
        ('support', _('Support')),
        ('system', _('Système')),
    )
    
    # Informations de base
    title = models.CharField(_('titre'), max_length=255, blank=True)
    conversation_type = models.CharField(_('type de conversation'), max_length=10, choices=CONVERSATION_TYPE_CHOICES)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_conversations',
        verbose_name=_('créé par')
    )
    
    # Paramètres de groupe
    is_group = models.BooleanField(_('est un groupe'), default=False)
    group_avatar = models.ImageField(_('avatar du groupe'), upload_to='conversation_avatars/', blank=True, null=True)
    group_description = models.TextField(_('description du groupe'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    last_message_at = models.DateTimeField(_('dernier message le'), auto_now_add=True)
    
    # Relation polymorphique (pour les conversations liées à un objet spécifique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('type de contenu')
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-last_message_at']
    
    def __str__(self):
        if self.title:
            return self.title
        
        # Pour les messages directs sans titre, utiliser les noms des participants
        if self.conversation_type == 'direct':
            participants = self.participants.all()
            if participants.count() == 2:
                return f"{participants[0].get_full_name()} - {participants[1].get_full_name()}"
        
        return f"Conversation #{self.id}"
    
    def get_participants(self):
        """
        Renvoie la liste des participants à la conversation.
        """
        return self.participants.select_related('user')
    
    def add_participant(self, user, is_admin=False):
        """
        Ajoute un participant à la conversation.
        """
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=self,
            user=user,
            defaults={'is_admin': is_admin}
        )
        return participant
    
    def remove_participant(self, user):
        """
        Retire un participant de la conversation.
        """
        ConversationParticipant.objects.filter(conversation=self, user=user).delete()
    
    def update_last_message_time(self):
        """
        Met à jour la date du dernier message.
        """
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at'])
    
    @property
    def participants_count(self):
        """
        Renvoie le nombre de participants à la conversation.
        """
        return self.participants.count()
    
    @property
    def unread_count(self, user):
        """
        Renvoie le nombre de messages non lus pour un utilisateur.
        """
        try:
            participant = ConversationParticipant.objects.get(conversation=self, user=user)
            return self.messages.filter(created_at__gt=participant.last_read_at).count()
        except ConversationParticipant.DoesNotExist:
            return 0


class ConversationParticipant(models.Model):
    """
    Modèle représentant un participant à une conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('conversation')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        verbose_name=_('utilisateur')
    )
    
    # Paramètres du participant
    is_admin = models.BooleanField(_('est administrateur'), default=False)
    is_muted = models.BooleanField(_('est muet'), default=False)
    
    # Paramètres de notification
    notify_on_new_message = models.BooleanField(_('notifier sur nouveau message'), default=True)
    
    # Suivi de la lecture
    joined_at = models.DateTimeField(_('rejoint le'), auto_now_add=True)
    last_read_at = models.DateTimeField(_('dernier lu le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('participant de conversation')
        verbose_name_plural = _('participants de conversation')
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} dans {self.conversation}"
    
    def mark_as_read(self):
        """
        Marque la conversation comme lue pour ce participant.
        """
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])
    
    def has_unread_messages(self):
        """
        Vérifie si le participant a des messages non lus.
        """
        return self.conversation.messages.filter(created_at__gt=self.last_read_at).exists()


class Message(models.Model):
    """
    Modèle représentant un message dans une conversation.
    """
    MESSAGE_TYPE_CHOICES = (
        ('text', _('Texte')),
        ('image', _('Image')),
        ('file', _('Fichier')),
        ('audio', _('Audio')),
        ('video', _('Vidéo')),
        ('location', _('Localisation')),
        ('system', _('Système')),
    )
    
    # Relations
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,  # Pour les messages système
        related_name='sent_messages',
        verbose_name=_('expéditeur')
    )
    
    # Contenu
    message_type = models.CharField(_('type de message'), max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField(_('contenu'), blank=True)
    
    # Pour les messages avec média
    image = models.ImageField(_('image'), upload_to='message_images/', blank=True, null=True)
    file = models.FileField(_('fichier'), upload_to='message_files/', blank=True, null=True)
    file_name = models.CharField(_('nom du fichier'), max_length=255, blank=True)
    file_size = models.PositiveIntegerField(_('taille du fichier'), null=True, blank=True)
    
    # Pour les messages audio/vidéo
    media_duration = models.PositiveIntegerField(_('durée du média'), null=True, blank=True)
    
    # Pour les messages de localisation
    latitude = models.FloatField(_('latitude'), null=True, blank=True)
    longitude = models.FloatField(_('longitude'), null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_edited = models.BooleanField(_('est édité'), default=False)
    
    # Statut de réception
    is_delivered = models.BooleanField(_('est délivré'), default=False)
    delivered_at = models.DateTimeField(_('délivré le'), null=True, blank=True)
    
    # Message parent (pour les réponses)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('message parent')
    )
    
    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
    
    def __str__(self):
        if self.message_type == 'text':
            preview = self.content[:50] + ('...' if len(self.content) > 50 else '')
            return f"{self.sender.get_full_name() if self.sender else 'Système'}: {preview}"
        return f"Message {self.get_message_type_display()} de {self.sender.get_full_name() if self.sender else 'Système'}"
    
    def save(self, *args, **kwargs):
        # Mettre à jour la date du dernier message dans la conversation
        is_new = self.pk is None
        
        # Enregistrer le message
        super().save(*args, **kwargs)
        
        # Mettre à jour la conversation
        if is_new:
            self.conversation.update_last_message_time()
    
    def mark_as_delivered(self):
        """
        Marque le message comme délivré.
        """
        self.is_delivered = True
        self.delivered_at = timezone.now()
        self.save(update_fields=['is_delivered', 'delivered_at'])
    
    def edit(self, new_content):
        """
        Modifie le contenu du message (uniquement pour les messages texte).
        """
        if self.message_type == 'text':
            self.content = new_content
            self.is_edited = True
            self.updated_at = timezone.now()
            self.save(update_fields=['content', 'is_edited', 'updated_at'])
    
    @property
    def is_system_message(self):
        """
        Indique s'il s'agit d'un message système.
        """
        return self.message_type == 'system' or self.sender is None
    
    @property
    def has_media(self):
        """
        Indique si le message contient un média.
        """
        return self.message_type in ['image', 'file', 'audio', 'video']


class MessageReaction(models.Model):
    """
    Modèle représentant une réaction à un message.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('message')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions',
        verbose_name=_('utilisateur')
    )
    reaction = models.CharField(_('réaction'), max_length=50)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('réaction à un message')
        verbose_name_plural = _('réactions aux messages')
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} a réagi '{self.reaction}' au message de {self.message.sender.get_full_name() if self.message.sender else 'Système'}"


class MessageRead(models.Model):
    """
    Modèle représentant la lecture d'un message par un utilisateur.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reads',
        verbose_name=_('message')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reads',
        verbose_name=_('utilisateur')
    )
    read_at = models.DateTimeField(_('lu le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('lecture de message')
        verbose_name_plural = _('lectures de messages')
        unique_together = ['message', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} a lu le message de {self.message.sender.get_full_name() if self.message.sender else 'Système'} à {self.read_at}"