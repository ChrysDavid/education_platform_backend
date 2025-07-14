from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    ResourceCategory, Resource, ResourceReview, 
    ResourceComment, ResourceCollection
)


class ResourceCategoryForm(forms.ModelForm):
    """
    Formulaire pour les catégories de ressources.
    """
    class Meta:
        model = ResourceCategory
        fields = ['name', 'description', 'icon', 'parent', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ResourceForm(forms.ModelForm):
    """
    Formulaire pour les ressources pédagogiques.
    """
    class Meta:
        model = Resource
        exclude = ['slug', 'created_by', 'view_count', 'download_count', 'like_count', 'created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resource_type': forms.Select(attrs={'class': 'form-select'}),
            'access_level': forms.Select(attrs={'class': 'form-select'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'external_url': forms.URLInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Séparés par des virgules'}),
            'language': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'author_name': forms.TextInput(attrs={'class': 'form-control'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'license': forms.TextInput(attrs={'class': 'form-control'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Conversion du champ tags en chaîne pour l'affichage dans le formulaire
        if self.instance.pk and isinstance(self.instance.tags, list):
            self.initial['tags'] = ', '.join(self.instance.tags)
    
    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        file = cleaned_data.get('file')
        external_url = cleaned_data.get('external_url')
        
        # Vérifier que soit le fichier soit l'URL externe est fourni
        if resource_type != 'link' and not file and not self.instance.file:
            if resource_type in ['document', 'image', 'video', 'audio']:
                self.add_error('file', _('Un fichier est requis pour ce type de ressource.'))
        
        if resource_type == 'link' and not external_url:
            self.add_error('external_url', _('Une URL externe est requise pour une ressource de type lien.'))
        
        # Convertir les tags en liste
        tags = cleaned_data.get('tags', '')
        if isinstance(tags, str):
            cleaned_data['tags'] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Assignation de l'utilisateur créateur
        if self.user and not instance.pk:
            instance.created_by = self.user
        
        # Enregistrement de l'instance
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class ResourceReviewForm(forms.ModelForm):
    """
    Formulaire pour les évaluations de ressources.
    """
    class Meta:
        model = ResourceReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier si l'utilisateur a déjà évalué cette ressource (si c'est une nouvelle évaluation)
        if not self.instance.pk and self.user and self.resource:
            if ResourceReview.objects.filter(resource=self.resource, user=self.user).exists():
                raise forms.ValidationError(_("Vous avez déjà évalué cette ressource."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        if self.resource:
            instance.resource = self.resource
        
        if commit:
            instance.save()
        
        return instance


class ResourceCommentForm(forms.ModelForm):
    """
    Formulaire pour les commentaires sur les ressources.
    """
    class Meta:
        model = ResourceComment
        fields = ['content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.user = self.user
        if self.resource:
            instance.resource = self.resource
        
        if commit:
            instance.save()
        
        return instance


class ResourceCollectionForm(forms.ModelForm):
    """
    Formulaire pour les collections de ressources.
    """
    class Meta:
        model = ResourceCollection
        fields = ['title', 'description', 'cover_image', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user and not instance.pk:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class ResourceSearchForm(forms.Form):
    """
    Formulaire pour la recherche de ressources.
    """
    search = forms.CharField(
        label=_("Rechercher"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Titre, description...")})
    )
    
    categories = forms.ModelMultipleChoiceField(
        label=_("Catégories"),
        queryset=ResourceCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'})
    )
    
    resource_type = forms.ChoiceField(
        label=_("Type de ressource"),
        choices=[('', '---')] + list(Resource.TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    language = forms.CharField(
        label=_("Langue"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    min_rating = forms.ChoiceField(
        label=_("Note minimale"),
        choices=[('', '---')] + [(str(i), str(i)) for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_approved = forms.BooleanField(
        label=_("Ressources approuvées uniquement"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    sort_by = forms.ChoiceField(
        label=_("Trier par"),
        choices=[
            ('created_at', _('Date (récentes d\'abord)')),
            ('-created_at', _('Date (anciennes d\'abord)')),
            ('title', _('Titre (A-Z)')),
            ('-title', _('Titre (Z-A)')),
            ('view_count', _('Nombre de vues')),
            ('like_count', _('Nombre de j\'aime')),
        ],
        required=False,
        initial='created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )