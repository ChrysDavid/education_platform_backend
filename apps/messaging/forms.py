from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import Conversation, ConversationParticipant, Message, MessageReaction, MessageRead

User = get_user_model()


class ConversationForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une conversation.
    """
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Conversation
        fields = ['title', 'conversation_type', 'is_group', 'group_avatar', 'group_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'conversation_type': forms.Select(attrs={'class': 'form-select'}),
            'is_group': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'group_avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'group_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si c'est une mise à jour, initialiser les participants
        if self.instance.pk:
            self.fields['participants'].initial = User.objects.filter(
                conversations__conversation=self.instance
            )
    
    def clean(self):
        cleaned_data = super().clean()
        conversation_type = cleaned_data.get('conversation_type')
        is_group = cleaned_data.get('is_group')
        title = cleaned_data.get('title')
        participants = cleaned_data.get('participants', [])
        
        # Vérifier que le titre est fourni pour les groupes
        if is_group and not title:
            self.add_error('title', _("Un titre est requis pour les conversations de groupe."))
        
        # Vérifier qu'il y a au moins un participant (en plus de l'utilisateur actuel)
        if not participants:
            self.add_error('participants', _("Veuillez sélectionner au moins un participant."))
        
        # Pour les messages directs, limiter à un seul participant
        if conversation_type == 'direct' and len(participants) > 1:
            self.add_error('participants', _("Les messages directs ne peuvent avoir qu'un seul destinataire."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir le créateur
        if not instance.pk and self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
            
            # Gérer les participants
            if 'participants' in self.cleaned_data:
                # Ajouter le créateur comme participant et admin
                if self.user:
                    instance.add_participant(self.user, is_admin=True)
                
                # Ajouter les autres participants
                for participant in self.cleaned_data['participants']:
                    if participant != self.user:
                        instance.add_participant(participant)
        
        return instance


class DirectMessageForm(forms.Form):
    """
    Formulaire pour envoyer un message direct à un utilisateur.
    """
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        label=_("Destinataire"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_recipient(self):
        recipient = self.cleaned_data['recipient']
        
        # Vérifier que le destinataire n'est pas l'expéditeur
        if recipient == self.user:
            raise forms.ValidationError(_("Vous ne pouvez pas vous envoyer un message à vous-même."))
        
        return recipient
    
    def save(self):
        """
        Crée une conversation directe et envoie le message.
        """
        recipient = self.cleaned_data['recipient']
        message_content = self.cleaned_data['message']
        
        # Vérifier s'il existe déjà une conversation directe entre ces utilisateurs
        existing_conversations = Conversation.objects.filter(
            conversation_type='direct',
            participants__user=self.user
        ).filter(
            participants__user=recipient
        ).distinct()
        
        if existing_conversations.exists():
            conversation = existing_conversations.first()
        else:
            # Créer une nouvelle conversation
            conversation = Conversation.objects.create(
                conversation_type='direct',
                created_by=self.user
            )
            
            # Ajouter les participants
            conversation.add_participant(self.user)
            conversation.add_participant(recipient)
        
        # Créer le message
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            message_type='text',
            content=message_content
        )
        
        return conversation, message


class MessageForm(forms.ModelForm):
    """
    Formulaire pour envoyer un message dans une conversation.
    """
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'image', 'file', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Votre message...')}),
            'message_type': forms.HiddenInput(),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'parent': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.conversation = kwargs.pop('conversation', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Masquer certains champs par défaut
        self.fields['image'].widget = forms.FileInput(attrs={'class': 'form-control d-none', 'accept': 'image/*'})
        self.fields['file'].widget = forms.FileInput(attrs={'class': 'form-control d-none'})
    
    def clean(self):
        cleaned_data = super().clean()
        message_type = cleaned_data.get('message_type', 'text')
        content = cleaned_data.get('content', '')
        image = cleaned_data.get('image')
        file = cleaned_data.get('file')
        
        # Vérifier que le contenu est fourni pour les messages texte
        if message_type == 'text' and not content:
            self.add_error('content', _("Le contenu est requis pour les messages texte."))
        
        # Vérifier qu'une image est fournie pour les messages image
        if message_type == 'image' and not image:
            self.add_error('image', _("Une image est requise pour les messages image."))
        
        # Vérifier qu'un fichier est fourni pour les messages fichier
        if message_type == 'file' and not file:
            self.add_error('file', _("Un fichier est requis pour les messages fichier."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir la conversation et l'expéditeur
        if self.conversation:
            instance.conversation = self.conversation
        
        if self.user:
            instance.sender = self.user
        
        # Déterminer le type de message si non spécifié
        if not instance.message_type:
            if instance.image:
                instance.message_type = 'image'
            elif instance.file:
                instance.message_type = 'file'
            else:
                instance.message_type = 'text'
        
        # Extraire les métadonnées du fichier si nécessaire
        if instance.file:
            instance.file_name = instance.file.name
            instance.file_size = instance.file.size
        
        if commit:
            instance.save()
            
            # Mettre à jour la date de dernier message dans la conversation
            instance.conversation.update_last_message_time()
            
            # Marquer le message comme lu par l'expéditeur
            if self.user:
                MessageRead.objects.create(message=instance, user=self.user)
                
                # Mettre à jour la date de dernière lecture pour l'expéditeur
                participant = ConversationParticipant.objects.get(
                    conversation=instance.conversation,
                    user=self.user
                )
                participant.mark_as_read()
        
        return instance


class MessageReactionForm(forms.ModelForm):
    """
    Formulaire pour ajouter une réaction à un message.
    """
    class Meta:
        model = MessageReaction
        fields = ['reaction']
        widgets = {
            'reaction': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.message = kwargs.pop('message', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_reaction(self):
        reaction = self.cleaned_data['reaction']
        
        # Vérifier si l'utilisateur a déjà réagi avec cette réaction
        if MessageReaction.objects.filter(message=self.message, user=self.user, reaction=reaction).exists():
            raise forms.ValidationError(_("Vous avez déjà ajouté cette réaction."))
        
        return reaction
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.message:
            instance.message = self.message
        
        if self.user:
            instance.user = self.user
        
        if commit:
            instance.save()
        
        return instance


class ConversationParticipantForm(forms.ModelForm):
    """
    Formulaire pour modifier les paramètres d'un participant à une conversation.
    """
    class Meta:
        model = ConversationParticipant
        fields = ['is_admin', 'is_muted', 'notify_on_new_message']
        widgets = {
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_muted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_on_new_message': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }