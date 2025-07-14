from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import (
    SchoolType, City, School, Department, Program,
    Facility, SchoolContact, SchoolReview, SchoolMedia, SchoolEvent
)


class SchoolTypeForm(forms.ModelForm):
    """
    Formulaire pour les types d'établissements.
    """
    class Meta:
        model = SchoolType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CityForm(forms.ModelForm):
    """
    Formulaire pour les villes.
    """
    class Meta:
        model = City
        fields = ['name', 'region', 'zip_code', 'longitude', 'latitude', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolForm(forms.ModelForm):
    """
    Formulaire pour les établissements.
    """
    class Meta:
        model = School
        exclude = ['slug', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'school_type': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'accreditation': forms.TextInput(attrs={'class': 'form-control'}),
            'student_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'staff_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'director_name': forms.TextInput(attrs={'class': 'form-control'}),
            'admin_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'admin_contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'admin_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_founded_year(self):
        """Validation de l'année de fondation."""
        founded_year = self.cleaned_data.get('founded_year')
        if founded_year and founded_year > 2023:
            raise forms.ValidationError(_("L'année de fondation ne peut pas être dans le futur."))
        return founded_year


class DepartmentForm(forms.ModelForm):
    """
    Formulaire pour les départements.
    """
    class Meta:
        model = Department
        exclude = ['slug', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'head_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProgramForm(forms.ModelForm):
    """
    Formulaire pour les programmes académiques.
    """
    class Meta:
        model = Program
        exclude = ['slug', 'created_at', 'updated_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.TextInput(attrs={'class': 'form-control'}),
            'degree_awarded': forms.TextInput(attrs={'class': 'form-control'}),
            'admission_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'career_opportunities': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les départements en fonction de l'école si une école est sélectionnée
        if 'school' in self.data:
            try:
                school_id = int(self.data.get('school'))
                self.fields['department'].queryset = Department.objects.filter(school_id=school_id)
            except (ValueError, TypeError):
                pass
        # Si l'instance existe déjà (modification)
        elif self.instance.pk and self.instance.school:
            self.fields['department'].queryset = Department.objects.filter(school=self.instance.school)


class FacilityForm(forms.ModelForm):
    """
    Formulaire pour les équipements.
    """
    class Meta:
        model = Facility
        exclude = ['created_at']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolContactForm(forms.ModelForm):
    """
    Formulaire pour les contacts des établissements.
    """
    class Meta:
        model = SchoolContact
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_type': forms.Select(attrs={'class': 'form-select'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolReviewForm(forms.ModelForm):
    """
    Formulaire pour les évaluations des établissements.
    """
    class Meta:
        model = SchoolReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'step': '1'
            }),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.school = kwargs.pop('school', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        """Validation personnalisée pour vérifier si l'utilisateur a déjà évalué cette école."""
        cleaned_data = super().clean()
        
        # Si c'est un nouvel avis (pas une mise à jour)
        if not self.instance.pk and self.user and self.school:
            existing_review = SchoolReview.objects.filter(user=self.user, school=self.school).exists()
            if existing_review:
                raise forms.ValidationError(_("Vous avez déjà évalué cet établissement. Vous pouvez modifier votre évaluation existante."))
        
        return cleaned_data
    
    def save(self, commit=True):
        """Enregistre l'avis avec l'utilisateur et l'école associés."""
        review = super().save(commit=False)
        
        if self.user:
            review.user = self.user
        if self.school:
            review.school = self.school
        
        if commit:
            review.save()
        
        return review


class SchoolMediaForm(forms.ModelForm):
    """
    Formulaire pour les médias des établissements.
    """
    class Meta:
        model = SchoolMedia
        exclude = ['created_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SchoolEventForm(forms.ModelForm):
    """
    Formulaire pour les événements des établissements.
    """
    class Meta:
        model = SchoolEvent
        exclude = ['created_at', 'updated_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'school': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'registration_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        """Validation personnalisée pour vérifier les dates."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError(_("La date de fin ne peut pas être antérieure à la date de début."))
        
        return cleaned_data


class SchoolSearchForm(forms.Form):
    """
    Formulaire pour la recherche d'établissements.
    """
    search = forms.CharField(
        label=_("Rechercher"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Nom, ville, etc.")})
    )
    school_type = forms.ModelChoiceField(
        label=_("Type d'établissement"),
        queryset=SchoolType.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.ModelChoiceField(
        label=_("Ville"),
        queryset=City.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    has_facilities = forms.MultipleChoiceField(
        label=_("Équipements"),
        choices=Facility.FACILITY_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    min_rating = forms.ChoiceField(
        label=_("Note minimale"),
        choices=[('', '---')] + [(str(i), str(i)) for i in range(1, 6)],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    is_verified = forms.BooleanField(
        label=_("Établissements vérifiés uniquement"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )