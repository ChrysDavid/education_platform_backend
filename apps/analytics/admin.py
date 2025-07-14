from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    UserActivity, Report, Dashboard, DashboardWidget,
    Metric, MetricValue, AnalyticsEvent
)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'action_type', 'action_detail', 'timestamp', 'ip_address')
    list_filter = ('action_type', 'timestamp')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'action_detail', 'ip_address')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'user', 'action_type', 'action_detail', 
                      'content_type', 'object_id', 'ip_address', 'user_agent', 'session_id', 'data')
    
    fieldsets = (
        (_('Utilisateur et action'), {
            'fields': ('user', 'action_type', 'action_detail', 'timestamp')
        }),
        (_('Objet lié'), {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        (_('Informations client'), {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        (_('Données supplémentaires'), {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return _("Utilisateur supprimé")
    user_display.short_description = _('Utilisateur')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'report_format', 'created_by_display', 'created_at', 'last_generated', 'file_link')
    list_filter = ('report_type', 'report_format', 'is_scheduled', 'created_at')
    search_fields = ('title', 'description', 'created_by__first_name', 'created_by__last_name', 'created_by__email')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('title', 'description', 'created_by', 'created_at')
        }),
        (_('Type et format'), {
            'fields': ('report_type', 'report_format')
        }),
        (_('Paramètres'), {
            'fields': ('parameters', 'start_date', 'end_date')
        }),
        (_('Génération'), {
            'fields': ('file', 'last_generated')
        }),
        (_('Planification'), {
            'fields': ('is_scheduled', 'schedule_frequency', 'next_run'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'last_generated')
    
    def created_by_display(self, obj):
        if obj.created_by:
            return f"{obj.created_by.get_full_name()} ({obj.created_by.email})"
        return _("Utilisateur supprimé")
    created_by_display.short_description = _('Créé par')
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, _('Télécharger'))
        return "-"
    file_link.short_description = _('Fichier')
    
    actions = ['generate_reports']
    
    def generate_reports(self, request, queryset):
        count = 0
        for report in queryset:
            try:
                report.generate()
                count += 1
            except Exception as e:
                self.message_user(request, _('Erreur lors de la génération du rapport "{}" : {}').format(report.title, str(e)), level='ERROR')
        
        self.message_user(request, _('%(count)d rapports ont été générés avec succès.') % {'count': count})
    generate_reports.short_description = _('Générer les rapports sélectionnés')

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_display', 'created_at', 'updated_at', 'is_default', 'is_public', 'widget_count')
    list_filter = ('is_default', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'user__first_name', 'user__last_name', 'user__email')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('title', 'description', 'user')
        }),
        (_('Configuration'), {
            'fields': ('layout', 'is_default', 'is_public')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def user_display(self, obj):
        return f"{obj.user.get_full_name()} ({obj.user.email})"
    user_display.short_description = _('Utilisateur')
    
    def widget_count(self, obj):
        return obj.widgets.count()
    widget_count.short_description = _('Widgets')

class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0
    fields = ('title', 'widget_type', 'position_x', 'position_y', 'width', 'height')

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('title', 'dashboard', 'widget_type', 'chart_type', 'position_display', 'size_display', 'last_refreshed')
    list_filter = ('widget_type', 'chart_type', 'dashboard')
    search_fields = ('title', 'dashboard__title', 'data_source')
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('title', 'dashboard', 'widget_type', 'chart_type')
        }),
        (_('Disposition'), {
            'fields': ('position_x', 'position_y', 'width', 'height')
        }),
        (_('Données'), {
            'fields': ('data_source', 'config', 'refresh_rate', 'last_refreshed')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_refreshed')
    
    def position_display(self, obj):
        return f"({obj.position_x}, {obj.position_y})"
    position_display.short_description = _('Position')
    
    def size_display(self, obj):
        return f"{obj.width} × {obj.height}"
    size_display.short_description = _('Taille')
    
    actions = ['refresh_widgets']
    
    def refresh_widgets(self, request, queryset):
        count = 0
        for widget in queryset:
            try:
                widget.refresh_data()
                count += 1
            except Exception as e:
                self.message_user(request, _('Erreur lors du rafraîchissement du widget "{}" : {}').format(widget.title, str(e)), level='ERROR')
        
        self.message_user(request, _('%(count)d widgets ont été rafraîchis avec succès.') % {'count': count})
    refresh_widgets.short_description = _('Rafraîchir les widgets sélectionnés')

@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'metric_type_display', 'unit', 'is_active', 'is_public', 'is_realtime')
    list_filter = ('is_counter', 'is_rate', 'is_gauge', 'is_active', 'is_public', 'is_realtime')
    search_fields = ('name', 'display_name', 'description')
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'display_name', 'description')
        }),
        (_('Type de métrique'), {
            'fields': ('is_counter', 'is_rate', 'is_gauge')
        }),
        (_('Formatage'), {
            'fields': ('unit', 'decimal_places')
        }),
        (_('Calcul'), {
            'fields': ('calculation_method', 'sql_query', 'python_function')
        }),
        (_('Pour les taux'), {
            'fields': ('numerator_metric', 'denominator_metric'),
            'classes': ('collapse',)
        }),
        (_('Alertes'), {
            'fields': ('threshold_warning', 'threshold_critical'),
            'classes': ('collapse',)
        }),
        (_('Configuration'), {
            'fields': ('available_intervals', 'is_active', 'is_public', 'is_realtime')
        }),
    )
    
    def metric_type_display(self, obj):
        types = []
        if obj.is_counter:
            types.append(_('Compteur'))
        if obj.is_rate:
            types.append(_('Taux'))
        if obj.is_gauge:
            types.append(_('Jauge'))
        return ', '.join(types) if types else _('Non défini')
    metric_type_display.short_description = _('Type')
    
    inlines = [
        # MetricValueInline peut être ajouté ici
    ]
    
    actions = ['calculate_metrics']
    
    def calculate_metrics(self, request, queryset):
        count = 0
        for metric in queryset:
            try:
                metric.get_value()  # Calcule la valeur actuelle
                count += 1
            except Exception as e:
                self.message_user(request, _('Erreur lors du calcul de la métrique "{}" : {}').format(metric.name, str(e)), level='ERROR')
        
        self.message_user(request, _('%(count)d métriques ont été calculées avec succès.') % {'count': count})
    calculate_metrics.short_description = _('Calculer les métriques sélectionnées')

@admin.register(MetricValue)
class MetricValueAdmin(admin.ModelAdmin):
    list_display = ('metric', 'value', 'interval', 'timestamp', 'has_dimensions')
    list_filter = ('metric', 'interval', 'timestamp')
    search_fields = ('metric__name', 'metric__display_name')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Métrique et valeur'), {
            'fields': ('metric', 'value', 'timestamp')
        }),
        (_('Intervalle'), {
            'fields': ('interval', 'start_date', 'end_date')
        }),
        (_('Dimensions'), {
            'fields': ('dimensions',),
            'classes': ('collapse',)
        }),
    )
    
    def has_dimensions(self, obj):
        return bool(obj.dimensions)
    has_dimensions.boolean = True
    has_dimensions.short_description = _('Dimensions')

@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'user_display', 'timestamp', 'campaign', 'source', 'medium', 'client_ip')
    list_filter = ('event_name', 'timestamp', 'campaign', 'source', 'medium')
    search_fields = ('event_name', 'user__first_name', 'user__last_name', 'user__email', 'campaign', 'source', 'properties')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Événement'), {
            'fields': ('event_name', 'user', 'timestamp')
        }),
        (_('Propriétés'), {
            'fields': ('properties',)
        }),
        (_('Informations client'), {
            'fields': ('client_ip', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        (_('Attribution'), {
            'fields': ('campaign', 'source', 'medium'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('timestamp', 'event_name', 'user', 'properties', 'client_ip', 'user_agent', 'session_id', 'campaign', 'source', 'medium')
    
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        return _("Utilisateur anonyme")
    user_display.short_description = _('Utilisateur')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False