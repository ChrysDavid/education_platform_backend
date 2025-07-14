from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q, Avg, Count, Prefetch
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.core.cache import cache

from rest_framework import generics, permissions, filters
from rest_framework.response import Response

from apps.accounts import models
from ..models import (
    ResourceCategory, Resource, ResourceReview, ResourceComment, 
    ResourceCollection, CollectionResource, ResourceLike
)
from ..forms import (
    ResourceCategoryForm, ResourceForm, ResourceReviewForm,
    ResourceCommentForm, ResourceCollectionForm, ResourceSearchForm
)
from ..serializers.mobile import (
    MobileResourceCategorySerializer, MobileResourceSerializer, MobileResourceDetailSerializer,
    MobileResourceReviewSerializer, MobileResourceCommentSerializer, MobileResourceCollectionSerializer
)
from ..permissions import IsResourceOwnerOrAdmin, CanReviewResource


class ResourceListView(ListView):
    """
    Vue pour afficher la liste des ressources.
    """
    model = Resource
    template_name = 'resources/resource_list.html'
    context_object_name = 'resources'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Filtre les ressources selon les paramètres de recherche.
        """
        queryset = Resource.objects.filter(is_active=True)
        form = ResourceSearchForm(self.request.GET)
        
        if form.is_valid():
            # Filtres de recherche
            search = form.cleaned_data.get('search')
            categories = form.cleaned_data.get('categories')
            resource_type = form.cleaned_data.get('resource_type')
            language = form.cleaned_data.get('language')
            min_rating = form.cleaned_data.get('min_rating')
            is_approved = form.cleaned_data.get('is_approved')
            sort_by = form.cleaned_data.get('sort_by')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(tags__icontains=search)
                )
            
            if categories:
                queryset = queryset.filter(categories__in=categories).distinct()
            
            if resource_type:
                queryset = queryset.filter(resource_type=resource_type)
            
            if language:
                queryset = queryset.filter(language=language)
            
            if min_rating:
                # Sous-requête pour filtrer par note moyenne
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating')
                ).filter(avg_rating__gte=float(min_rating))
            
            if is_approved:
                queryset = queryset.filter(is_approved=True)
            
            # Gestion du tri
            if sort_by:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-created_at')
        else:
            # Par défaut : ressources les plus récentes
            queryset = queryset.order_by('-created_at')
        
        # Optimisation des requêtes
        return queryset.select_related('created_by').prefetch_related('categories')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ResourceSearchForm(self.request.GET)
        context['categories'] = ResourceCategory.objects.filter(is_active=True)
        return context


class ResourceDetailView(DetailView):
    """
    Vue pour afficher les détails d'une ressource.
    """
    model = Resource
    template_name = 'resources/resource_detail.html'
    context_object_name = 'resource'
    
    def get_queryset(self):
        return Resource.objects.filter(is_active=True).select_related(
            'created_by'
        ).prefetch_related(
            'categories',
            Prefetch('reviews', queryset=ResourceReview.objects.filter(is_public=True).select_related('user')),
            Prefetch('comments', queryset=ResourceComment.objects.filter(is_public=True, parent=None).select_related('user'))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resource = self.object
        
        # Incrémenter le compteur de vues
        resource.increment_view_count()
        
        # Vérifier si l'utilisateur a aimé cette ressource
        if self.request.user.is_authenticated:
            context['user_has_liked'] = ResourceLike.objects.filter(
                resource=resource, user=self.request.user
            ).exists()
            
            # Vérifier si l'utilisateur a évalué cette ressource
            user_review = ResourceReview.objects.filter(
                resource=resource, user=self.request.user
            ).first()
            
            if user_review:
                context['user_review'] = user_review
                context['review_form'] = ResourceReviewForm(instance=user_review)
            else:
                context['review_form'] = ResourceReviewForm()
            
            # Formulaire de commentaire
            context['comment_form'] = ResourceCommentForm()
        
        # Ressources similaires
        similar_resources = Resource.objects.filter(
            categories__in=resource.categories.all(),
            is_active=True,
            is_approved=True
        ).exclude(pk=resource.pk).distinct()[:6]
        
        context['similar_resources'] = similar_resources
        
        # Commentaires de premier niveau
        context['comments'] = ResourceComment.objects.filter(
            resource=resource,
            parent=None,
            is_public=True
        ).select_related('user').prefetch_related('replies')
        
        # Collections contenant cette ressource
        context['collections'] = ResourceCollection.objects.filter(
            resources=resource,
            is_public=True
        )[:5]
        
        return context


class ResourceCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer une nouvelle ressource.
    """
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La ressource a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Ajouter une ressource")
        return context


class ResourceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier une ressource existante.
    """
    model = Resource
    form_class = ResourceForm
    template_name = 'resources/resource_form.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est le créateur de la ressource ou un administrateur."""
        resource = self.get_object()
        return self.request.user == resource.created_by or self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La ressource a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.object.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Modifier la ressource")
        context['is_update'] = True
        return context


class ResourceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer une ressource.
    """
    model = Resource
    template_name = 'resources/resource_confirm_delete.html'
    success_url = reverse_lazy('resources:resource_list')
    
    def test_func(self):
        """Vérifie que l'utilisateur est le créateur de la ressource ou un administrateur."""
        resource = self.get_object()
        return self.request.user == resource.created_by or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("La ressource a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


@method_decorator(require_POST, name='dispatch')
class ResourceLikeView(LoginRequiredMixin, FormView):
    """
    Vue pour aimer/ne plus aimer une ressource.
    """
    http_method_names = ['post']
    
    def form_valid(self, request, *args, **kwargs):
        resource = get_object_or_404(Resource, pk=self.kwargs['pk'])
        
        # Ajouter/retirer un j'aime
        is_liked = resource.toggle_like(self.request.user)
        
        # Répondre en JSON pour les requêtes AJAX
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'liked': is_liked,
                'likes': resource.like_count
            })
        
        # Redirection normale
        return redirect('resources:resource_detail', slug=resource.slug)


class ResourceReviewCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer une évaluation sur une ressource.
    """
    model = ResourceReview
    form_class = ResourceReviewForm
    template_name = 'resources/review_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.resource = get_object_or_404(Resource, slug=self.kwargs['slug'])
        
        # Vérifier si l'utilisateur a déjà évalué cette ressource
        existing_review = ResourceReview.objects.filter(
            resource=self.resource, user=request.user
        ).first()
        
        if existing_review:
            return redirect('resources:edit_review', pk=existing_review.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['resource'] = self.resource
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre évaluation a été ajoutée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.resource.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource'] = self.resource
        return context


class ResourceReviewUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier une évaluation.
    """
    model = ResourceReview
    form_class = ResourceReviewForm
    template_name = 'resources/review_form.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est l'auteur de l'évaluation."""
        review = self.get_object()
        return self.request.user == review.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['resource'] = self.get_object().resource
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre évaluation a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.get_object().resource.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource'] = self.get_object().resource
        context['is_update'] = True
        return context


class ResourceReviewDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer une évaluation.
    """
    model = ResourceReview
    template_name = 'resources/review_confirm_delete.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est l'auteur de l'évaluation ou un administrateur."""
        review = self.get_object()
        return self.request.user == review.user or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.get_object().resource.slug})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Votre évaluation a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


class ResourceCommentCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour ajouter un commentaire à une ressource.
    """
    model = ResourceComment
    form_class = ResourceCommentForm
    template_name = 'resources/comment_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.resource = get_object_or_404(Resource, slug=self.kwargs['slug'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['resource'] = self.resource
        
        # Si c'est une réponse à un commentaire
        parent_id = self.request.GET.get('parent_id')
        if parent_id:
            parent = get_object_or_404(ResourceComment, pk=parent_id, resource=self.resource)
            kwargs['initial'] = {'parent': parent.pk}
        
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre commentaire a été ajouté avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.resource.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource'] = self.resource
        
        # Si c'est une réponse
        parent_id = self.request.GET.get('parent_id')
        if parent_id:
            parent = get_object_or_404(ResourceComment, pk=parent_id)
            context['parent_comment'] = parent
            context['is_reply'] = True
        
        return context


class ResourceCommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier un commentaire.
    """
    model = ResourceComment
    form_class = ResourceCommentForm
    template_name = 'resources/comment_form.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est l'auteur du commentaire."""
        comment = self.get_object()
        return self.request.user == comment.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['resource'] = self.get_object().resource
        return kwargs
    
    def form_valid(self, form):
        # Marquer le commentaire comme édité
        form.instance.is_edited = True
        messages.success(self.request, _("Votre commentaire a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.get_object().resource.slug})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['resource'] = self.get_object().resource
        context['is_update'] = True
        return context


class ResourceCommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer un commentaire.
    """
    model = ResourceComment
    template_name = 'resources/comment_confirm_delete.html'
    
    def test_func(self):
        """Vérifie que l'utilisateur est l'auteur du commentaire ou un administrateur."""
        comment = self.get_object()
        return self.request.user == comment.user or self.request.user.is_staff
    
    def get_success_url(self):
        return reverse('resources:resource_detail', kwargs={'slug': self.get_object().resource.slug})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Votre commentaire a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


class ResourceCategoryAPIListView(generics.ListAPIView):
    """
    API pour lister les catégories de ressources.
    """
    queryset = ResourceCategory.objects.filter(is_active=True)
    serializer_class = MobileResourceCategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ResourceAPIListView(generics.ListAPIView):
    """
    API pour lister les ressources.
    """
    serializer_class = MobileResourceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['created_at', 'view_count', 'like_count', 'title']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Resource.objects.filter(is_active=True).select_related('created_by')
        
        # Filtre par catégorie
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(categories__slug=category)
        
        # Filtre par type
        resource_type = self.request.query_params.get('type')
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        
        # Filtre par niveau d'accès
        access_level = self.request.query_params.get('access_level')
        if access_level:
            queryset = queryset.filter(access_level=access_level)
        
        # Filtre par approbation
        is_approved = self.request.query_params.get('approved')
        if is_approved:
            queryset = queryset.filter(is_approved=True)
        
        return queryset


class ResourceAPIDetailView(generics.RetrieveAPIView):
    """
    API pour récupérer les détails d'une ressource.
    """
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = MobileResourceDetailSerializer
    lookup_field = 'slug'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class ResourceReviewAPIListCreateView(generics.ListCreateAPIView):
    """
    API pour lister et créer des évaluations pour une ressource.
    """
    serializer_class = MobileResourceReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        resource = get_object_or_404(Resource, slug=self.kwargs['slug'])
        return ResourceReview.objects.filter(
            resource=resource, is_public=True
        ).select_related('user')
    
    def perform_create(self, serializer):
        resource = get_object_or_404(Resource, slug=self.kwargs['slug'])
        serializer.save(user=self.request.user, resource=resource)