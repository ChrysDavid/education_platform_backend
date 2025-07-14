from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Avg, Count

from .models import (
    SchoolType, City, School, Department, Program,
    Facility, SchoolContact, SchoolReview, SchoolMedia, SchoolEvent
)


@admin.register(SchoolType)
class SchoolTypeAdmin(admin.ModelAdmin):
    """
    Administration des types d'établissements.
    """
    list_display = ('name', 'slug', 'school_count')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def school_count(self, obj):
        """Affiche le nombre d'établissements de ce type."""
        count = obj.schools.count()
        return count
    school_count.short_description = _("Nombre d'établissements")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """
    Administration des villes.
    """
    list_display = ('name', 'region', 'zip_code', 'school_count', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ['name', 'region', 'zip_code']
    list_editable = ['is_active']
    
    def school_count(self, obj):
        """Affiche le nombre d'établissements dans cette ville."""
        count = obj.schools.count()
        return count
    school_count.short_description = _("Nombre d'établissements")


class DepartmentInline(admin.TabularInline):
    """
    Inline pour ajouter des départements à un établissement.
    """
    model = Department
    extra = 1
    fields = ('name', 'slug', 'head_name', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


class ProgramInline(admin.TabularInline):
    """
    Inline pour ajouter des programmes à un établissement.
    """
    model = Program
    extra = 1
    fields = ('name', 'slug', 'code', 'department', 'level', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


class FacilityInline(admin.TabularInline):
    """
    Inline pour ajouter des équipements à un établissement.
    """
    model = Facility
    extra = 1
    fields = ('name', 'facility_type', 'description', 'quantity', 'is_active')


class SchoolContactInline(admin.TabularInline):
    """
    Inline pour ajouter des contacts à un établissement.
    """
    model = SchoolContact
    extra = 1
    fields = ('name', 'contact_type', 'title', 'phone', 'email', 'is_active')


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """
    Administration des établissements.
    """
    list_display = (
        'name', 'school_type', 'city', 'student_count',
        'founded_year', 'average_rating', 'is_verified', 'is_active'
    )
    list_filter = ('school_type', 'city', 'is_verified', 'is_active')
    search_fields = ['name', 'description', 'address', 'city__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'average_rating', 'display_logo', 'display_cover')
    list_editable = ['is_verified', 'is_active']
    date_hierarchy = 'created_at'
    filter_horizontal = []
    save_on_top = True
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'slug', 'school_type', 'description', 'founded_year')
        }),
        (_('Coordonnées'), {
            'fields': ('address', 'city', 'postal_code', 'phone', 'email', 'website')
        }),
        (_('Médias'), {
            'fields': ('logo', 'display_logo', 'cover_image', 'display_cover')
        }),
        (_('Localisation'), {
            'fields': ('longitude', 'latitude'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('student_count', 'staff_count', 'director_name', 'average_rating')
        }),
        (_('Contact administratif'), {
            'fields': ('admin_contact_name', 'admin_contact_email', 'admin_contact_phone'),
            'classes': ('collapse',)
        }),
        (_('Statut'), {
            'fields': ('is_verified', 'is_active', 'created_at', 'updated_at')
        }),
    )
    
    inlines = [
        DepartmentInline,
        ProgramInline,
        FacilityInline,
        SchoolContactInline,
    ]
    
    def display_logo(self, obj):
        """Affiche une prévisualisation du logo."""
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 200px;" />', obj.logo.url)
        return "-"
    display_logo.short_description = _("Aperçu du logo")
    
    def display_cover(self, obj):
        """Affiche une prévisualisation de l'image de couverture."""
        if obj.cover_image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 300px;" />', obj.cover_image.url)
        return "-"
    display_cover.short_description = _("Aperçu de l'image de couverture")
    
    def average_rating(self, obj):
        """Calcule et affiche la note moyenne de l'établissement."""
        avg = obj.reviews.filter(is_public=True).aggregate(Avg('rating'))['rating__avg']
        if avg is not None:
            return f"{avg:.1f}/5.0"
        return "-"
    average_rating.short_description = _("Note moyenne")
    
    def get_queryset(self, request):
        """Optimise les requêtes avec des prefetch_related."""
        return super().get_queryset(request).select_related(
            'school_type', 'city'
        ).prefetch_related(
            'departments', 'programs', 'facilities'
        ).annotate(
            review_count=Count('reviews', distinct=True)
        )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Administration des départements.
    """
    list_display = ('name', 'school', 'head_name', 'program_count', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ['name', 'description', 'school__name', 'head_name']
    prepopulated_fields = {'slug': ('name',)}
    
    def program_count(self, obj):
        """Affiche le nombre de programmes dans ce département."""
        count = obj.programs.count()
        return count
    program_count.short_description = _("Nombre de programmes")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    """
    Administration des programmes académiques.
    """
    list_display = (
        'name', 'school', 'department', 'code',
        'level', 'duration', 'is_active'
    )
    list_filter = ('school', 'department', 'level', 'is_active')
    search_fields = ['name', 'description', 'code', 'school__name', 'department__name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """
    Administration des équipements.
    """
    list_display = ('name', 'facility_type', 'school', 'quantity', 'is_active')
    list_filter = ('facility_type', 'school', 'is_active')
    search_fields = ['name', 'description', 'school__name']


@admin.register(SchoolContact)
class SchoolContactAdmin(admin.ModelAdmin):
    """
    Administration des contacts des établissements.
    """
    list_display = ('name', 'title', 'contact_type', 'school', 'email', 'phone', 'is_active')
    list_filter = ('contact_type', 'school', 'is_active')
    search_fields = ['name', 'email', 'phone', 'title', 'school__name']


@admin.register(SchoolReview)
class SchoolReviewAdmin(admin.ModelAdmin):
    """
    Administration des évaluations des établissements.
    """
    list_display = ('school', 'user', 'rating', 'title', 'created_at', 'is_verified', 'is_public')
    list_filter = ('school', 'rating', 'is_verified', 'is_public', 'created_at')
    search_fields = ['title', 'comment', 'school__name', 'user__email']
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ['is_verified', 'is_public']
    date_hierarchy = 'created_at'
    
    actions = ['verify_reviews', 'make_public', 'make_private']
    
    def verify_reviews(self, request, queryset):
        """Action pour vérifier plusieurs évaluations à la fois."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, _("{} évaluations ont été marquées comme vérifiées.").format(updated))
    verify_reviews.short_description = _("Marquer les évaluations sélectionnées comme vérifiées")
    
    def make_public(self, request, queryset):
        """Action pour rendre plusieurs évaluations publiques."""
        updated = queryset.update(is_public=True)
        self.message_user(request, _("{} évaluations ont été rendues publiques.").format(updated))
    make_public.short_description = _("Rendre les évaluations sélectionnées publiques")
    
    def make_private(self, request, queryset):
        """Action pour rendre plusieurs évaluations privées."""
        updated = queryset.update(is_public=False)
        self.message_user(request, _("{} évaluations ont été rendues privées.").format(updated))
    make_private.short_description = _("Rendre les évaluations sélectionnées privées")


@admin.register(SchoolMedia)
class SchoolMediaAdmin(admin.ModelAdmin):
    """
    Administration des médias des établissements.
    """
    list_display = ('title', 'school', 'media_type', 'created_at', 'is_public')
    list_filter = ('school', 'media_type', 'is_public', 'created_at')
    search_fields = ['title', 'description', 'school__name']
    readonly_fields = ('created_at', 'display_media')
    list_editable = ['is_public']
    date_hierarchy = 'created_at'
    
    def display_media(self, obj):
        """Affiche une prévisualisation du média."""
        if obj.media_type == 'photo' and obj.file:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 400px;" />', obj.file.url)
        elif obj.media_type == 'video' and obj.file:
            return format_html('<a href="{}" target="_blank">Voir la vidéo</a>', obj.file.url)
        elif obj.media_type == 'document' and obj.file:
            return format_html('<a href="{}" target="_blank">Voir le document</a>', obj.file.url)
        return "-"
    display_media.short_description = _("Aperçu du média")


@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):
    """
    Administration des événements des établissements.
    """
    list_display = ('title', 'school', 'start_date', 'end_date', 'is_past', 'is_ongoing', 'is_public')
    list_filter = ('school', 'start_date', 'is_public')
    search_fields = ['title', 'description', 'location', 'school__name']
    readonly_fields = ('created_at', 'updated_at', 'is_past', 'is_ongoing', 'display_image')
    list_editable = ['is_public']
    date_hierarchy = 'start_date'
    
    def is_past(self, obj):
        """Indique si l'événement est passé."""
        return obj.is_past
    is_past.boolean = True
    is_past.short_description = _("Passé")
    
    def is_ongoing(self, obj):
        """Indique si l'événement est en cours."""
        return obj.is_ongoing
    is_ongoing.boolean = True
    is_ongoing.short_description = _("En cours")
    
    def display_image(self, obj):
        """Affiche une prévisualisation de l'image de l'événement."""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 150px; max-width: 300px;" />', obj.image.url)
        return "-"
    display_image.short_description = _("Aperçu de l'image")