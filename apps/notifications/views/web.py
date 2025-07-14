from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
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


class IsAdminMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est administrateur.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, _("Vous devez être administrateur pour accéder à cette page."))
        return redirect('home')


class NotificationTypeListView(LoginRequiredMixin, IsAdminMixin, ListView):
    """
    Vue pour afficher la liste des types de notification (admin).
    """
    model = NotificationType
    template_name = 'notifications/admin/notification_type_list.html'
    context_object_name = 'notification_types'
    
    def get_queryset(self):
        return NotificationType.objects.all().annotate(
            notification_count=Count('notifications'),
            preference_count=Count('user_preferences')
        ).order_by('order', 'name')


class NotificationTypeCreateView(LoginRequiredMixin, IsAdminMixin, CreateView):
    """
    Vue pour créer un type de notification (admin).
    """
    model = NotificationType
    form_class = NotificationTypeForm
    template_name = 'notifications/admin/notification_type_form.html'
    success_url = reverse_lazy('notifications:admin_notification_type_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Le type de notification a été créé avec succès."))
        return super().form_valid(form)


class NotificationTypeUpdateView(LoginRequiredMixin, IsAdminMixin, UpdateView):
    """
    Vue pour modifier un type de notification (admin).
    """
    model = NotificationType
    form_class = NotificationTypeForm
    template_name = 'notifications/admin/notification_type_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, _("Le type de notification a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('notifications:admin_notification_type_detail', kwargs={'pk': self.object.pk})


class NotificationTypeDetailView(LoginRequiredMixin, IsAdminMixin, DetailView):
    """
    Vue pour afficher les détails d'un type de notification (admin).
    """
    model = NotificationType
    template_name = 'notifications/admin/notification_type_detail.html'
    context_object_name = 'notification_type'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les modèles de notification
        context['templates'] = NotificationTemplate.objects.filter(
            notification_type=self.object
        )
        
        # Ajouter les préférences des utilisateurs
        context['preferences'] = UserNotificationPreference.objects.filter(
            notification_type=self.object
        ).select_related('user')
        
        # Ajouter des exemples de notifications
        context['sample_notifications'] = Notification.objects.filter(
            notification_type=self.object
        ).select_related('user')[:5]
        
        return context


class NotificationTypeDeleteView(LoginRequiredMixin, IsAdminMixin, DeleteView):
    """
    Vue pour supprimer un type de notification (admin).
    """
    model = NotificationType
    template_name = 'notifications/admin/notification_type_confirm_delete.html'
    success_url = reverse_lazy('notifications:admin_notification_type_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Le type de notification a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


class NotificationTemplateListView(LoginRequiredMixin, IsAdminMixin, ListView):
    """
    Vue pour afficher la liste des modèles de notification (admin).
    """
    model = NotificationTemplate
    template_name = 'notifications/admin/notification_template_list.html'
    context_object_name = 'notification_templates'
    
    def get_queryset(self):
        return NotificationTemplate.objects.all().select_related('notification_type').order_by(
            'notification_type__name', 'name'
        )


class NotificationTemplateCreateView(LoginRequiredMixin, IsAdminMixin, CreateView):
    """
    Vue pour créer un modèle de notification (admin).
    """
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications/admin/notification_template_form.html'
    success_url = reverse_lazy('notifications:admin_notification_template_list')
    
    def get_initial(self):
        initial = super().get_initial()
        notification_type_id = self.request.GET.get('notification_type')
        if notification_type_id:
            initial['notification_type'] = notification_type_id
        return initial
    
    def form_valid(self, form):
        messages.success(self.request, _("Le modèle de notification a été créé avec succès."))
        return super().form_valid(form)


class NotificationTemplateUpdateView(LoginRequiredMixin, IsAdminMixin, UpdateView):
    """
    Vue pour modifier un modèle de notification (admin).
    """
    model = NotificationTemplate
    form_class = NotificationTemplateForm
    template_name = 'notifications/admin/notification_template_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, _("Le modèle de notification a été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('notifications:admin_notification_template_list')


class NotificationTemplateDeleteView(LoginRequiredMixin, IsAdminMixin, DeleteView):
    """
    Vue pour supprimer un modèle de notification (admin).
    """
    model = NotificationTemplate
    template_name = 'notifications/admin/notification_template_confirm_delete.html'
    success_url = reverse_lazy('notifications:admin_notification_template_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Le modèle de notification a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)


class DeviceTokenListView(LoginRequiredMixin, IsAdminMixin, ListView):
    """
    Vue pour afficher la liste des tokens d'appareil (admin).
    """
    model = DeviceToken
    template_name = 'notifications/admin/device_token_list.html'
    context_object_name = 'device_tokens'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = DeviceToken.objects.all().select_related('user')
        
        # Filtrer par utilisateur si spécifié
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrer par plateforme si spécifié
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform=platform)
        
        # Filtrer par statut (actif/inactif)
        is_active = self.request.GET.get('is_active')
        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-last_used_at')


class DeviceTokenCreateView(LoginRequiredMixin, IsAdminMixin, CreateView):
    """
    Vue pour créer un token d'appareil (admin).
    """
    model = DeviceToken
    form_class = DeviceTokenForm
    template_name = 'notifications/admin/device_token_form.html'
    success_url = reverse_lazy('notifications:admin_device_token_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Le token d'appareil a été créé avec succès."))
        return super().form_valid(form)


class DeviceTokenUpdateView(LoginRequiredMixin, IsAdminMixin, UpdateView):
    """
    Vue pour modifier un token d'appareil (admin).
    """
    model = DeviceToken
    form_class = DeviceTokenForm
    template_name = 'notifications/admin/device_token_form.html'
    success_url = reverse_lazy('notifications:admin_device_token_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Le token d'appareil a été mis à jour avec succès."))
        return super().form_valid(form)


class DeviceTokenDeleteView(LoginRequiredMixin, IsAdminMixin, DeleteView):
    """
    Vue pour supprimer un token d'appareil (admin).
    """
    model = DeviceToken
    template_name = 'notifications/admin/device_token_confirm_delete.html'
    success_url = reverse_lazy('notifications:admin_device_token_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Le token d'appareil a été supprimé avec succès."))
        return super().delete(request, *args, **kwargs)