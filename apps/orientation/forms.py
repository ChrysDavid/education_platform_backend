from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import (
    AssessmentType, AssessmentQuestion, Assessment, AssessmentAnswer,
    SkillCategory, Skill, CareerField, CareerPath, OrientationPath,
    OrientationCareerPath, StudentSkill
)


class AssessmentTypeForm(forms.ModelForm):
    """
    Formulaire pour les types d'évaluation d'orientation.
    """
    class Meta:
        model = AssessmentType
        fields = ['name', 'description', 'max_score', 'passing_score', 'time_limit_minutes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        max_score = cleaned_data.get('max_score')
        passing_score = cleaned_data.get('passing_score')
        
        if max_score and passing_score and passing_score > max_score:
            self.add_error('passing_score', _('Le score de validation ne peut pas être supérieur au score maximal.'))
        
        return cleaned_data


class AssessmentQuestionForm(forms.ModelForm):
    """
    Formulaire pour les questions d'évaluation.
    """
    class Meta:
        model = AssessmentQuestion
        fields = [
            'assessment_type', 'text', 'question_type', 'required',
            'order', 'points', 'options', 'scale_min', 'scale_max', 'scale_step',
            'is_active'
        ]
        widgets = {
            'assessment_type': forms.Select(attrs={'class': 'form-select'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'scale_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'scale_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'scale_step': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Les champs qui dépendent du type de question
        self.fields['options'].widget = forms.HiddenInput()
        self.fields['scale_min'].widget = forms.HiddenInput()
        self.fields['scale_max'].widget = forms.HiddenInput()
        self.fields['scale_step'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        
        if question_type in ['single_choice', 'multiple_choice']:
            options = cleaned_data.get('options', {})
            if not isinstance(options, dict) or not options.get('choices'):
                self.add_error('options', _('Veuillez spécifier les options de réponse.'))
        
        if question_type == 'scale':
            scale_min = cleaned_data.get('scale_min')
            scale_max = cleaned_data.get('scale_max')
            scale_step = cleaned_data.get('scale_step')
            
            if scale_min is None or scale_max is None:
                self.add_error('scale_min', _('Les valeurs minimale et maximale sont requises pour une échelle.'))
            elif scale_min >= scale_max:
                self.add_error('scale_min', _('La valeur minimale doit être inférieure à la valeur maximale.'))
            
            if scale_step is None or scale_step <= 0:
                self.add_error('scale_step', _('Le pas doit être un nombre positif.'))
        
        return cleaned_data


class AssessmentForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une session d'évaluation.
    """
    class Meta:
        model = Assessment
        fields = ['student', 'advisor', 'assessment_type', 'status', 'advisor_notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'advisor': forms.Select(attrs={'class': 'form-select'}),
            'assessment_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'advisor_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'utilisateur est un conseiller, préselectionner son compte
        if self.request_user and hasattr(self.request_user, 'advisor_profile'):
            self.fields['advisor'].initial = self.request_user
        
        # Filtrer les étudiants actifs uniquement
        from django.db.models import Q
        self.fields['student'].queryset = self.fields['student'].queryset.filter(
            Q(type='student') & Q(is_active=True)
        )
        
        # Filtrer les conseillers actifs uniquement
        self.fields['advisor'].queryset = self.fields['advisor'].queryset.filter(
            Q(type='advisor') & Q(is_active=True)
        )


class AssessmentAnswerForm(forms.ModelForm):
    """
    Formulaire pour répondre à une question d'évaluation.
    """
    class Meta:
        model = AssessmentAnswer
        fields = ['assessment', 'question', 'answer_data']
    
    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        # Masquer les champs qui seront définis automatiquement
        self.fields['assessment'].widget = forms.HiddenInput()
        self.fields['question'].widget = forms.HiddenInput()
        
        # Si une question est fournie, la définir comme valeur par défaut
        if self.question:
            self.fields['question'].initial = self.question
        
        # Le champ answer_data sera personnalisé selon le type de question
        self.fields['answer_data'].widget = forms.HiddenInput()


class SkillCategoryForm(forms.ModelForm):
    """
    Formulaire pour les catégories de compétences.
    """
    class Meta:
        model = SkillCategory
        fields = ['name', 'description', 'icon', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SkillForm(forms.ModelForm):
    """
    Formulaire pour les compétences.
    """
    class Meta:
        model = Skill
        fields = ['name', 'description', 'category', 'level', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer uniquement les catégories actives
        self.fields['category'].queryset = SkillCategory.objects.filter(is_active=True)


class CareerFieldForm(forms.ModelForm):
    """
    Formulaire pour les domaines professionnels.
    """
    class Meta:
        model = CareerField
        fields = ['name', 'description', 'icon', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CareerPathForm(forms.ModelForm):
    """
    Formulaire pour les filières professionnelles.
    """
    class Meta:
        model = CareerPath
        fields = [
            'name', 'description', 'field', 'average_salary', 'job_prospects',
            'education_requirements', 'skills_required', 'content', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'field': forms.Select(attrs={'class': 'form-select'}),
            'average_salary': forms.TextInput(attrs={'class': 'form-control'}),
            'job_prospects': forms.TextInput(attrs={'class': 'form-control'}),
            'education_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'skills_required': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer uniquement les domaines actifs
        self.fields['field'].queryset = CareerField.objects.filter(is_active=True)
        
        # Filtrer uniquement les compétences actives
        self.fields['skills_required'].queryset = Skill.objects.filter(is_active=True)
        
        # Le champ content est un champ JSON géré par JavaScript
        self.fields['content'].widget = forms.HiddenInput()


class OrientationPathForm(forms.ModelForm):
    """
    Formulaire pour les parcours d'orientation.
    """
    class Meta:
        model = OrientationPath
        fields = [
            'student', 'advisor', 'title', 'description', 'assessments',
            'steps', 'resources', 'milestones', 'status', 'start_date',
            'target_end_date', 'advisor_notes'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'advisor': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assessments': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'advisor_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'utilisateur est un conseiller, préselectionner son compte
        if self.request_user and hasattr(self.request_user, 'advisor_profile'):
            self.fields['advisor'].initial = self.request_user
        
        # Filtrer les étudiants actifs uniquement
        from django.db.models import Q
        self.fields['student'].queryset = self.fields['student'].queryset.filter(
            Q(type='student') & Q(is_active=True)
        )
        
        # Filtrer les conseillers actifs uniquement
        self.fields['advisor'].queryset = self.fields['advisor'].queryset.filter(
            Q(type='advisor') & Q(is_active=True)
        )
        
        # Filtrer les évaluations selon l'étudiant (si défini)
        if self.instance and self.instance.student_id:
            self.fields['assessments'].queryset = Assessment.objects.filter(
                student=self.instance.student, status='completed'
            )
        else:
            # Masquer le champ évaluations s'il n'y a pas d'étudiant défini
            self.fields['assessments'].widget = forms.HiddenInput()
        
        # Les champs JSON sont gérés par JavaScript
        self.fields['steps'].widget = forms.HiddenInput()
        self.fields['resources'].widget = forms.HiddenInput()
        self.fields['milestones'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        target_end_date = cleaned_data.get('target_end_date')
        
        if start_date and target_end_date and target_end_date < start_date:
            self.add_error('target_end_date', _('La date de fin prévue ne peut pas être antérieure à la date de début.'))
        
        return cleaned_data


class OrientationCareerPathForm(forms.ModelForm):
    """
    Formulaire pour associer des filières professionnelles à un parcours d'orientation.
    """
    class Meta:
        model = OrientationCareerPath
        fields = ['orientation_path', 'career_path', 'compatibility_score', 'recommendation_reason', 'is_primary']
        widgets = {
            'orientation_path': forms.HiddenInput(),
            'career_path': forms.Select(attrs={'class': 'form-select'}),
            'compatibility_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'recommendation_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.orientation_path = kwargs.pop('orientation_path', None)
        super().__init__(*args, **kwargs)
        
        if self.orientation_path:
            self.fields['orientation_path'].initial = self.orientation_path
        
        # Filtrer uniquement les filières actives
        self.fields['career_path'].queryset = CareerPath.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        orientation_path = cleaned_data.get('orientation_path')
        career_path = cleaned_data.get('career_path')
        is_primary = cleaned_data.get('is_primary')
        
        # Vérifier si cette filière est déjà associée à ce parcours
        if orientation_path and career_path and not self.instance.pk:
            if OrientationCareerPath.objects.filter(orientation_path=orientation_path, career_path=career_path).exists():
                self.add_error('career_path', _('Cette filière est déjà associée à ce parcours d\'orientation.'))
        
        # Vérifier si on essaie de définir une autre filière principale alors qu'il en existe déjà une
        if is_primary and orientation_path and not self.instance.pk:
            if OrientationCareerPath.objects.filter(orientation_path=orientation_path, is_primary=True).exists():
                self.add_error('is_primary', _('Il existe déjà une filière principale pour ce parcours.'))
        
        return cleaned_data


class StudentSkillForm(forms.ModelForm):
    """
    Formulaire pour les compétences d'un étudiant.
    """
    class Meta:
        model = StudentSkill
        fields = [
            'student', 'skill', 'proficiency_level', 'self_assessed',
            'advisor_assessed', 'assessment_derived', 'evidence', 'last_practiced'
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'proficiency_level': forms.Select(attrs={'class': 'form-select'}),
            'self_assessed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'advisor_assessed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'assessment_derived': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'last_practiced': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        self.student_user = kwargs.pop('student_user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'étudiant est fourni, le prédéfinir
        if self.student_user:
            self.fields['student'].initial = self.student_user
            self.fields['student'].widget = forms.HiddenInput()
        
        # Si l'utilisateur est un conseiller, marquer comme évalué par un conseiller
        if self.request_user and hasattr(self.request_user, 'advisor_profile'):
            self.fields['advisor_assessed'].initial = True
        elif self.request_user and hasattr(self.request_user, 'student_profile'):
            self.fields['self_assessed'].initial = True
        
        # Filtrer uniquement les compétences actives
        self.fields['skill'].queryset = Skill.objects.filter(is_active=True)
        
        # Filtrer uniquement les étudiants
        from django.db.models import Q
        self.fields['student'].queryset = self.fields['student'].queryset.filter(
            Q(type='student') & Q(is_active=True)
        )


class TakeAssessmentForm(forms.Form):
    """
    Formulaire pour répondre à une évaluation complète.
    """
    def __init__(self, *args, **kwargs):
        self.assessment = kwargs.pop('assessment', None)
        super().__init__(*args, **kwargs)
        
        if not self.assessment:
            return
        
        # Ajouter dynamiquement un champ pour chaque question de l'évaluation
        for question in AssessmentQuestion.objects.filter(
            assessment_type=self.assessment.assessment_type,
            is_active=True
        ).order_by('order'):
            field_name = f'question_{question.id}'
            
            if question.question_type == 'single_choice':
                choices = [(idx, text) for idx, text in enumerate(question.options.get('choices', []))]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                )
            
            elif question.question_type == 'multiple_choice':
                choices = [(idx, text) for idx, text in enumerate(question.options.get('choices', []))]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
                )
            
            elif question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.required,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                )
            
            elif question.question_type == 'numeric':
                self.fields[field_name] = forms.IntegerField(
                    label=question.text,
                    required=question.required,
                    widget=forms.NumberInput(attrs={'class': 'form-control'})
                )
            
            elif question.question_type == 'scale':
                min_val = question.scale_min or 1
                max_val = question.scale_max or 5
                step = question.scale_step or 1
                
                choices = [(val, str(val)) for val in range(min_val, max_val + 1, step)]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    choices=choices,
                    required=question.required,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                )
    
    def save(self):
        """
        Enregistre les réponses à l'évaluation.
        """
        if not self.assessment:
            return
        
        # Parcourir tous les champs du formulaire et enregistrer les réponses
        for field_name, value in self.cleaned_data.items():
            if not field_name.startswith('question_'):
                continue
            
            question_id = int(field_name.split('_')[1])
            question = AssessmentQuestion.objects.get(id=question_id)
            
            # Préparer les données de réponse en fonction du type de question
            answer_data = {}
            
            if question.question_type == 'single_choice':
                answer_data = {'selected_option': int(value)}
            elif question.question_type == 'multiple_choice':
                answer_data = {'selected_options': [int(v) for v in value]}
            elif question.question_type == 'text':
                answer_data = {'text': value}
            elif question.question_type == 'numeric':
                answer_data = {'value': value}
            elif question.question_type == 'scale':
                answer_data = {'value': int(value)}
            
            # Créer ou mettre à jour la réponse
            AssessmentAnswer.objects.update_or_create(
                assessment=self.assessment,
                question=question,
                defaults={'answer_data': answer_data}
            )
        
        # Marquer l'évaluation comme terminée
        self.assessment.complete()