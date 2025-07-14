# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm as AuthPasswordChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from .models import User, Student, Pupil, Teacher, Advisor, Administrator


class PasswordChangeForm(AuthPasswordChangeForm):
    """Formulaire personnalisé pour le changement de mot de passe."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class CustomUserCreationForm(UserCreationForm):
    """Formulaire pour la création d'un utilisateur avec email comme identifiant."""
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'type')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Cette adresse e-mail est déjà utilisée."))
        return email


class CustomUserChangeForm(UserChangeForm):
    """Formulaire pour la modification d'un utilisateur existant."""
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number',
                 'date_of_birth', 'profile_picture', 'address', 'city',
                 'postal_code', 'country', 'communication_preferences')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class StudentProfileForm(forms.ModelForm):
    """Formulaire pour le profil étudiant."""
    class Meta:
        model = Student
        fields = ('institution_name', 'current_level', 'major', 'academic_year',
                 'student_id', 'school_id', 'scholarship', 'scholarship_type',
                 'housing_needs', 'internship_search', 'computer_skills',
                 'extracurricular_activities', 'interests', 'average_grade')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['average_grade'].widget.attrs.update({'min': '0', 'max': '20', 'step': '0.1'})
        self.fields['housing_needs'].widget = forms.CheckboxSelectMultiple(choices=[
            ('residence', 'Résidence universitaire'),
            ('shared', 'Colocation'),
            ('studio', 'Studio'),
            ('family', 'Chez une famille')
        ])
        self.fields['computer_skills'].widget = forms.CheckboxSelectMultiple(choices=[
            ('office', 'Suite Office'),
            ('programming', 'Programmation'),
            ('graphic', 'Design graphique'),
            ('statistics', 'Logiciels statistiques'),
            ('video', 'Montage vidéo')
        ])


class PupilProfileForm(forms.ModelForm):
    """Formulaire pour le profil élève."""
    class Meta:
        model = Pupil
        fields = ('school_name', 'current_level', 'specialization',
                 'legal_guardian_name', 'legal_guardian_phone',
                 'second_guardian_name', 'second_guardian_phone',
                 'cafeteria', 'dietary_restrictions', 'school_transport',
                 'transport_details', 'medical_information',
                 'school_insurance', 'exit_permissions',
                 'siblings_at_school', 'desired_activities')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['dietary_restrictions'].widget = forms.CheckboxSelectMultiple(choices=[
            ('vegetarian', 'Végétarien'),
            ('vegan', 'Végan'),
            ('halal', 'Halal'),
            ('kosher', 'Kosher'),
            ('allergies', 'Allergies alimentaires')
        ])
        self.fields['desired_activities'].widget = forms.CheckboxSelectMultiple(choices=[
            ('sports', 'Sports'),
            ('music', 'Musique'),
            ('theater', 'Théâtre'),
            ('art', 'Arts plastiques'),
            ('science', 'Club scientifique')
        ])


class TeacherProfileForm(forms.ModelForm):
    """Formulaire pour le profil enseignant."""
    class Meta:
        model = Teacher
        fields = ('institution_name', 'subjects', 'years_of_experience',
                 'highest_degree', 'degree_document', 'qualifications',
                 'professional_license', 'teaching_type', 'expertise_areas',
                 'cv', 'availability', 'professional_references',
                 'continuous_education')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['teaching_type'].widget = forms.CheckboxSelectMultiple(choices=[
            ('in_person', 'Présentiel'),
            ('online', 'En ligne'),
            ('hybrid', 'Hybride')
        ])
        self.fields['expertise_areas'].widget = forms.CheckboxSelectMultiple(choices=[
            ('stem', 'STEM'),
            ('humanities', 'Humanités'),
            ('arts', 'Arts'),
            ('languages', 'Langues'),
            ('vocational', 'Professionnel')
        ])


class AdvisorProfileForm(forms.ModelForm):
    """Formulaire pour le profil conseiller."""
    class Meta:
        model = Advisor
        fields = ('organization', 'specialization', 'years_of_experience',
                 'professional_license', 'certifications',
                 'certification_documents', 'geographical_areas', 'rates',
                 'portfolio', 'portfolio_link', 'publications', 'availability')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        self.fields['specialization'].widget = forms.Select(choices=[
            ('academic', 'Orientation scolaire'),
            ('career', 'Orientation professionnelle'),
            ('psychology', 'Psychologie'),
            ('counseling', 'Conseil')
        ])
        self.fields['geographical_areas'].widget = forms.CheckboxSelectMultiple(choices=[
            ('local', 'Local'),
            ('regional', 'Régional'),
            ('national', 'National'),
            ('international', 'International')
        ])


class AdministratorProfileForm(forms.ModelForm):
    """Formulaire pour le profil administrateur."""
    class Meta:
        model = Administrator
        fields = ('role', 'department', 'administrative_level', 'responsibilities')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class PasswordResetRequestForm(forms.Form):
    """Formulaire pour la demande de réinitialisation de mot de passe."""
    email = forms.EmailField(
        label=_("Adresse e-mail"),
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )


class SetPasswordForm(forms.Form):
    """Formulaire pour définir un nouveau mot de passe."""
    new_password1 = forms.CharField(
        label=_("Nouveau mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("Confirmation du nouveau mot de passe"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Les deux mots de passe ne correspondent pas."))
        validate_password(password2)
        return password2


class RegistrationForm(UserCreationForm):
    """Formulaire complet d'inscription avec champs conditionnels."""
    # Informations de base
    email = forms.EmailField(label=_("Adresse e-mail"), widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label=_("Prénom"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label=_("Nom"), widget=forms.TextInput(attrs={'class': 'form-control'}))
    type = forms.ChoiceField(
        label=_("Type d'utilisateur"),
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'user-type-select'})
    )
    
    # Champs optionnels communs
    phone_number = forms.CharField(label=_("Téléphone"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_of_birth = forms.DateField(label=_("Date de naissance"), required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    address = forms.CharField(label=_("Adresse"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(label=_("Ville"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal_code = forms.CharField(label=_("Code postal"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    country = forms.CharField(label=_("Pays"), required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    # Consentements
    data_processing_consent = forms.BooleanField(
        label=_("Je consens au traitement de mes données personnelles"),
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    image_rights_consent = forms.BooleanField(
        label=_("J'autorise l'utilisation de mon image"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.address = self.cleaned_data['address']
        user.city = self.cleaned_data['city']
        user.postal_code = self.cleaned_data['postal_code']
        user.country = self.cleaned_data['country']
        user.data_processing_consent = self.cleaned_data['data_processing_consent']
        user.image_rights_consent = self.cleaned_data['image_rights_consent']
        user.verification_status = 'unverified'
        
        if commit:
            user.save()
            
            # Création du profil spécifique
            if user.type == 'student':
                Student.objects.create(user=user)
            elif user.type == 'pupil':
                Pupil.objects.create(user=user)
            elif user.type == 'teacher':
                Teacher.objects.create(user=user)
            elif user.type == 'advisor':
                Advisor.objects.create(user=user)
            elif user.type == 'administrator':
                Administrator.objects.create(user=user)
        
        return user


class LoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé."""
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        label=_("Mot de passe"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = _("Email")