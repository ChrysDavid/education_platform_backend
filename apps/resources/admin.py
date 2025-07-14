from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ResourceCategory, Resource, ResourceReview, ResourceComment,
    ResourceCollection, CollectionResource, ResourceLike
)


class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'order', 'is_active', 'resource_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']


class ResourceReviewInline(admin.TabularInline):
    model = ResourceReview
    extra = 0
    readonly_fields = ['user', 'created_at']


class ResourceCommentInline(admin.TabularInline):
    model = ResourceComment
    extra = 0
    readonly_fields = ['user', 'created_at']
    fields = ['user', 'content', 'parent', 'is_public', 'created_at']


class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'resource_type', 'created_by', 'access_level',
        'view_count', 'like_count', 'is_approved', 'is_featured', 'is_active'
    ]
    list_filter = [
        'resource_type', 'access_level', 'categories',
        'is_approved', 'is_featured', 'is_active', 'created_at'
    ]
    search_fields = ['title', 'description', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'download_count', 'like_count', 'created_at', 'updated_at']
    filter_horizontal = ['categories']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('title', 'slug', 'description', 'resource_type', 'access_level')
        }),
        (_('Contenu'), {
            'fields': ('file', 'external_url', 'thumbnail')
        }),
        (_('Catégorisation'), {
            'fields': ('categories', 'tags')
        }),
        (_('Métadonnées'), {
            'fields': ('language', 'duration', 'author_name', 'source', 'license')
        }),
        (_('Statistiques'), {
            'fields': ('view_count', 'download_count', 'like_count')
        }),
        (_('État'), {
            'fields': ('is_approved', 'is_featured', 'is_active')
        }),
        (_('Informations système'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ResourceReviewInline, ResourceCommentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouvel objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ResourceReviewAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'rating', 'created_at', 'is_public']
    list_filter = ['rating', 'is_public', 'created_at']
    search_fields = ['comment', 'user__email', 'resource__title']
    readonly_fields = ['created_at', 'updated_at']


class ResourceCommentAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'parent', 'created_at', 'is_edited', 'is_public']
    list_filter = ['is_edited', 'is_public', 'created_at']
    search_fields = ['content', 'user__email', 'resource__title']
    readonly_fields = ['created_at', 'updated_at', 'is_edited']


class CollectionResourceInline(admin.TabularInline):
    model = CollectionResource
    extra = 1
    fields = ['resource', 'order']


class ResourceCollectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'resource_count', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'description', 'created_by__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [CollectionResourceInline]
    
    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = _('Nombre de ressources')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est un nouvel objet
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(ResourceCategory, ResourceCategoryAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(ResourceReview, ResourceReviewAdmin)
admin.site.register(ResourceComment, ResourceCommentAdmin)
admin.site.register(ResourceCollection, ResourceCollectionAdmin)