from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class SchoolType(models.Model):
    """
    Modèle représentant un type d'établissement scolaire (primaire, secondaire, supérieur, etc.)
    """
    name = models.CharField(_('nom'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    class Meta:
        verbose_name = _('type d\'établissement')
        verbose_name_plural = _('types d\'établissement')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class City(models.Model):
    """
    Modèle représentant une ville en Côte d'Ivoire.
    """
    name = models.CharField(_('nom'), max_length=100, unique=True)
    zip_code = models.CharField(_('code postal'), max_length=10, blank=True)
    region = models.CharField(_('région'), max_length=100, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    longitude = models.FloatField(_('longitude'), null=True, blank=True)
    latitude = models.FloatField(_('latitude'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('ville')
        verbose_name_plural = _('villes')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class School(models.Model):
    """
    Modèle représentant un établissement scolaire.
    """
    name = models.CharField(_('nom'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    school_type = models.ForeignKey(
        SchoolType,
        on_delete=models.CASCADE,
        related_name='schools',
        verbose_name=_('type d\'établissement')
    )
    address = models.CharField(_('adresse'), max_length=255, blank=True)
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        related_name='schools',
        verbose_name=_('ville')
    )
    postal_code = models.CharField(_('code postal'), max_length=10, blank=True)
    phone = models.CharField(_('téléphone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('site web'), blank=True)
    description = models.TextField(_('description'), blank=True)
    logo = models.ImageField(_('logo'), upload_to='school_logos/', blank=True, null=True)
    cover_image = models.ImageField(_('image de couverture'), upload_to='school_covers/', blank=True, null=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_verified = models.BooleanField(_('vérifié'), default=False)
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Coordonnées géographiques
    longitude = models.FloatField(_('longitude'), null=True, blank=True)
    latitude = models.FloatField(_('latitude'), null=True, blank=True)
    
    # Métadonnées
    founded_year = models.PositiveIntegerField(_('année de fondation'), null=True, blank=True)
    accreditation = models.CharField(_('accréditation'), max_length=255, blank=True)
    student_count = models.PositiveIntegerField(_('nombre d\'élèves'), null=True, blank=True)
    staff_count = models.PositiveIntegerField(_('nombre de personnel'), null=True, blank=True)
    director_name = models.CharField(_('nom du directeur'), max_length=255, blank=True)
    
    # Paramètres de contact administratif
    admin_contact_name = models.CharField(_('nom du contact administratif'), max_length=255, blank=True)
    admin_contact_email = models.EmailField(_('email du contact administratif'), blank=True)
    admin_contact_phone = models.CharField(_('téléphone du contact administratif'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('établissement')
        verbose_name_plural = _('établissements')
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['city']),
            models.Index(fields=['school_type']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('schools:school_detail', kwargs={'slug': self.slug})
    
    @property
    def student_count_display(self):
        """
        Affiche le nombre d'élèves avec une formulation adaptée.
        """
        if self.student_count is None:
            return _("Nombre d'élèves non disponible")
        if self.student_count == 0:
            return _("Pas d'élèves actuellement")
        if self.student_count == 1:
            return _("1 élève")
        return _("%d élèves") % self.student_count
    
    @property
    def address_display(self):
        """
        Renvoie l'adresse complète formatée.
        """
        parts = [part for part in [self.address, self.postal_code, self.city.name if self.city else None] if part]
        return ", ".join(parts)


class Department(models.Model):
    """
    Modèle représentant un département ou une section au sein d'un établissement.
    """
    name = models.CharField(_('nom'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('établissement')
    )
    description = models.TextField(_('description'), blank=True)
    head_name = models.CharField(_('nom du responsable'), max_length=255, blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('département')
        verbose_name_plural = _('départements')
        ordering = ['school', 'name']
        unique_together = ('school', 'slug')
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Program(models.Model):
    """
    Modèle représentant un programme académique ou une filière proposée 
    par un établissement ou un département.
    """
    name = models.CharField(_('nom'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255)
    code = models.CharField(_('code'), max_length=50, blank=True)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='programs',
        verbose_name=_('établissement')
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programs',
        verbose_name=_('département')
    )
    description = models.TextField(_('description'), blank=True)
    duration = models.CharField(_('durée'), max_length=100, blank=True)
    level = models.CharField(_('niveau'), max_length=100, blank=True)
    degree_awarded = models.CharField(_('diplôme délivré'), max_length=255, blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    admission_requirements = models.TextField(_('conditions d\'admission'), blank=True)
    career_opportunities = models.TextField(_('débouchés professionnels'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('programme')
        verbose_name_plural = _('programmes')
        ordering = ['school', 'name']
        unique_together = ('school', 'slug')
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Facility(models.Model):
    """
    Modèle représentant un équipement ou une installation d'un établissement.
    """
    FACILITY_TYPE_CHOICES = (
        ('library', _('Bibliothèque')),
        ('laboratory', _('Laboratoire')),
        ('sports', _('Installations sportives')),
        ('technology', _('Équipement technologique')),
        ('dormitory', _('Internat')),
        ('canteen', _('Cantine')),
        ('medical', _('Service médical')),
        ('other', _('Autre')),
    )
    
    name = models.CharField(_('nom'), max_length=255)
    facility_type = models.CharField(_('type d\'équipement'), max_length=50, choices=FACILITY_TYPE_CHOICES)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='facilities',
        verbose_name=_('établissement')
    )
    description = models.TextField(_('description'), blank=True)
    image = models.ImageField(_('image'), upload_to='facility_images/', blank=True, null=True)
    quantity = models.PositiveIntegerField(_('quantité'), default=1)
    is_active = models.BooleanField(_('actif'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('équipement')
        verbose_name_plural = _('équipements')
        ordering = ['school', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.school.name}"


class SchoolContact(models.Model):
    """
    Modèle représentant un contact spécifique au sein d'un établissement.
    """
    CONTACT_TYPE_CHOICES = (
        ('general', _('Contact général')),
        ('admissions', _('Admissions')),
        ('academic', _('Services académiques')),
        ('administration', _('Administration')),
        ('technical', _('Support technique')),
        ('other', _('Autre')),
    )
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('établissement')
    )
    contact_type = models.CharField(_('type de contact'), max_length=50, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(_('nom'), max_length=255)
    title = models.CharField(_('titre'), max_length=255, blank=True)
    phone = models.CharField(_('téléphone'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('actif'), default=True)
    
    class Meta:
        verbose_name = _('contact d\'établissement')
        verbose_name_plural = _('contacts d\'établissement')
        ordering = ['school', 'contact_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_contact_type_display()}) - {self.school.name}"


class SchoolReview(models.Model):
    """
    Modèle représentant une évaluation d'un établissement par un utilisateur.
    """
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('établissement')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='school_reviews',
        verbose_name=_('utilisateur')
    )
    rating = models.PositiveSmallIntegerField(
        _('note'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(_('titre'), max_length=255, blank=True)
    comment = models.TextField(_('commentaire'), blank=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    is_verified = models.BooleanField(_('vérifié'), default=False)
    is_public = models.BooleanField(_('public'), default=True)
    
    class Meta:
        verbose_name = _('évaluation d\'établissement')
        verbose_name_plural = _('évaluations d\'établissement')
        ordering = ['-created_at']
        unique_together = ('school', 'user')
    
    def __str__(self):
        return f"Évaluation de {self.user.get_full_name()} pour {self.school.name}"


class SchoolMedia(models.Model):
    """
    Modèle représentant un média (photo, vidéo) lié à un établissement.
    """
    MEDIA_TYPE_CHOICES = (
        ('photo', _('Photo')),
        ('video', _('Vidéo')),
        ('document', _('Document')),
    )
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='media',
        verbose_name=_('établissement')
    )
    title = models.CharField(_('titre'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    media_type = models.CharField(_('type de média'), max_length=20, choices=MEDIA_TYPE_CHOICES)
    file = models.FileField(_('fichier'), upload_to='school_media/')
    thumbnail = models.ImageField(_('vignette'), upload_to='school_media/thumbnails/', blank=True, null=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    is_public = models.BooleanField(_('public'), default=True)
    
    class Meta:
        verbose_name = _('média d\'établissement')
        verbose_name_plural = _('médias d\'établissement')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.school.name}"


class SchoolEvent(models.Model):
    """
    Modèle représentant un événement organisé par un établissement.
    """
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_('établissement')
    )
    title = models.CharField(_('titre'), max_length=255)
    description = models.TextField(_('description'))
    start_date = models.DateTimeField(_('date de début'))
    end_date = models.DateTimeField(_('date de fin'), null=True, blank=True)
    location = models.CharField(_('lieu'), max_length=255, blank=True)
    contact_email = models.EmailField(_('email de contact'), blank=True)
    contact_phone = models.CharField(_('téléphone de contact'), max_length=20, blank=True)
    image = models.ImageField(_('image'), upload_to='school_events/', blank=True, null=True)
    registration_url = models.URLField(_('lien d\'inscription'), blank=True)
    is_public = models.BooleanField(_('public'), default=True)
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('événement')
        verbose_name_plural = _('événements')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.title} - {self.school.name}"
    
    @property
    def is_past(self):
        """
        Indique si l'événement est passé.
        """
        import datetime
        if self.end_date:
            return self.end_date < datetime.datetime.now(datetime.timezone.utc)
        return self.start_date < datetime.datetime.now(datetime.timezone.utc)
    
    @property
    def is_ongoing(self):
        """
        Indique si l'événement est en cours.
        """
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now