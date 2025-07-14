from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from ..models import Topic, Post
from ..forms import TopicForm, PostForm, TopicModerationForm, PostModerationForm


class TopicUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier un sujet.
    """
    model = Topic
    form_class = TopicForm
    template_name = 'forum/topic_form.html'
    
    def get_object(self):
        # Récupérer le sujet par le slug de la catégorie et le slug du sujet
        return get_object_or_404(
            Topic,
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['topic_slug']
        )
    
    def test_func(self):
        # Vérifier que l'utilisateur est l'auteur du sujet ou un modérateur
        topic = self.get_object()
        return self.request.user == topic.author or self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre sujet a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Récupérer le contenu du premier message pour le formulaire
        topic = self.get_object()
        first_post = topic.posts.order_by('created_at').first()
        if first_post:
            initial['content'] = first_post.content
        
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Mettre à jour le contenu du premier message
        topic = self.object
        first_post = topic.posts.order_by('created_at').first()
        if first_post:
            first_post.content = form.cleaned_data['content']
            first_post.is_edited = True
            first_post.save()
        
        messages.success(self.request, _("Le sujet a été mis à jour avec succès."))
        return response


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier un message.
    """
    model = Post
    form_class = PostForm
    template_name = 'forum/post_form.html'
    pk_url_kwarg = 'post_id'
    
    def test_func(self):
        # Vérifier que l'utilisateur est l'auteur du message ou un modérateur
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['topic'] = self.get_object().topic
        return kwargs
    
    def form_valid(self, form):
        # Marquer le message comme édité
        form.instance.is_edited = True
        
        messages.success(self.request, _("Votre message a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = self.object.topic
        context['is_update'] = True
        return context


@login_required
@require_POST
@csrf_protect
def moderate_topic(request, category_slug, topic_slug):
    """
    Vue pour modérer un sujet (fermer, épingler, etc.).
    """
    topic = get_object_or_404(Topic, category__slug=category_slug, slug=topic_slug)
    
    # Vérifier les permissions de modération
    if not request.user.is_staff and request.user != topic.author:
        return HttpResponseForbidden()
    
    form = TopicModerationForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        moderator_note = form.cleaned_data['moderator_note']
        
        # Effectuer l'action demandée
        if action == 'close':
            topic.status = 'closed'
            message = _("Le sujet a été fermé.")
        elif action == 'open':
            topic.status = 'open'
            message = _("Le sujet a été rouvert.")
        elif action == 'pin':
            topic.status = 'pinned'
            message = _("Le sujet a été épinglé.")
        elif action == 'unpin':
            topic.status = 'open'
            message = _("Le sujet a été désépinglé.")
        elif action == 'hide':
            topic.status = 'hidden'
            message = _("Le sujet a été masqué.")
        elif action == 'unhide':
            topic.status = 'open'
            message = _("Le sujet est maintenant visible.")
        elif action == 'move':
            target_category = form.cleaned_data['target_category']
            if target_category:
                # Vérifier si un sujet avec le même slug existe déjà dans la catégorie cible
                if Topic.objects.filter(category=target_category, slug=topic.slug).exists():
                    # Générer un nouveau slug unique
                    base_slug = topic.slug
                    counter = 1
                    new_slug = f"{base_slug}-{counter}"
                    
                    while Topic.objects.filter(category=target_category, slug=new_slug).exists():
                        counter += 1
                        new_slug = f"{base_slug}-{counter}"
                    
                    topic.slug = new_slug
                
                old_category = topic.category
                topic.category = target_category
                message = _("Le sujet a été déplacé de '{0}' vers '{1}'.").format(
                    old_category.name, target_category.name
                )
            else:
                messages.error(request, _("Vous devez sélectionner une catégorie cible."))
                return redirect('forum:topic_detail', category_slug=category_slug, topic_slug=topic_slug)
        
        topic.save()
        
        # Ajouter un message système si une note de modération est fournie
        if moderator_note:
            system_message = _(f"[Modération] {request.user.get_full_name()}: {moderator_note}")
            Post.objects.create(
                topic=topic,
                author=None,  # Message système
                content=system_message,
                message_type='system'
            )
        
        messages.success(request, message)
    else:
        messages.error(request, _("Une erreur est survenue lors de la modération du sujet."))
    
    # Rediriger en fonction de l'action (notamment pour le déplacement)
    return redirect('forum:topic_detail', category_slug=topic.category.slug, topic_slug=topic.slug)


@login_required
@require_POST
@csrf_protect
def moderate_post(request, post_id):
    """
    Vue pour modérer un message (masquer, marquer comme solution, etc.).
    """
    post = get_object_or_404(Post, pk=post_id)
    
    # Vérifier les permissions de modération
    if not request.user.is_staff and request.user != post.topic.author:
        return HttpResponseForbidden()
    
    form = PostModerationForm(request.POST)
    
    if form.is_valid():
        action = form.cleaned_data['action']
        moderator_note = form.cleaned_data['moderator_note']
        
        # Effectuer l'action demandée
        if action == 'hide':
            post.is_hidden = True
            message = _("Le message a été masqué.")
        elif action == 'unhide':
            post.is_hidden = False
            message = _("Le message est maintenant visible.")
        elif action == 'mark_solution':
            post.mark_as_solution()
            message = _("Le message a été marqué comme solution.")
        elif action == 'unmark_solution':
            post.is_solution = False
            message = _("Le message n'est plus marqué comme solution.")
        
        post.save()
        
        # Ajouter un message système si une note de modération est fournie
        if moderator_note:
            system_message = _(f"[Modération] {request.user.get_full_name()}: {moderator_note}")
            Post.objects.create(
                topic=post.topic,
                author=None,  # Message système
                content=system_message,
                message_type='system'
            )
        
        messages.success(request, message)
    else:
        messages.error(request, _("Une erreur est survenue lors de la modération du message."))
    
    return redirect(post.get_absolute_url())