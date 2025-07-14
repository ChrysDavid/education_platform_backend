# apps/orientation/models.py
from datetime import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
import uuid


class AssessmentType(models.Model):
    """
    Modèle représentant un type d'évaluation d'orientation.
    """
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'))
    
    # Configuration
    max_score = models.PositiveIntegerField(_('score maximal'), default=100)
    passing_score = models.PositiveIntegerField(_('score de validation'), default=50)
    time_limit_minutes = models.PositiveIntegerField(_('temps limite (minutes)'), null=True, blank=True)
    
    # États
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('type d\'évaluation')
        verbose_name_plural = _('types d\'évaluation')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_question_count(self):
        """Retourne le nombre de questions pour ce type d'évaluation."""
        return self.questions.count()


class AssessmentQuestion(models.Model):
    """
    Modèle représentant une question d'évaluation d'orientation.
    """
    QUESTION_TYPE_CHOICES = (
        ('single_choice', _('Choix unique')),
        ('multiple_choice', _('Choix multiple')),
        ('text', _('Texte')),
        ('numeric', _('Numérique')),
        ('scale', _('Échelle')),
    )
    
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('type d\'évaluation')
    )
    
    text = models.TextField(_('texte de la question'))
    question_type = models.CharField(_('type de question'), max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    # Configuration de la question
    required = models.BooleanField(_('obligatoire'), default=True)
    order = models.PositiveIntegerField(_('ordre'), default=0)
    points = models.PositiveIntegerField(_('points'), default=1)
    
    # Configuration supplémentaire selon le type
    options = models.JSONField(_('options'), default=dict, blank=True, 
                              help_text=_('Options pour les questions à choix'))
    scale_min = models.IntegerField(_('minimum de l\'échelle'), null=True, blank=True)
    scale_max = models.IntegerField(_('maximum de l\'échelle'), null=True, blank=True)
    scale_step = models.IntegerField(_('pas de l\'échelle'), null=True, blank=True, default=1)
    
    # États
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('question d\'évaluation')
        verbose_name_plural = _('questions d\'évaluation')
        ordering = ['assessment_type', 'order']
    
    def __str__(self):
        return f"{self.assessment_type.name} - {self.text[:50]}"
    
    def get_options(self):
        """Retourne les options de la question si c'est une question à choix."""
        if self.question_type in ['single_choice', 'multiple_choice']:
            return self.options.get('choices', [])
        return []


class Assessment(models.Model):
    """
    Modèle représentant une session d'évaluation d'orientation pour un étudiant.
    """
    STATUS_CHOICES = (
        ('pending', _('En attente')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('expired', _('Expiré')),
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name=_('étudiant')
    )
    
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_assessments',
        verbose_name=_('conseiller')
    )
    
    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name='assessments',
        verbose_name=_('type d\'évaluation')
    )
    
    uuid = models.UUIDField(_('identifiant unique'), default=uuid.uuid4, editable=False, unique=True)
    
    # État de l'évaluation
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    score = models.PositiveIntegerField(_('score'), null=True, blank=True)
    start_time = models.DateTimeField(_('heure de début'), null=True, blank=True)
    end_time = models.DateTimeField(_('heure de fin'), null=True, blank=True)
    time_spent_seconds = models.PositiveIntegerField(_('temps passé (secondes)'), null=True, blank=True)
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    # Paramètres personnalisés
    custom_parameters = models.JSONField(_('paramètres personnalisés'), default=dict, blank=True)
    
    # Résultats et commentaires
    results = models.JSONField(_('résultats'), default=dict, blank=True)
    advisor_notes = models.TextField(_('notes du conseiller'), blank=True)
    student_feedback = models.TextField(_('commentaires de l\'étudiant'), blank=True)
    
    class Meta:
        verbose_name = _('évaluation')
        verbose_name_plural = _('évaluations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.assessment_type.name} - {self.student.get_full_name()} ({self.get_status_display()})"
    
    def calculate_score(self):
        """Calcule le score total de l'évaluation."""
        total_points = 0
        earned_points = 0
        
        for answer in self.answers.all().select_related('question'):
            question = answer.question
            total_points += question.points
            
            if answer.is_correct():
                earned_points += question.points
        
        if total_points > 0:
            self.score = int((earned_points / total_points) * self.assessment_type.max_score)
        else:
            self.score = 0
        
        self.save(update_fields=['score'])
        return self.score
    
    def start(self):
        """Marque l'évaluation comme commencée."""
        from django.utils import timezone
        
        if self.status == 'pending':
            self.status = 'in_progress'
            self.start_time = timezone.now()
            self.save(update_fields=['status', 'start_time'])
    
    def complete(self):
        """Marque l'évaluation comme terminée."""
        from django.utils import timezone
        
        if self.status == 'in_progress':
            self.status = 'completed'
            self.end_time = timezone.now()
            
            # Calculer le temps passé
            if self.start_time:
                delta = self.end_time - self.start_time
                self.time_spent_seconds = delta.total_seconds()
            
            self.save(update_fields=['status', 'end_time', 'time_spent_seconds'])
            
            # Calculer le score
            self.calculate_score()
    
    def is_passed(self):
        """Vérifie si l'étudiant a réussi l'évaluation."""
        if self.score is None:
            return False
        return self.score >= self.assessment_type.passing_score


class AssessmentAnswer(models.Model):
    """
    Modèle représentant une réponse à une question d'évaluation.
    """
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('évaluation')
    )
    
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('question')
    )
    
    # Les réponses sont stockées en JSON pour s'adapter aux différents types de questions
    answer_data = models.JSONField(_('données de réponse'))
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('réponse d\'évaluation')
        verbose_name_plural = _('réponses d\'évaluation')
        unique_together = ('assessment', 'question')
    
    def __str__(self):
        return f"Réponse de {self.assessment.student.get_full_name()} à {self.question.text[:30]}"
    
    def is_correct(self):
        """
        Détermine si la réponse est correcte selon le type de question.
        Pour les questions de type échelle, texte, numérique, retourne toujours True.
        """
        question_type = self.question.question_type
        
        if question_type == 'single_choice':
            correct_option = self.question.options.get('correct_answer')
            return self.answer_data.get('selected_option') == correct_option
        
        elif question_type == 'multiple_choice':
            correct_options = set(self.question.options.get('correct_answers', []))
            selected_options = set(self.answer_data.get('selected_options', []))
            return correct_options == selected_options
        
        # Pour les autres types de questions, la correction est subjective
        return True


class SkillCategory(models.Model):
    """
    Modèle représentant une catégorie de compétence.
    """
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    icon = models.CharField(_('icône'), max_length=50, blank=True)
    order = models.PositiveIntegerField(_('ordre'), default=0)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('catégorie de compétence')
        verbose_name_plural = _('catégories de compétence')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Skill(models.Model):
    """
    Modèle représentant une compétence évaluable.
    """
    LEVEL_CHOICES = (
        ('basic', _('Basique')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
        ('expert', _('Expert')),
    )
    
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'))
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_('catégorie')
    )
    level = models.CharField(_('niveau'), max_length=20, choices=LEVEL_CHOICES, default='basic')
    icon = models.CharField(_('icône'), max_length=50, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('compétence')
        verbose_name_plural = _('compétences')
        ordering = ['category', 'level', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CareerField(models.Model):
    """
    Modèle représentant un domaine professionnel.
    """
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'))
    icon = models.CharField(_('icône'), max_length=50, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('domaine professionnel')
        verbose_name_plural = _('domaines professionnels')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class CareerPath(models.Model):
    """
    Modèle représentant une filière professionnelle.
    """
    name = models.CharField(_('nom'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'))
    field = models.ForeignKey(
        CareerField,
        on_delete=models.CASCADE,
        related_name='career_paths',
        verbose_name=_('domaine')
    )
    
    # Détails sur la filière
    average_salary = models.CharField(_('salaire moyen'), max_length=100, blank=True)
    job_prospects = models.CharField(_('perspectives d\'emploi'), max_length=100, blank=True)
    education_requirements = models.TextField(_('prérequis éducatifs'), blank=True)
    skills_required = models.ManyToManyField(
        Skill,
        related_name='career_paths',
        verbose_name=_('compétences requises')
    )
    
    # Contenu
    content = models.JSONField(_('contenu détaillé'), default=dict, blank=True)
    
    # États
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('filière professionnelle')
        verbose_name_plural = _('filières professionnelles')
        ordering = ['field', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.field.name})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class OrientationPath(models.Model):
    """
    Modèle représentant un parcours d'orientation personnalisé pour un étudiant.
    """
    STATUS_CHOICES = (
        ('draft', _('Brouillon')),
        ('proposed', _('Proposé')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('abandoned', _('Abandonné')),
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orientation_paths',
        verbose_name=_('étudiant')
    )
    
    advisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_paths',
        verbose_name=_('conseiller')
    )
    
    title = models.CharField(_('titre'), max_length=255)
    description = models.TextField(_('description'))
    
    # Relation avec les évaluations
    assessments = models.ManyToManyField(
        Assessment,
        related_name='orientation_paths',
        verbose_name=_('évaluations')
    )
    
    # Filières recommandées
    career_paths = models.ManyToManyField(
        CareerPath,
        through='OrientationCareerPath',
        related_name='orientation_paths',
        verbose_name=_('filières recommandées')
    )
    
    # Contenu du parcours d'orientation
    steps = models.JSONField(_('étapes'), default=list)
    resources = models.JSONField(_('ressources'), default=list)
    milestones = models.JSONField(_('jalons'), default=list)
    
    # État et progression
    status = models.CharField(_('statut'), max_length=20, choices=STATUS_CHOICES, default='draft')
    progress = models.PositiveIntegerField(_('progression (%)'), default=0)
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    start_date = models.DateField(_('date de début'), null=True, blank=True)
    target_end_date = models.DateField(_('date de fin prévue'), null=True, blank=True)
    completed_date = models.DateField(_('date de complétion'), null=True, blank=True)
    
    # Feedback
    student_feedback = models.TextField(_('commentaires de l\'étudiant'), blank=True)
    advisor_notes = models.TextField(_('notes du conseiller'), blank=True)
    
    class Meta:
        verbose_name = _('parcours d\'orientation')
        verbose_name_plural = _('parcours d\'orientation')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.student.get_full_name()}"
    
    def update_progress(self):
        """Met à jour la progression du parcours."""
        total_steps = len(self.steps)
        if total_steps == 0:
            self.progress = 0
            return
        
        completed_steps = sum(step.get('completed', False) for step in self.steps)
        self.progress = int((completed_steps / total_steps) * 100)
        self.save(update_fields=['progress'])
        
        # Mettre à jour le statut si nécessaire
        if self.progress == 100 and self.status == 'in_progress':
            self.status = 'completed'
            self.completed_date = timezone.now().date()
            self.save(update_fields=['status', 'completed_date'])


class OrientationCareerPath(models.Model):
    """
    Modèle intermédiaire entre OrientationPath et CareerPath, avec score de compatibilité.
    """
    orientation_path = models.ForeignKey(
        OrientationPath,
        on_delete=models.CASCADE,
        verbose_name=_('parcours d\'orientation')
    )
    
    career_path = models.ForeignKey(
        CareerPath,
        on_delete=models.CASCADE,
        verbose_name=_('filière professionnelle')
    )
    
    compatibility_score = models.PositiveIntegerField(_('score de compatibilité'), default=0)
    recommendation_reason = models.TextField(_('raison de la recommandation'), blank=True)
    is_primary = models.BooleanField(_('recommandation principale'), default=False)
    
    class Meta:
        verbose_name = _('filière recommandée')
        verbose_name_plural = _('filières recommandées')
        ordering = ['-compatibility_score']
        unique_together = ('orientation_path', 'career_path')
    
    def __str__(self):
        return f"{self.career_path.name} pour {self.orientation_path.student.get_full_name()} ({self.compatibility_score}%)"


class StudentSkill(models.Model):
    """
    Modèle représentant les compétences d'un étudiant et leur niveau.
    """
    PROFICIENCY_CHOICES = (
        (1, _('Débutant')),
        (2, _('Élémentaire')),
        (3, _('Intermédiaire')),
        (4, _('Avancé')),
        (5, _('Expert')),
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='skills',
        verbose_name=_('étudiant')
    )
    
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='student_skills',
        verbose_name=_('compétence')
    )
    
    proficiency_level = models.PositiveSmallIntegerField(
        _('niveau de maîtrise'),
        choices=PROFICIENCY_CHOICES,
        default=1
    )
    
    # Sources d'évaluation
    self_assessed = models.BooleanField(_('auto-évalué'), default=False)
    advisor_assessed = models.BooleanField(_('évalué par conseiller'), default=False)
    assessment_derived = models.BooleanField(_('dérivé d\'évaluation'), default=False)
    
    # Preuves et progression
    evidence = models.TextField(_('preuves'), blank=True)
    last_practiced = models.DateField(_('dernière pratique'), null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('compétence d\'étudiant')
        verbose_name_plural = _('compétences d\'étudiant')
        unique_together = ('student', 'skill')
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.skill.name} ({self.get_proficiency_level_display()})"