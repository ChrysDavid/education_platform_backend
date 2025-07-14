from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

class UserActivity(models.Model):
    """
    Modèle pour suivre l'activité des utilisateurs sur la plateforme.
    """
    ACTION_TYPES = (
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('view', _('Consultation')),
        ('create', _('Création')),
        ('update', _('Mise à jour')),
        ('delete', _('Suppression')),
        ('search', _('Recherche')),
        ('download', _('Téléchargement')),
        ('upload', _('Téléversement')),
        ('other', _('Autre')),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name=_('utilisateur')
    )
    
    timestamp = models.DateTimeField(_('date et heure'), default=timezone.now)
    action_type = models.CharField(_('type d\'action'), max_length=20, choices=ACTION_TYPES)
    action_detail = models.CharField(_('détail de l\'action'), max_length=255, blank=True)
    
    # Relation polymorphique avec n'importe quel objet
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('type de contenu')
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Informations supplémentaires
    ip_address = models.GenericIPAddressField(_('adresse IP'), null=True, blank=True)
    user_agent = models.CharField(_('user agent'), max_length=512, blank=True)
    session_id = models.CharField(_('identifiant de session'), max_length=40, blank=True)
    
    # Métadonnées supplémentaires (clés arbitraires)
    data = models.JSONField(_('données'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('activité utilisateur')
        verbose_name_plural = _('activités utilisateur')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_action_type_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def log(cls, user, action_type, action_detail='', related_object=None, request=None, **kwargs):
        """
        Méthode de classe pour faciliter la création d'entrées d'activité.
        """
        activity = cls(
            user=user,
            action_type=action_type,
            action_detail=action_detail,
            **kwargs
        )
        
        # Si un objet lié est fourni
        if related_object:
            activity.content_type = ContentType.objects.get_for_model(related_object)
            activity.object_id = related_object.pk
        
        # Si une requête HTTP est fournie, extraire les informations supplémentaires
        if request:
            activity.ip_address = cls.get_client_ip(request)
            activity.user_agent = request.META.get('HTTP_USER_AGENT', '')
            activity.session_id = request.session.session_key
        
        activity.save()
        return activity
    
    @staticmethod
    def get_client_ip(request):
        """
        Extrait l'adresse IP du client à partir de la requête HTTP.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class Report(models.Model):
    """
    Modèle pour stocker les rapports générés.
    """
    REPORT_TYPES = (
        ('user_activity', _('Activité utilisateur')),
        ('resource_usage', _('Utilisation des ressources')),
        ('appointment_stats', _('Statistiques des rendez-vous')),
        ('user_stats', _('Statistiques utilisateurs')),
        ('orientation_stats', _('Statistiques d\'orientation')),
        ('verification_stats', _('Statistiques de vérification')),
        ('custom', _('Personnalisé')),
    )
    
    REPORT_FORMATS = (
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('html', 'HTML'),
    )
    
    title = models.CharField(_('titre'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    report_type = models.CharField(_('type de rapport'), max_length=30, choices=REPORT_TYPES)
    report_format = models.CharField(_('format du rapport'), max_length=10, choices=REPORT_FORMATS)
    
    # Paramètres de génération
    parameters = models.JSONField(_('paramètres'), default=dict, blank=True)
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    last_generated = models.DateTimeField(_('dernière génération'), null=True, blank=True)
    start_date = models.DateField(_('date de début'), null=True, blank=True)
    end_date = models.DateField(_('date de fin'), null=True, blank=True)
    
    # Fichier généré
    file = models.FileField(_('fichier'), upload_to='reports/%Y/%m/', null=True, blank=True)
    
    # Utilisateur qui a créé le rapport
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name=_('créé par')
    )
    
    # État du rapport
    is_scheduled = models.BooleanField(_('planifié'), default=False)
    schedule_frequency = models.CharField(_('fréquence de planification'), max_length=50, blank=True)
    next_run = models.DateTimeField(_('prochaine exécution'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('rapport')
        verbose_name_plural = _('rapports')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()}) - {self.created_at.strftime('%d/%m/%Y')}"
    
    def generate(self):
        """
        Génère le rapport en utilisant le service approprié.
        """
        # Importer ici pour éviter les dépendances circulaires
        from .services import ReportService
        
        service = ReportService(self)
        result = service.generate()
        
        # Mettre à jour la date de dernière génération
        self.last_generated = timezone.now()
        self.save(update_fields=['last_generated'])
        
        return result

class Dashboard(models.Model):
    """
    Modèle pour représenter les tableaux de bord personnalisés.
    """
    title = models.CharField(_('titre'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Configuration des widgets
    layout = models.JSONField(_('disposition'), default=dict)
    
    # Lié à un utilisateur
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name=_('utilisateur')
    )
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    # Paramètres
    is_default = models.BooleanField(_('par défaut'), default=False)
    is_public = models.BooleanField(_('public'), default=False)
    
    class Meta:
        verbose_name = _('tableau de bord')
        verbose_name_plural = _('tableaux de bord')
        unique_together = ('user', 'title')
        ordering = ['-is_default', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.user.get_full_name()})"
    
    def save(self, *args, **kwargs):
        # Si ce tableau de bord est défini comme par défaut, désactiver les autres
        if self.is_default:
            Dashboard.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)

class DashboardWidget(models.Model):
    """
    Modèle pour représenter un widget dans un tableau de bord.
    """
    WIDGET_TYPES = (
        ('chart', _('Graphique')),
        ('counter', _('Compteur')),
        ('table', _('Tableau')),
        ('kpi', _('Indicateur de performance')),
        ('timeline', _('Chronologie')),
        ('map', _('Carte')),
        ('custom', _('Personnalisé')),
    )
    
    CHART_TYPES = (
        ('line', _('Ligne')),
        ('bar', _('Barres')),
        ('pie', _('Secteurs')),
        ('doughnut', _('Anneau')),
        ('radar', _('Radar')),
        ('scatter', _('Nuage de points')),
        ('area', _('Aires')),
    )
    
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name=_('tableau de bord')
    )
    
    title = models.CharField(_('titre'), max_length=255)
    widget_type = models.CharField(_('type de widget'), max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(_('type de graphique'), max_length=20, choices=CHART_TYPES, blank=True)
    
    # Configuration et données
    config = models.JSONField(_('configuration'), default=dict)
    data_source = models.CharField(_('source de données'), max_length=255, blank=True)
    refresh_rate = models.PositiveIntegerField(_('taux de rafraîchissement (minutes)'), default=0)
    
    # Position et taille dans le tableau de bord
    position_x = models.PositiveSmallIntegerField(_('position X'), default=0)
    position_y = models.PositiveSmallIntegerField(_('position Y'), default=0)
    width = models.PositiveSmallIntegerField(_('largeur'), default=1)
    height = models.PositiveSmallIntegerField(_('hauteur'), default=1)
    
    # Dates
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    last_refreshed = models.DateTimeField(_('dernier rafraîchissement'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('widget')
        verbose_name_plural = _('widgets')
        ordering = ['dashboard', 'position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()}) - {self.dashboard.title}"
    
    def refresh_data(self):
        """
        Rafraîchit les données du widget.
        """
        # Importer ici pour éviter les dépendances circulaires
        from .services import WidgetService
        
        service = WidgetService(self)
        result = service.refresh_data()
        
        # Mettre à jour la date de dernier rafraîchissement
        self.last_refreshed = timezone.now()
        self.save(update_fields=['last_refreshed'])
        
        return result

class Metric(models.Model):
    """
    Modèle pour représenter des métriques et KPIs.
    """
    name = models.CharField(_('nom'), max_length=100, unique=True)
    display_name = models.CharField(_('nom d\'affichage'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    # Type de métrique
    is_counter = models.BooleanField(_('est un compteur'), default=False)
    is_rate = models.BooleanField(_('est un taux'), default=False)
    is_gauge = models.BooleanField(_('est une jauge'), default=False)
    
    # Unité et formatage
    unit = models.CharField(_('unité'), max_length=50, blank=True)
    decimal_places = models.PositiveSmallIntegerField(_('décimales'), default=0)
    
    # Pour les taux
    numerator_metric = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='numerator_for',
        verbose_name=_('métrique numérateur')
    )
    denominator_metric = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='denominator_for',
        verbose_name=_('métrique dénominateur')
    )
    
    # Calcul
    calculation_method = models.CharField(_('méthode de calcul'), max_length=255, blank=True)
    sql_query = models.TextField(_('requête SQL'), blank=True)
    python_function = models.CharField(_('fonction Python'), max_length=255, blank=True)
    
    # Alertes
    threshold_warning = models.DecimalField(_('seuil d\'avertissement'), max_digits=15, decimal_places=5, null=True, blank=True)
    threshold_critical = models.DecimalField(_('seuil critique'), max_digits=15, decimal_places=5, null=True, blank=True)
    
    # Intervalles de temps disponibles
    available_intervals = models.JSONField(_('intervalles disponibles'), default=list)
    
    # Paramètres
    is_active = models.BooleanField(_('active'), default=True)
    is_public = models.BooleanField(_('publique'), default=False)
    is_realtime = models.BooleanField(_('temps réel'), default=False)
    
    # Dates
    created_at = models.DateTimeField(_('créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mise à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('métrique')
        verbose_name_plural = _('métriques')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    def get_value(self, start_date=None, end_date=None, interval='day'):
        """
        Récupère la valeur de la métrique pour l'intervalle spécifié.
        """
        # Importer ici pour éviter les dépendances circulaires
        from .services import MetricService
        
        service = MetricService(self)
        return service.get_value(start_date, end_date, interval)

class MetricValue(models.Model):
    """
    Modèle pour stocker les valeurs historiques des métriques.
    """
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_('métrique')
    )
    
    timestamp = models.DateTimeField(_('date et heure'))
    value = models.DecimalField(_('valeur'), max_digits=15, decimal_places=5)
    
    # Intervalle de temps
    interval = models.CharField(_('intervalle'), max_length=20, default='day')
    start_date = models.DateTimeField(_('date de début'), null=True, blank=True)
    end_date = models.DateTimeField(_('date de fin'), null=True, blank=True)
    
    # Dimensions (filtres, segmentation)
    dimensions = models.JSONField(_('dimensions'), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('valeur de métrique')
        verbose_name_plural = _('valeurs de métrique')
        unique_together = ('metric', 'timestamp', 'interval')
        ordering = ['metric', '-timestamp']
        indexes = [
            models.Index(fields=['metric', 'timestamp']),
            models.Index(fields=['metric', 'interval', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.metric.name} - {self.value} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

class AnalyticsEvent(models.Model):
    """
    Modèle pour les événements analytiques custom.
    """
    event_name = models.CharField(_('nom de l\'événement'), max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_events',
        verbose_name=_('utilisateur')
    )
    
    timestamp = models.DateTimeField(_('date et heure'), default=timezone.now)
    
    # Propriétés de l'événement
    properties = models.JSONField(_('propriétés'), default=dict, blank=True)
    
    # Informations sur le client
    client_ip = models.GenericIPAddressField(_('IP client'), null=True, blank=True)
    user_agent = models.CharField(_('user agent'), max_length=512, blank=True)
    session_id = models.CharField(_('ID de session'), max_length=100, blank=True)
    
    # Pour le suivi de conversion
    campaign = models.CharField(_('campagne'), max_length=100, blank=True)
    source = models.CharField(_('source'), max_length=100, blank=True)
    medium = models.CharField(_('medium'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('événement analytique')
        verbose_name_plural = _('événements analytiques')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_name']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
    
    @classmethod
    def track(cls, event_name, user=None, properties=None, request=None, **kwargs):
        """
        Méthode de classe pour faciliter le suivi des événements.
        """
        if properties is None:
            properties = {}
        
        event = cls(
            event_name=event_name,
            user=user,
            properties=properties,
            **kwargs
        )
        
        # Si une requête HTTP est fournie, extraire les informations supplémentaires
        if request:
            event.client_ip = cls.get_client_ip(request)
            event.user_agent = request.META.get('HTTP_USER_AGENT', '')
            event.session_id = request.session.session_key
            
            # Attribution
            event.campaign = request.GET.get('utm_campaign', '')
            event.source = request.GET.get('utm_source', '')
            event.medium = request.GET.get('utm_medium', '')
        
        event.save()
        return event
    
    @staticmethod
    def get_client_ip(request):
        """
        Extrait l'adresse IP du client à partir de la requête HTTP.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip