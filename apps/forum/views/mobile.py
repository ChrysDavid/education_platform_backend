from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Max, Prefetch
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator

from ..models import (
    Category, Topic, Post, PostReaction, 
    TopicSubscription, TopicView, PostReport
)
from ..forms import (
    CategoryForm, TopicForm, PostForm, TopicModerationForm, TopicSubscriptionForm,
    PostReportForm, PostReactionForm
)


class ForumHomepageView(ListView):
    """
    Vue pour la page d'accueil du forum, affichant toutes les catégories.
    """
    model = Category
    template_name = 'forum/index.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Filtrer selon les permissions de groupe si l'utilisateur est connecté
        if self.request.user.is_authenticated:
            # Les administrateurs voient toutes les catégories
            if self.request.user.is_staff:
                pass
            else:
                # Filtrer les catégories restreintes
                restricted_categories = queryset.filter(authorized_groups__isnull=False)
                user_groups = self.request.user.groups.all()
                
                # Pour chaque catégorie restreinte, vérifier si l'utilisateur a accès
                restricted_ids_to_exclude = []
                for category in restricted_categories:
                    category_groups = category.authorized_groups.all()
                    if not any(group in user_groups for group in category_groups):
                        restricted_ids_to_exclude.append(category.id)
                
                queryset = queryset.exclude(id__in=restricted_ids_to_exclude)
        else:
            # Les utilisateurs non connectés ne voient que les catégories sans restriction
            queryset = queryset.filter(authorized_groups__isnull=True)
        
        # Optimiser les requêtes pour les statistiques et derniers messages
        queryset = queryset.prefetch_related(
            Prefetch('topics', queryset=Topic.objects.filter(status__in=['open', 'pinned']))
        ).annotate(
            topic_count=Count('topics', filter=Q(topics__status__in=['open', 'pinned'])),
            post_count=Count('topics__posts', filter=Q(topics__status__in=['open', 'pinned']))
        ).order_by('order', 'name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les derniers messages pour chaque catégorie
        for category in context['categories']:
            category.last_post = Post.objects.filter(
                topic__category=category,
                topic__status__in=['open', 'pinned']
            ).order_by('-created_at').first()
        
        # Ajouter les sujets actifs
        context['active_topics'] = Topic.objects.filter(
            status__in=['open', 'pinned']
        ).select_related('category', 'author').order_by('-last_activity_at')[:10]
        
        # Ajouter les statistiques globales
        context['total_topics'] = Topic.objects.filter(status__in=['open', 'pinned']).count()
        context['total_posts'] = Post.objects.filter(topic__status__in=['open', 'pinned']).count()
        
        return context


class CategoryDetailView(DetailView):
    """
    Vue pour afficher le détail d'une catégorie et ses sujets.
    """
    model = Category
    template_name = 'forum/category_detail.html'
    context_object_name = 'category'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions d'accès à la catégorie
        category = self.get_object()
        
        if not category.is_active:
            messages.error(request, _("Cette catégorie n'est pas active."))
            return redirect('forum:index')
        
        if category.authorized_groups.exists() and request.user.is_authenticated:
            # Vérifier si l'utilisateur appartient à au moins un groupe autorisé
            user_groups = request.user.groups.all()
            if not any(group in user_groups for group in category.authorized_groups.all()):
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder à cette catégorie."))
                return redirect('forum:index')
        elif category.authorized_groups.exists() and not request.user.is_authenticated:
            messages.error(request, _("Vous devez vous connecter pour accéder à cette catégorie."))
            return redirect('forum:index')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        
        # Récupérer les sujets épinglés
        pinned_topics = Topic.objects.filter(
            category=category,
            status='pinned'
        ).select_related('author').annotate(
            post_count=Count('posts'),
            last_post_date=Max('posts__created_at')
        ).order_by('-last_activity_at')
        
        # Récupérer les sujets normaux avec pagination
        regular_topics = Topic.objects.filter(
            category=category,
            status='open'
        ).select_related('author').annotate(
            post_count=Count('posts'),
            last_post_date=Max('posts__created_at')
        ).order_by('-last_activity_at')
        
        # Paginer les sujets normaux
        paginator = Paginator(regular_topics, 20)  # 20 sujets par page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['pinned_topics'] = pinned_topics
        context['page_obj'] = page_obj
        
        # Ajouter les métadonnées des sujets
        for topic in list(pinned_topics) + list(page_obj.object_list):
            # Dernier message du sujet
            topic.last_post = Post.objects.filter(
                topic=topic
            ).order_by('-created_at').first()
            
            # Vérifier si le sujet a été lu par l'utilisateur
            if self.request.user.is_authenticated:
                topic.is_read = TopicView.objects.filter(
                    topic=topic,
                    user=self.request.user
                ).exists()
            else:
                topic.is_read = False
        
        # Ajouter le formulaire de création de sujet si l'utilisateur est connecté
        if self.request.user.is_authenticated:
            context['topic_form'] = TopicForm(user=self.request.user, category=category)
        
        return context


class TopicDetailView(DetailView):
    """
    Vue pour afficher un sujet et ses messages.
    """
    model = Topic
    template_name = 'forum/topic_detail.html'
    context_object_name = 'topic'
    
    def get_object(self):
        # Récupérer le sujet par le slug de la catégorie et le slug du sujet
        return get_object_or_404(
            Topic,
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['topic_slug']
        )
    
    def dispatch(self, request, *args, **kwargs):
        topic = self.get_object()
        
        # Vérifier si le sujet est caché
        if topic.status == 'hidden' and not request.user.is_staff:
            messages.error(request, _("Ce sujet n'est pas accessible."))
            return redirect('forum:category_detail', slug=topic.category.slug)
        
        # Vérifier les permissions d'accès à la catégorie
        category = topic.category
        
        if not category.is_active:
            messages.error(request, _("Cette catégorie n'est pas active."))
            return redirect('forum:index')
        
        if category.authorized_groups.exists() and request.user.is_authenticated:
            # Vérifier si l'utilisateur appartient à au moins un groupe autorisé
            user_groups = request.user.groups.all()
            if not any(group in user_groups for group in category.authorized_groups.all()):
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder à cette catégorie."))
                return redirect('forum:index')
        elif category.authorized_groups.exists() and not request.user.is_authenticated:
            messages.error(request, _("Vous devez vous connecter pour accéder à cette catégorie."))
            return redirect('forum:index')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        topic = self.object
        
        # Incrémenter le compteur de vues
        topic.increment_view_count()
        
        # Enregistrer la vue de l'utilisateur s'il est connecté
        if request.user.is_authenticated:
            TopicView.objects.update_or_create(
                topic=topic,
                user=request.user,
                defaults={'viewed_at': timezone.now()}
            )
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object
        
        # Récupérer les messages avec pagination
        posts = Post.objects.filter(
            topic=topic
        ).select_related('author').prefetch_related(
            'reactions'
        ).order_by('created_at')
        
        # Paginer les messages
        paginator = Paginator(posts, 20)  # 20 messages par page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['page_obj'] = page_obj
        
        # Vérifier si l'utilisateur est abonné au sujet
        if self.request.user.is_authenticated:
            context['is_subscribed'] = TopicSubscription.objects.filter(
                topic=topic,
                user=self.request.user
            ).exists()
        
        # Ajouter le formulaire de réponse si l'utilisateur est connecté et si le sujet n'est pas fermé
        if self.request.user.is_authenticated and topic.status != 'closed':
            context['post_form'] = PostForm(user=self.request.user, topic=topic)
        
        # Ajouter le formulaire de modération pour les modérateurs
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user == topic.author):
            context['topic_moderation_form'] = TopicModerationForm()
        
        return context


class TopicCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer un nouveau sujet.
    """
    model = Topic
    form_class = TopicForm
    template_name = 'forum/topic_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.category = None
        
        # Récupérer la catégorie si spécifiée dans l'URL
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug, is_active=True)
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier les permissions de création de sujet dans cette catégorie
        if self.category:
            if self.category.requires_verification and not hasattr(request.user, 'verification_status'):
                messages.error(request, _("Vous devez être vérifié pour créer un sujet dans cette catégorie."))
                return redirect('forum:category_detail', slug=self.category.slug)
            elif self.category.requires_verification and request.user.verification_status != 'verified':
                messages.error(request, _("Vous devez être vérifié pour créer un sujet dans cette catégorie."))
                return redirect('forum:category_detail', slug=self.category.slug)
            
            # Vérifier si la catégorie est restreinte à certains groupes
            if self.category.authorized_groups.exists():
                user_groups = request.user.groups.all()
                if not any(group in user_groups for group in self.category.authorized_groups.all()):
                    messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer un sujet dans cette catégorie."))
                    return redirect('forum:index')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['category'] = self.category
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre sujet a été créé avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer un nouveau message dans un sujet.
    """
    model = Post
    form_class = PostForm
    template_name = 'forum/post_form.html'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.topic = get_object_or_404(
            Topic, 
            category__slug=self.kwargs['category_slug'],
            slug=self.kwargs['topic_slug']
        )
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier si le sujet est fermé
        if self.topic.status == 'closed' and not request.user.is_staff:
            messages.error(request, _("Ce sujet est fermé, vous ne pouvez pas y répondre."))
            return redirect('forum:topic_detail', category_slug=self.topic.category.slug, topic_slug=self.topic.slug)
        
        # Vérifier les permissions de réponse dans cette catégorie
        category = self.topic.category
        
        if category.requires_verification and not hasattr(request.user, 'verification_status'):
            messages.error(request, _("Vous devez être vérifié pour répondre dans cette catégorie."))
            return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=self.topic.slug)
        elif category.requires_verification and request.user.verification_status != 'verified':
            messages.error(request, _("Vous devez être vérifié pour répondre dans cette catégorie."))
            return redirect('forum:topic_detail', category_slug=category.slug, topic_slug=self.topic.slug)
        
        # Vérifier si la catégorie est restreinte à certains groupes
        if category.authorized_groups.exists():
            user_groups = request.user.groups.all()
            if not any(group in user_groups for group in self.category.authorized_groups.all()):
                messages.error(request, _("Vous n'avez pas les permissions nécessaires pour répondre dans cette catégorie."))
                return redirect('forum:index')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['topic'] = self.topic
        return kwargs
    
    def form_valid(self, form):
        # Mettre à jour la date de dernière activité du sujet
        self.topic.update_last_activity()
        
        messages.success(self.request, _("Votre réponse a été publiée avec succès."))
        
        # Notifier les abonnés au sujet
        post = form.save()
        self.notify_subscribers(post)
        
        return super().form_valid(form)
    
    def get_success_url(self):
        topic = self.topic
        post = self.object
        
        # Calculer la page où se trouve le nouveau message
        posts_per_page = 20
        post_index = Post.objects.filter(topic=topic, created_at__lt=post.created_at).count()
        page = (post_index // posts_per_page) + 1
        
        url = topic.get_absolute_url()
        if page > 1:
            url += f"?page={page}"
        
        # Ajouter un ancre pour naviguer directement au message
        url += f"#post-{post.id}"
        
        return url
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topic'] = self.topic
        return context
    
    def notify_subscribers(self, post):
        """
        Notifie les abonnés au sujet qu'un nouveau message a été publié.
        """
        # Récupérer les abonnés qui souhaitent être notifiés
        subscribers = TopicSubscription.objects.filter(
            topic=self.topic,
            notify_on_new_post=True
        ).exclude(
            user=self.request.user  # Ne pas notifier l'auteur du message
        ).select_related('user')
        
        # Notifier chaque abonné
        try:
            from apps.notifications.services import NotificationService
            
            for subscription in subscribers:
                NotificationService.create_notification(
                    user=subscription.user,
                    notification_type_code='forum_new_post',
                    context={
                        'topic_title': self.topic.title,
                        'category_name': self.topic.category.name,
                        'post_content': post.content[:100] + ('...' if len(post.content) > 100 else ''),
                        'author_name': post.author.get_full_name()
                    },
                    related_object=post,
                    action_url=post.get_absolute_url(),
                    action_text=_('Voir le message')
                )
        except ImportError:
            # Le module notifications n'est pas disponible
            pass
        except Exception as e:
            # Une erreur s'est produite lors de l'envoi des notifications
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la notification des abonnés : {str(e)}")


@login_required
@require_POST
@csrf_protect
def subscribe_topic(request, category_slug, topic_slug):
    """
    Vue pour s'abonner ou se désabonner d'un sujet.
    """
    topic = get_object_or_404(Topic, category__slug=category_slug, slug=topic_slug)
    
    # Vérifier si l'utilisateur est déjà abonné
    subscription, created = TopicSubscription.objects.get_or_create(
        topic=topic,
        user=request.user
    )
    
    if created:
        action = 'subscribed'
        message = _("Vous êtes maintenant abonné à ce sujet.")
    else:
        # Si déjà abonné, désabonner
        subscription.delete()
        action = 'unsubscribed'
        message = _("Vous êtes maintenant désabonné de ce sujet.")
    
    # Pour les requêtes AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'action': action,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('forum:topic_detail', category_slug=category_slug, topic_slug=topic_slug)


@login_required
@require_POST
@csrf_protect
def react_to_post(request, post_id):
    """
    Vue pour ajouter ou retirer une réaction à un message.
    """
    post = get_object_or_404(Post, pk=post_id)
    reaction = request.POST.get('reaction')
    
    if not reaction:
        return JsonResponse({'status': 'error', 'message': _("La réaction est requise.")}, status=400)
    
    # Vérifier si l'utilisateur a déjà cette réaction
    existing_reaction = PostReaction.objects.filter(
        post=post,
        user=request.user,
        reaction=reaction
    ).first()
    
    if existing_reaction:
        # Supprimer la réaction existante
        existing_reaction.delete()
        action = 'removed'
    else:
        # Ajouter la nouvelle réaction
        PostReaction.objects.create(
            post=post,
            user=request.user,
            reaction=reaction
        )
        action = 'added'
    
    # Récupérer toutes les réactions pour ce message
    reactions = PostReaction.objects.filter(post=post)
    reaction_data = {}
    
    for r in reactions:
        if r.reaction not in reaction_data:
            reaction_data[r.reaction] = 0
        reaction_data[r.reaction] += 1
    
    return JsonResponse({
        'status': 'success',
        'action': action,
        'reactions': reaction_data
    })


@login_required
@require_POST
@csrf_protect
def report_post(request, post_id):
    """
    Vue pour signaler un message inapproprié.
    """
    post = get_object_or_404(Post, pk=post_id)
    
    # Vérifier si l'utilisateur a déjà signalé ce message
    if PostReport.objects.filter(post=post, reporter=request.user).exists():
        messages.warning(request, _("Vous avez déjà signalé ce message."))
        return redirect('forum:topic_detail', category_slug=post.topic.category.slug, topic_slug=post.topic.slug)
    
    form = PostReportForm(request.POST)
    
    if form.is_valid():
        report = form.save(commit=False)
        report.post = post
        report.reporter = request.user
        report.save()
        
        messages.success(request, _("Votre signalement a été enregistré et sera examiné par un modérateur."))
    else:
        messages.error(request, _("Une erreur est survenue lors du signalement."))
    
    return redirect('forum:topic_detail', category_slug=post.topic.category.slug, topic_slug=post.topic.slug)