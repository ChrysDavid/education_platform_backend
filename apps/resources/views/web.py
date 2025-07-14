from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.core.paginator import Paginator

from apps.accounts import models
from ..models import (
    ResourceCategory, Resource, ResourceReview, ResourceComment, 
    ResourceCollection, CollectionResource, ResourceLike
)
from ..forms import (
    ResourceCategoryForm, ResourceForm, ResourceReviewForm,
    ResourceCommentForm, ResourceCollectionForm, ResourceSearchForm
)
from ..serializers.web import (
    WebResourceCategorySerializer, WebResourceSerializer, WebResourceDetailSerializer,
    WebResourceReviewSerializer, WebResourceCommentSerializer, WebResourceCollectionSerializer
)



class ResourceCategoryListView(ListView):
    """
    Vue pour afficher la liste des catégories de ressources.
    """
    model = ResourceCategory
    template_name = 'resources/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return ResourceCategory.objects.filter(
            is_active=True, parent=None
        ).prefetch_related('subcategories')


class ResourceCategoryDetailView(DetailView):
    """
    Vue pour afficher les ressources d'une catégorie.
    """
    model = ResourceCategory
    template_name = 'resources/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        
        # Ressources de cette catégorie et de ses sous-catégories
        category_ids = [category.id]
        subcategories = category.subcategories.filter(is_active=True)
        category_ids.extend(subcategories.values_list('id', flat=True))
        
        resources = Resource.objects.filter(
            categories__id__in=category_ids,
            is_active=True
        ).distinct().select_related('created_by').order_by('-created_at')
        
        # Paginer les résultats
        paginator = Paginator(resources, 12)
        page = self.request.GET.get('page')
        resources = paginator.get_page(page)
        
        context['resources'] = resources
        context['subcategories'] = subcategories
        return context


class ResourceCollectionListView(ListView):
    """
    Vue pour afficher la liste des collections de ressources.
    """
    model = ResourceCollection
    template_name = 'resources/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = ResourceCollection.objects.filter(is_public=True).select_related('created_by')
        
        # Si filtrage par utilisateur
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        
        return queryset.order_by('-created_at')


class ResourceCollectionDetailView(DetailView):
    """
    Vue pour afficher les détails d'une collection.
    """
    model = ResourceCollection
    template_name = 'resources/collection_detail.html'
    context_object_name = 'collection'
    
    def get_queryset(self):
        queryset = ResourceCollection.objects.select_related('created_by')
        
        # Si l'utilisateur n'est pas connecté, n'afficher que les collections publiques
        if not self.request.user.is_authenticated:
            return queryset.filter(is_public=True)
        
        # Si l'utilisateur est connecté, afficher ses collections privées aussi
        return queryset.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = self.object
        
        # Récupérer les ressources de la collection avec leur ordre
        resources = Resource.objects.filter(
            collections=collection,
            is_active=True
        ).select_related('created_by')
        
        # Tri par ordre dans la collection
        resources = resources.annotate(
            collection_order=models.Min('collectionresource__order')
        ).order_by('collection_order')
        
        context['resources'] = resources
        return context


class ResourceCollectionCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer une nouvelle collection.
    """
    model = ResourceCollection
    form_class = ResourceCollectionForm
    template_name = 'resources/collection_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La collection a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:collection_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Créer une collection")
        return context


class ResourceCollectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier une collection.
    """
    model = ResourceCollection
    form_class = ResourceCollectionForm
    template_name = 'resources/collection_form.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est le créateur de la collection."""
        collection = self.get_object()
        return self.request.user == collection.created_by
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La collection a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:collection_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier la collection")
        context['is_update'] = True
        return context


class ResourceCollectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer une collection.
    """
    model = ResourceCollection
    template_name = 'resources/collection_confirm_delete.html'
    success_url = reverse_lazy('resources:collection_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est le créateur de la collection."""
        collection = self.get_object()
        return self.request.user == collection.created_by or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("La collection a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)
    

class ResourceListView(ListView):
    """
    Vue pour afficher la liste des ressources pédagogiques.
    """
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Resource.objects.filter(is_active=True).select_related('created_by')
        
        # Filtrage par catégorie si spécifié
        category_slug = self.request.GET.get('category')
        if category_slug:
            category = get_object_or_404(ResourceCategory, slug=category_slug, is_active=True)
            queryset = queryset.filter(categories=category)
        
        # Filtrage par type de ressource
        resource_type = self.request.GET.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filtrage par utilisateur
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(created_by_id=user_id)
        
        # Tri des résultats
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['title', '-title', 'created_at', '-created_at', 'view_count', 'like_count']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les catégories actives au contexte
        context['categories'] = ResourceCategory.objects.filter(is_active=True, parent=None)
        
        # Ajouter le formulaire de recherche
        context['search_form'] = ResourceSearchForm(self.request.GET or None)
        
        # Ajouter les paramètres de filtrage actuels
        context['current_category'] = self.request.GET.get('category')
        context['current_type'] = self.request.GET.get('type')
        context['current_user'] = self.request.GET.get('user')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        return context