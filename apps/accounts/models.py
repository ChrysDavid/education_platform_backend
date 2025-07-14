from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Gestionnaire de modèle personnalisé pour le modèle User qui utilise l'email comme
    identifiant unique pour l'authentification au lieu des noms d'utilisateur.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Crée et enregistre un utilisateur avec l'email et le mot de passe donnés.
        """
        if not email:
            raise ValueError(_('Un email valide est requis'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Création automatique du profil spécifique seulement s'il n'existe pas déjà
        if user.type == 'student' and not hasattr(user, 'student_profile'):
            Student.objects.create(user=user)
        elif user.type == 'pupil' and not hasattr(user, 'pupil_profile'):
            Pupil.objects.create(user=user)
        elif user.type == 'teacher' and not hasattr(user, 'teacher_profile'):
            Teacher.objects.create(user=user)
        # elif user.type == 'advisor' and not hasattr(user, 'advisor_profile'):
        #     Advisor.objects.create(user=user)
        elif user.type == 'administrator' and not hasattr(user, 'administrator_profile'):
            Administrator.objects.create(user=user)
            
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée et enregistre un superutilisateur avec l'email et le mot de passe donnés.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('type', 'administrator')
        extra_fields.setdefault('verification_status', 'verified')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Le superutilisateur doit avoir is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé qui étend AbstractUser et PermissionsMixin
    et inclut des champs supplémentaires pour la vérification et le type d'utilisateur.
    """
    USER_TYPE_CHOICES = (
        ('student', 'Étudiant'),
        ('pupil', 'Élève'),
        ('teacher', 'Enseignant'),
        ('advisor', 'Conseiller d\'orientation'),
        ('administrator', 'Administrateur'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('unverified', 'Non vérifié'),
        ('pending', 'En attente'),
        ('verified', 'Vérifié'),
        ('rejected', 'Rejeté'),
    )

    COMMUNICATION_PREFERENCES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('phone', 'Appel téléphonique'),
    )

    LANGUAGE_LEVELS = (
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
        ('fluent', 'Courant'),
        ('native', 'Langue maternelle'),
    )

    # On supprime le champ username car on utilise email comme identifiant
    username = None
    email = models.EmailField(_('adresse email'), unique=True)
    first_name = models.CharField(_('prénom'), max_length=150)
    last_name = models.CharField(_('nom'), max_length=150)
    phone_number = models.CharField(_('numéro de téléphone'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date de naissance'), null=True, blank=True)
    profile_picture = models.ImageField(_('photo de profil'), upload_to='profile_pictures/', blank=True, null=True)
    address = models.CharField(_('adresse'), max_length=255, blank=True)
    city = models.CharField(_('ville'), max_length=100, blank=True)
    postal_code = models.CharField(_('code postal'), max_length=20, blank=True)
    country = models.CharField(_('pays'), max_length=100, blank=True)
    
    # Identité et documents
    identity_document = models.FileField(_('pièce d\'identité'), upload_to='identity_documents/', blank=True, null=True)
    
    # Consentements
    data_processing_consent = models.BooleanField(_('consentement au traitement des données'), default=False)
    image_rights_consent = models.BooleanField(_('autorisation de droit à l\'image'), default=False)
    
    # Préférences de communication
    communication_preferences = models.JSONField(_('préférences de communication'), default=list, blank=True)
    
    # Langues parlées
    languages = models.JSONField(_('langues parlées et niveaux'), default=dict, blank=True)
    
    # Contact d'urgence
    emergency_contact_name = models.CharField(_('nom du contact d\'urgence'), max_length=150, blank=True)
    emergency_contact_phone = models.CharField(_('téléphone du contact d\'urgence'), max_length=20, blank=True)
    emergency_contact_relation = models.CharField(_('relation avec le contact d\'urgence'), max_length=50, blank=True)
    
    date_joined = models.DateTimeField(_('date d\'inscription'), default=timezone.now)
    is_active = models.BooleanField(_('actif'), default=False)  # Inactif par défaut jusqu'à vérification
    is_staff = models.BooleanField(_('personnel'), default=False)
    
    type = models.CharField(_('type d\'utilisateur'), max_length=20, choices=USER_TYPE_CHOICES)
    verification_status = models.CharField(
        _('statut de vérification'), 
        max_length=20, 
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified'
    )
    verification_requested_date = models.DateTimeField(_('date de demande de vérification'), null=True, blank=True)
    verification_completed_date = models.DateTimeField(_('date de vérification complétée'), null=True, blank=True)
    verification_notes = models.TextField(_('notes de vérification'), blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'type']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def save(self, *args, **kwargs):
        created = not self.pk  # Vérifie si c'est une nouvelle création
        super().save(*args, **kwargs)
        
        if created and not self.is_staff:  # Pour les nouveaux utilisateurs non-admins
            self.verification_status = 'unverified'
            self.save(update_fields=['verification_status'])
    
    def get_full_name(self):
        """Retourne le prénom et le nom de l'utilisateur avec un espace entre."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Retourne le prénom de l'utilisateur."""
        return self.first_name
    
    def is_verified(self):
        """Vérifie si l'utilisateur est vérifié."""
        return self.verification_status == 'verified'
    
    def is_pending_verification(self):
        """Vérifie si l'utilisateur est en attente de vérification."""
        return self.verification_status == 'pending'
    
    def request_verification(self):
        """Définit le statut de vérification sur 'en attente' et enregistre la date de demande."""
        self.verification_status = 'pending'
        self.verification_requested_date = timezone.now()
        self.save(update_fields=['verification_status', 'verification_requested_date'])
        return True

    def complete_verification(self, status, notes=''):
        """
        Complète le processus de vérification avec le statut final.
        """
        valid_statuses = ['verified', 'rejected']
        if status not in valid_statuses:
            raise ValueError(f"Statut invalide. Doit être l'un des suivants: {', '.join(valid_statuses)}")
        
        self.verification_status = status
        self.verification_completed_date = timezone.now()
        self.verification_notes = notes
        
        # Activer le compte si vérifié
        if status == 'verified':
            self.is_active = True
        
        self.save(update_fields=['verification_status', 'verification_completed_date', 'verification_notes', 'is_active'])
        return True

    def get_profile_info(self):
        """Retourne les infos du profil selon le type"""
        if hasattr(self, f'{self.type}_profile'):
            return getattr(self, f'{self.type}_profile')
        return None




class Student(models.Model):
    """Profil spécifique pour les étudiants."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='student_profile'
    )
    school_id = models.PositiveIntegerField(_('ID de l\'école'), null=True, blank=True)
    institution_name = models.CharField(_('établissement fréquenté'), max_length=255, blank=True)
    current_level = models.CharField(_('niveau d\'études actuel'), max_length=100, blank=True)
    major = models.CharField(_('spécialité / filière suivie'), max_length=100, blank=True)
    academic_year = models.CharField(_('année universitaire en cours'), max_length=9, blank=True)
    student_id = models.CharField(_('matricule étudiant'), max_length=50, blank=True)
    
    # Bourse et logement
    scholarship = models.BooleanField(_('bénéficiaire d\'une bourse'), default=False)
    scholarship_type = models.CharField(_('type de bourse'), max_length=100, blank=True)
    housing_needs = models.JSONField(_('logement étudiant recherché'), default=list, blank=True)
    
    # Stages et compétences
    internship_search = models.TextField(_('stages/alternance recherchés'), blank=True)
    computer_skills = models.JSONField(_('compétences informatiques'), default=list, blank=True)
    extracurricular_activities = models.TextField(_('activités extra-universitaires'), blank=True)
    
    interests = models.JSONField(_('centres d\'intérêt'), default=list, blank=True)
    average_grade = models.FloatField(_('moyenne générale'), null=True, blank=True)
    
    @property
    def school(self):
        from ..schools.models import School
        return School.objects.get(id=self.school_id) if self.school_id else None

    class Meta:
        verbose_name = _('étudiant')
        verbose_name_plural = _('étudiants')

    def __str__(self):
        return f"Étudiant: {self.user.get_full_name()}"
    




    

class Pupil(models.Model):
    """Profil spécifique pour les élèves."""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='pupil_profile'
    )
    school_name = models.CharField(_('nom de l\'établissement scolaire'), max_length=255, blank=True)
    current_level = models.CharField(_('niveau actuel'), max_length=100, blank=True)
    specialization = models.CharField(_('section ou spécialité'), max_length=100, blank=True)
    
    # Informations sur les responsables légaux
    legal_guardian_name = models.CharField(_('nom du responsable légal'), max_length=150, blank=True)
    legal_guardian_phone = models.CharField(_('numéro de téléphone du parent ou tuteur'), max_length=20, blank=True)
    second_guardian_name = models.CharField(_('nom du second parent/responsable légal'), max_length=150, blank=True)
    second_guardian_phone = models.CharField(_('téléphone du second responsable légal'), max_length=20, blank=True)
    
    # Services et besoins particuliers
    cafeteria = models.BooleanField(_('inscription à la cantine'), default=False)
    dietary_restrictions = models.TextField(_('régime alimentaire particulier'), blank=True)
    school_transport = models.BooleanField(_('utilisation du transport scolaire'), default=False)
    transport_details = models.TextField(_('détails sur le transport scolaire'), blank=True)
    
    # Informations médicales et assurances
    medical_information = models.TextField(_('informations médicales importantes'), blank=True)
    school_insurance = models.CharField(_('assurance scolaire'), max_length=255, blank=True)
    
    # Autorisations
    exit_permissions = models.JSONField(_('autorisations de sortie'), default=list, blank=True)
    siblings_at_school = models.TextField(_('fratrie dans l\'établissement'), blank=True)
    desired_activities = models.JSONField(_('activités périscolaires souhaitées'), default=list, blank=True)

    class Meta:
        verbose_name = _('élève')
        verbose_name_plural = _('élèves')

    def __str__(self):
        return f"Élève: {self.user.get_full_name()}"











class Teacher(models.Model):
    """Profil spécifique pour les enseignants."""
    TEACHING_TYPES = (
        ('in_person', 'Présentiel'),
        ('online', 'En ligne'),
        ('hybrid', 'Hybride'),
    )

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='teacher_profile'
    )
    school_id = models.PositiveIntegerField(
        _('ID de l\'école'), 
        null=True, 
        blank=True,
        help_text=_("ID de l'établissement scolaire dans le système")
    )
    institution_name = models.CharField(
        _('établissement où il enseigne'), 
        max_length=255,
        help_text=_("Nom de l'établissement d'enseignement")
    )
    subjects = models.JSONField(
        _('matières enseignées'), 
        default=list,
        help_text=_("Liste des matières enseignées par le professeur")
    )
    highest_degree = models.CharField(
        _('diplôme le plus élevé obtenu'), 
        max_length=255,
        help_text=_("Dernier diplôme académique obtenu")
    )
    degree_document = models.FileField(
        _('document du diplôme'), 
        upload_to='teacher_degrees/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_("Document scanné du diplôme (PDF ou image)"),
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])]
    )
    years_of_experience = models.PositiveIntegerField(
        _('années d\'expérience en enseignement'), 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(70)],
        help_text=_("Nombre d'années d'expérience dans l'enseignement")
    )
    teaching_type = models.JSONField(
        _('type d\'enseignement'), 
        default=list,
        help_text=_("Types d'enseignement proposés (présentiel, en ligne, hybride)")
    )
    cv = models.FileField(
        _('CV complet'), 
        upload_to='teacher_cvs/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_("Curriculum Vitae du professeur"),
        validators=[FileExtensionValidator(['pdf', 'doc', 'docx'])]
    )
    # AJOUT DU CHAMP MANQUANT
    identity_document = models.FileField(
        _('document d\'identité'), 
        upload_to='teacher_identity/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_("Document d'identité scanné (PDF ou image)"),
        validators=[FileExtensionValidator(['pdf', 'png', 'jpg', 'jpeg'])]
    )
    availability = models.JSONField(
        _('disponibilités horaires'), 
        default=dict,
        blank=True,
        help_text=_("Disponibilités hebdomadaires pour les cours")
    )
    professional_references = models.TextField(
        _('références professionnelles'), 
        blank=True,
        help_text=_("Contacts ou références professionnelles")
    )
    continuous_education = models.JSONField(
        _('formations continues suivies'), 
        default=list,
        blank=True,
        help_text=_("Liste des formations continues ou certifications récentes")
    )
    qualifications = models.CharField(
        _('qualifications'), 
        max_length=255,
        help_text=_("Qualifications pédagogiques spécifiques")
    )
    professional_license = models.CharField(
        _('numéro de licence professionnelle'), 
        max_length=100, 
        blank=True,
        help_text=_("Numéro d'agrément ou licence d'enseignement")
    )
    expertise_areas = models.JSONField(
        _('domaines d\'expertise'), 
        default=list, 
        blank=True,
        help_text=_("Domaines de spécialisation ou expertises particulières")
    )
    teaching_philosophy = models.TextField(
        _('philosophie d\'enseignement'), 
        blank=True,
        help_text=_("Description de l'approche pédagogique")
    )
    hourly_rate = models.DecimalField(
        _('tarif horaire'), 
        max_digits=6, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Tarif horaire pour les cours particuliers")
    )
    is_approved = models.BooleanField(
        _('approuvé'), 
        default=False,
        help_text=_("Indique si le profil a été approuvé par l'administration")
    )
    approval_date = models.DateField(
        _('date d\'approbation'), 
        null=True,
        blank=True,
        help_text=_("Date à laquelle le profil a été approuvé")
    )

    class Meta:
        verbose_name = _('enseignant')
        verbose_name_plural = _('enseignants')
        ordering = ['-user__date_joined']
        indexes = [
            models.Index(fields=['institution_name']),
            models.Index(fields=['highest_degree']),
        ]

    def __str__(self):
        return f"Enseignant: {self.user.get_full_name()}"

    def clean(self):
        """Validation supplémentaire du modèle"""
        if self.years_of_experience < 0:
            raise ValidationError({
                'years_of_experience': _("Le nombre d'années d'expérience ne peut pas être négatif")
            })

    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour un traitement personnalisé"""
        self.clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('teacher-detail', kwargs={'pk': self.pk})

    @property
    def full_profile_complete(self):
        """Vérifie si le profil est complet"""
        required_fields = [
            self.institution_name,
            self.subjects,
            self.highest_degree,
            self.years_of_experience,
            self.teaching_type,
            self.qualifications
        ]
        return all(required_fields) and bool(self.degree_document) and bool(self.cv)

    def get_teaching_types_display(self):
        """Retourne les types d'enseignement sous forme lisible"""
        return ", ".join([dict(self.TEACHING_TYPES).get(t, t) for t in self.teaching_type])




    
    


class Advisor(models.Model):
    """Profil spécifique pour les conseillers d'orientation."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='advisor_profile'
    )
    organization = models.CharField(_('entreprise ou cabinet de rattachement'), max_length=255)
    specialization = models.CharField(_('spécialité du conseil'), max_length=255)
    years_of_experience = models.PositiveIntegerField(_('années d\'expérience en conseil'), default=0)
    
    # Certifications et licences
    professional_license = models.CharField(_('numéro de licence professionnelle'), max_length=100, blank=True)
    certifications = models.JSONField(_('certification(s) professionnelle(s)'), default=list, blank=True)
    certification_documents = models.JSONField(_('documents de certification'), default=list, blank=True)
    
    # Zones d'intervention et tarifs
    geographical_areas = models.JSONField(_('zones géographiques d\'intervention'), default=list, blank=True)
    rates = models.JSONField(_('tarifs pratiqués'), default=dict, blank=True)
    
    # Portfolio et disponibilités
    portfolio = models.FileField(_('portfolio/exemples de réalisations'), upload_to='advisor_portfolios/', blank=True, null=True)
    portfolio_link = models.URLField(_('lien vers portfolio en ligne'), blank=True)
    publications = models.JSONField(_('publications/travaux de recherche'), default=list, blank=True)
    availability = models.JSONField(_('disponibilités pour rendez-vous'), default=dict, blank=True)

    class Meta:
        verbose_name = _('conseiller')
        verbose_name_plural = _('conseillers')

    def __str__(self):
        return f"Conseiller: {self.user.get_full_name()}"






    
    


class Administrator(models.Model):
    """Profil spécifique pour les administrateurs."""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        primary_key=True,
        related_name='administrator_profile'
    )
    role = models.CharField(_('rôle'), max_length=100)
    department = models.CharField(_('département'), max_length=100, blank=True)
    administrative_level = models.CharField(_('niveau administratif'), max_length=100, blank=True)
    responsibilities = models.JSONField(_('responsabilités principales'), default=list, blank=True)

    class Meta:
        verbose_name = _('administrateur')
        verbose_name_plural = _('administrateurs')

    def __str__(self):
        return f"Administrateur: {self.user.get_full_name()}"