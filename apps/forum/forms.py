from datetime import timezone
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import (
    Category, Topic, Post, PostReaction, 
    TopicSubscription, PostReport
)

User = get_user_model()


class CategoryForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une catégorie.
    """
    class Meta:
        model = Category
        fields = [
            'name', 'description', 'icon', 'color', 'order', 
            'is_active', 'requires_verification', 'authorized_groups'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_verification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'authorized_groups': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }


class TopicForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un sujet.
    """
    content = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        help_text=_('Le contenu du premier message du sujet')
    )
    
    tags_input = forms.CharField(
        label=_('Tags'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Séparés par des virgules')}),
        help_text=_('Entrez des tags séparés par des virgules (ex: question, aide, projet)')
    )
    
    class Meta:
        model = Topic
        fields = ['category', 'title']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        
        # Si une catégorie est fournie, la définir comme valeur par défaut
        if self.category:
            self.fields['category'].initial = self.category
            self.fields['category'].widget = forms.HiddenInput()
        
        # Filtrer les catégories actives uniquement
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        
        # Préremplir les tags si on modifie un sujet existant
        if self.instance.pk and hasattr(self.instance, 'tags'):
            self.fields['tags_input'].initial = ', '.join(self.instance.tags)
    
    def clean_tags_input(self):
        """
        Convertit la chaîne de tags en liste.
        """
        tags_input = self.cleaned_data.get('tags_input', '')
        if tags_input:
            # Diviser par les virgules et nettoyer les espaces
            return [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        return []
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier les permissions pour la catégorie
        category = cleaned_data.get('category')
        
        if category and self.user:
            # Vérifier si la catégorie nécessite une vérification
            if category.requires_verification and not hasattr(self.user, 'verification_status'):
                self.add_error('category', _("Vous devez être vérifié pour créer un sujet dans cette catégorie."))
            elif category.requires_verification and self.user.verification_status != 'verified':
                self.add_error('category', _("Vous devez être vérifié pour créer un sujet dans cette catégorie."))
            
            # Vérifier si la catégorie est restreinte à certains groupes
            if category.authorized_groups.exists():
                user_groups = self.user.groups.all()
                if not any(group in user_groups for group in category.authorized_groups.all()):
                    self.add_error('category', _("Vous n'avez pas les permissions nécessaires pour créer un sujet dans cette catégorie."))
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Enregistre le sujet et crée le premier message.
        """
        instance = super().save(commit=False)
        
        # Définir l'auteur si fourni
        if self.user and not instance.author:
            instance.author = self.user
        
        # Définir les tags
        instance.tags = self.cleaned_data.get('tags_input', [])
        
        if commit:
            instance.save()
            
            # Créer le premier message
            post_content = self.cleaned_data.get('content')
            if post_content:
                Post.objects.create(
                    topic=instance,
                    author=instance.author,
                    content=post_content
                )
                
                # Abonner automatiquement l'auteur au sujet
                TopicSubscription.objects.get_or_create(
                    topic=instance,
                    user=instance.author
                )
        
        return instance


class PostForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un message.
    """
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier si le sujet est fermé
        if self.topic and self.topic.is_closed:
            raise forms.ValidationError(_("Vous ne pouvez pas répondre à un sujet fermé."))
        
        # Vérifier les permissions de la catégorie
        if self.topic and self.user:
            category = self.topic.category
            
            # Vérifier si la catégorie nécessite une vérification
            if category.requires_verification and not hasattr(self.user, 'verification_status'):
                raise forms.ValidationError(_("Vous devez être vérifié pour répondre dans cette catégorie."))
            elif category.requires_verification and self.user.verification_status != 'verified':
                raise forms.ValidationError(_("Vous devez être vérifié pour répondre dans cette catégorie."))
            
            # Vérifier si la catégorie est restreinte à certains groupes
            if category.authorized_groups.exists():
                user_groups = self.user.groups.all()
                if not any(group in user_groups for group in category.authorized_groups.all()):
                    raise forms.ValidationError(_("Vous n'avez pas les permissions nécessaires pour répondre dans cette catégorie."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir l'auteur et le sujet si fournis
        if self.user:
            instance.author = self.user
        
        if self.topic:
            instance.topic = self.topic
        
        if commit:
            instance.save()
            
            # Abonner automatiquement l'auteur au sujet s'il ne l'est pas déjà
            if self.user:
                TopicSubscription.objects.get_or_create(
                    topic=instance.topic,
                    user=self.user
                )
                
                # Marquer le sujet comme vu par l'utilisateur
                from .models import TopicView
                TopicView.objects.update_or_create(
                    topic=instance.topic,
                    user=self.user,
                    defaults={'viewed_at': timezone.now()}
                )
        
        return instance


class TopicSubscriptionForm(forms.ModelForm):
    """
    Formulaire pour gérer les abonnements à un sujet.
    """
    class Meta:
        model = TopicSubscription
        fields = ['notify_on_new_post']
        widgets = {
            'notify_on_new_post': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PostReportForm(forms.ModelForm):
    """
    Formulaire pour signaler un message inapproprié.
    """
    class Meta:
        model = PostReport
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Expliquez pourquoi ce message vous semble inapproprié...')}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.post = kwargs.pop('post', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.reporter = self.user
        
        if self.post:
            instance.post = self.post
        
        if commit:
            instance.save()
        
        return instance


class PostReactionForm(forms.ModelForm):
    """
    Formulaire pour réagir à un message.
    """
    class Meta:
        model = PostReaction
        fields = ['reaction']
        widgets = {
            'reaction': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.post = kwargs.pop('post', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        
        if self.post:
            instance.post = self.post
        
        if commit:
            instance.save()
        
        return instance


class TopicModerationForm(forms.Form):
    """
    Formulaire pour les actions de modération sur un sujet.
    """
    ACTION_CHOICES = (
        ('close', _('Fermer le sujet')),
        ('open', _('Rouvrir le sujet')),
        ('pin', _('Épingler le sujet')),
        ('unpin', _('Désépingler le sujet')),
        ('hide', _('Masquer le sujet')),
        ('unhide', _('Afficher le sujet')),
        ('move', _('Déplacer vers une autre catégorie')),
    )
    
    action = forms.ChoiceField(
        label=_('Action'),
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    target_category = forms.ModelChoiceField(
        label=_('Catégorie cible'),
        queryset=Category.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    moderator_note = forms.CharField(
        label=_('Note de modération'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        target_category = cleaned_data.get('target_category')
        
        if action == 'move' and not target_category:
            self.add_error('target_category', _('Vous devez sélectionner une catégorie cible pour déplacer le sujet.'))
        
        return cleaned_data


class PostModerationForm(forms.Form):
    """
    Formulaire pour les actions de modération sur un message.
    """
    ACTION_CHOICES = (
        ('hide', _('Masquer le message')),
        ('unhide', _('Afficher le message')),
        ('mark_solution', _('Marquer comme solution')),
        ('unmark_solution', _('Retirer comme solution')),
    )
    
    action = forms.ChoiceField(
        label=_('Action'),
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    moderator_note = forms.CharField(
        label=_('Note de modération'),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )