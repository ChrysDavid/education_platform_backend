from django.views.generic import ListView, DetailView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator

from ..models import (
    NotificationType, UserNotificationPreference, Notification, 
    NotificationTemplate, DeviceToken
)
from ..forms import (
    NotificationTypeForm, UserNotificationPreferenceForm, 
    NotificationTemplateForm, DeviceTokenForm, NotificationPreferencesUpdateForm
)


class NotificationListView(LoginRequiredMixin, ListView):
    """
    Vue pour afficher la liste des notifications de l'utilisateur.
    """
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        
        # Filtrer selon le statut demandé
        status = self.request.GET.get('status', 'unread')
        if status == 'all':
            queryset = queryset.exclude(status='archived')
        elif status == 'archived':
            queryset = queryset.filter(status='archived')
        else:  # 'unread' par défaut
            queryset = queryset.filter(status='unread')
        
        return queryset.select_related('notification_type').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter le statut actif
        context['active_status'] = self.request.GET.get('status', 'unread')
        
        # Ajouter les compteurs
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user, status='unread'
        ).count()
        
        context['read_count'] = Notification.objects.filter(
            user=self.request.user, status='read'
        ).count()
        
        context['archived_count'] = Notification.objects.filter(
            user=self.request.user, status='archived'
        ).count()
        
        return context


class NotificationDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher le détail d'une notification.
    """
    model = Notification
    template_name = 'notifications/notification_detail.html'
    context_object_name = 'notification'
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        # Marquer la notification comme lue
        self.object = self.get_object()
        if self.object.status == 'unread':
            self.object.mark_as_read()
        
        return super().get(request, *args, **kwargs)


@login_required
@require_POST
def mark_notification_as_read(request, pk):
    """
    Vue pour marquer une notification comme lue.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:notification_list')


@login_required
@require_POST
def mark_notification_as_unread(request, pk):
    """
    Vue pour marquer une notification comme non lue.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_unread()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:notification_list')


@login_required
@require_POST
def mark_all_notifications_as_read(request):
    """
    Vue pour marquer toutes les notifications comme lues.
    """
    Notification.objects.filter(
        user=request.user, status='unread'
    ).update(status='read', read_at=timezone.now())
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, _("Toutes les notifications ont été marquées comme lues."))
    return redirect('notifications:notification_list')


@login_required
@require_POST
def archive_notification(request, pk):
    """
    Vue pour archiver une notification.
    """
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.archive()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('notifications:notification_list')


@login_required
@require_POST
def archive_all_notifications(request):
    """
    Vue pour archiver toutes les notifications lues.
    """
    Notification.objects.filter(
        user=request.user, status='read'
    ).update(status='archived', archived_at=timezone.now())
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, _("Toutes les notifications lues ont été archivées."))
    return redirect('notifications:notification_list')


@login_required
@require_GET
def get_notification_count(request):
    """
    Vue pour récupérer le nombre de notifications non lues.
    """
    count = Notification.objects.filter(
        user=request.user, status='unread'
    ).count()
    
    return JsonResponse({'count': count})


class NotificationPreferencesView(LoginRequiredMixin, FormView):
    """
    Vue pour afficher et modifier les préférences de notification.
    """
    template_name = 'notifications/notification_preferences.html'
    form_class = NotificationPreferencesUpdateForm
    success_url = reverse_lazy('notifications:notification_preferences')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Vos préférences de notification ont été mises à jour."))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Organiser les types de notification par catégorie pour l'affichage
        categories = {}
        
        for notification_type in NotificationType.objects.filter(is_active=True).order_by('order', 'name'):
            # Déterminer la catégorie (premier mot du nom ou "Général")
            category_name = notification_type.name.split()[0] if ' ' in notification_type.name else _("Général")
            
            if category_name not in categories:
                categories[category_name] = []
            
            # Récupérer les préférences de l'utilisateur
            try:
                preference = UserNotificationPreference.objects.get(
                    user=self.request.user,
                    notification_type=notification_type
                )
            except UserNotificationPreference.DoesNotExist:
                preference = None
            
            categories[category_name].append({
                'type': notification_type,
                'preference': preference,
                'field_prefix': f"notification_{notification_type.id}"
            })
        
        context['categories'] = categories
        return context


@login_required
@require_POST
def register_device_token(request):
    """
    Vue pour enregistrer un token d'appareil pour les notifications push.
    """
    if not request.is_ajax():
        return JsonResponse({'status': 'error', 'message': _("Requête invalide.")}, status=400)
    
    token = request.POST.get('token')
    platform = request.POST.get('platform')
    device_name = request.POST.get('device_name', '')
    
    if not token or not platform:
        return JsonResponse({
            'status': 'error', 
            'message': _("Token et plateforme requis.")
        }, status=400)
    
    # Vérifier que la plateforme est valide
    if platform not in [choice[0] for choice in DeviceToken.PLATFORM_CHOICES]:
        return JsonResponse({
            'status': 'error', 
            'message': _("Plateforme non valide.")
        }, status=400)
    
    # Créer ou mettre à jour le token
    device_token, created = DeviceToken.objects.update_or_create(
        user=request.user,
        token=token,
        defaults={
            'platform': platform,
            'device_name': device_name,
            'is_active': True,
            'last_used_at': timezone.now()
        }
    )
    
    return JsonResponse({
        'status': 'success',
        'message': _("Token enregistré avec succès."),
        'created': created
    })


@login_required
@require_POST
def unregister_device_token(request):
    """
    Vue pour supprimer un token d'appareil.
    """
    if not request.is_ajax():
        return JsonResponse({'status': 'error', 'message': _("Requête invalide.")}, status=400)
    
    token = request.POST.get('token')
    
    if not token:
        return JsonResponse({
            'status': 'error', 
            'message': _("Token requis.")
        }, status=400)
    
    # Désactiver le token
    try:
        device_token = DeviceToken.objects.get(user=request.user, token=token)
        device_token.is_active = False
        device_token.save(update_fields=['is_active'])
        
        return JsonResponse({
            'status': 'success',
            'message': _("Token désactivé avec succès.")
        })
    except DeviceToken.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': _("Token non trouvé.")
        }, status=404)