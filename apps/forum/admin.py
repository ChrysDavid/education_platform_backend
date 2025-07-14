from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Category, Topic, Post, PostReaction, 
    TopicSubscription, TopicView, PostReport
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'topic_count', 'post_count', 'requires_verification', 'is_active', 'order']
    list_filter = ['is_active', 'requires_verification']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['authorized_groups']
    
    def topic_count(self, obj):
        return obj.topics.count()
    topic_count.short_description = _('Sujets')
    
    def post_count(self, obj):
        from django.db.models import Count
        return Post.objects.filter(topic__category=obj).count()
    post_count.short_description = _('Messages')


class PostInline(admin.TabularInline):
    model = Post
    fields = ['author', 'content', 'created_at', 'is_hidden', 'is_edited']
    readonly_fields = ['author', 'created_at', 'is_edited']
    extra = 0
    max_num = 10


class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'created_at', 'last_activity_at', 'view_count', 'post_count']
    list_filter = ['status', 'category', 'created_at', 'last_activity_at']
    search_fields = ['title', 'author__first_name', 'author__last_name', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'last_activity_at', 'view_count']
    inlines = [PostInline]
    
    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = _('Messages')


class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic_link', 'author', 'content_preview', 'created_at', 'is_hidden', 'is_edited', 'is_solution']
    list_filter = ['is_hidden', 'is_edited', 'is_solution', 'created_at']
    search_fields = ['content', 'author__first_name', 'author__last_name', 'author__email', 'topic__title']
    readonly_fields = ['created_at', 'updated_at']
    
    def topic_link(self, obj):
        return format_html('<a href="{}">{}</a>', obj.topic.get_absolute_url(), obj.topic.title)
    topic_link.short_description = _('Sujet')
    
    def content_preview(self, obj):
        if len(obj.content) > 100:
            return obj.content[:97] + '...'
        return obj.content
    content_preview.short_description = _('Contenu')


class PostReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'reaction', 'created_at']
    list_filter = ['reaction', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'post__content']


class TopicSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'notify_on_new_post', 'created_at']
    list_filter = ['notify_on_new_post', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'topic__title']


class TopicViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'topic', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'topic__title']


class PostReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'post', 'status', 'created_at', 'handled_by']
    list_filter = ['status', 'created_at']
    search_fields = ['reporter__first_name', 'reporter__last_name', 'reporter__email', 'post__content', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        # Si le statut est modifié, définir l'utilisateur qui l'a traité
        if change and 'status' in form.changed_data:
            obj.handled_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Category, CategoryAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(PostReaction, PostReactionAdmin)
admin.site.register(TopicSubscription, TopicSubscriptionAdmin)
admin.site.register(TopicView, TopicViewAdmin)
admin.site.register(PostReport, PostReportAdmin)