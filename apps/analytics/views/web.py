from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Q

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import Dashboard, DashboardWidget, Report
from ..services import WidgetService
from ..permissions import IsOwner

# Vues pour les tableaux de bord
class DashboardListView(LoginRequiredMixin, ListView):
    model = Dashboard
    template_name = 'analytics/dashboard_list.html'
    context_object_name = 'dashboards'
    
    def get_queryset(self):
        # Ne montrer que les tableaux de bord de l'utilisateur et les tableaux publics
        return Dashboard.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).order_by('-is_default', 'title')

class DashboardDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Dashboard
    template_name = 'analytics/dashboard_detail.html'
    context_object_name = 'dashboard'
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire ou si le tableau est public
        dashboard = self.get_object()
        return dashboard.user == self.request.user or dashboard.is_public
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard = self.get_object()
        
        # Récupérer les widgets du tableau de bord
        widgets = dashboard.widgets.all().order_by('position_y', 'position_x')
        context['widgets'] = widgets
        
        return context

class DashboardCreateView(LoginRequiredMixin, CreateView):
    model = Dashboard
    template_name = 'analytics/dashboard_form.html'
    fields = ['title', 'description', 'is_default', 'is_public']
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _("Tableau de bord créé avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('analytics:dashboard-detail', kwargs={'pk': self.object.pk})

class DashboardUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Dashboard
    template_name = 'analytics/dashboard_form.html'
    fields = ['title', 'description', 'is_default', 'is_public']
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire
        dashboard = self.get_object()
        return dashboard.user == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _("Tableau de bord mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('analytics:dashboard-detail', kwargs={'pk': self.object.pk})

class DashboardDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Dashboard
    template_name = 'analytics/dashboard_confirm_delete.html'
    success_url = reverse_lazy('analytics:dashboard-list')
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire
        dashboard = self.get_object()
        return dashboard.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Tableau de bord supprimé avec succès."))
        return super().delete(request, *args, **kwargs)

# Vues pour les widgets
class WidgetCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DashboardWidget
    template_name = 'analytics/widget_form.html'
    fields = ['title', 'widget_type', 'chart_type', 'data_source', 
              'config', 'position_x', 'position_y', 'width', 'height']
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire du tableau de bord
        dashboard_id = self.kwargs.get('dashboard_id')
        dashboard = get_object_or_404(Dashboard, pk=dashboard_id)
        return dashboard.user == self.request.user
    
    def form_valid(self, form):
        dashboard_id = self.kwargs.get('dashboard_id')
        form.instance.dashboard_id = dashboard_id
        messages.success(self.request, _("Widget créé avec succès."))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_id = self.kwargs.get('dashboard_id')
        context['dashboard'] = get_object_or_404(Dashboard, pk=dashboard_id)
        return context
    
    def get_success_url(self):
        dashboard_id = self.kwargs.get('dashboard_id')
        return reverse('analytics:dashboard-detail', kwargs={'pk': dashboard_id})

class WidgetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DashboardWidget
    template_name = 'analytics/widget_form.html'
    fields = ['title', 'widget_type', 'chart_type', 'data_source', 
              'config', 'position_x', 'position_y', 'width', 'height']
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire du tableau de bord du widget
        widget = self.get_object()
        return widget.dashboard.user == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _("Widget mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        widget = self.get_object()
        context['dashboard'] = widget.dashboard
        return context
    
    def get_success_url(self):
        widget = self.get_object()
        return reverse('analytics:dashboard-detail', kwargs={'pk': widget.dashboard.pk})

class WidgetDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DashboardWidget
    template_name = 'analytics/widget_confirm_delete.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire du tableau de bord du widget
        widget = self.get_object()
        return widget.dashboard.user == self.request.user
    
    def get_success_url(self):
        widget = self.get_object()
        dashboard_id = widget.dashboard.pk
        messages.success(self.request, _("Widget supprimé avec succès."))
        return reverse('analytics:dashboard-detail', kwargs={'pk': dashboard_id})

class WidgetRefreshView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire du tableau de bord du widget
        widget_id = self.kwargs.get('pk')
        widget = get_object_or_404(DashboardWidget, pk=widget_id)
        return widget.dashboard.user == self.request.user
    
    def post(self, request, pk):
        widget = get_object_or_404(DashboardWidget, pk=pk)
        try:
            service = WidgetService(widget)
            data = service.refresh_data()
            return JsonResponse({
                'success': True,
                'data': data,
                'message': _("Widget rafraîchi avec succès.")
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': _("Erreur lors du rafraîchissement du widget: {}").format(str(e))
            }, status=500)

# Vues pour les rapports
class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    template_name = 'analytics/report_form.html'
    fields = ['title', 'description', 'report_type', 'report_format', 
              'parameters', 'start_date', 'end_date']
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, _("Rapport créé avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('analytics:report-detail', kwargs={'pk': self.object.pk})

class ReportUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Report
    template_name = 'analytics/report_form.html'
    fields = ['title', 'description', 'report_type', 'report_format', 
              'parameters', 'start_date', 'end_date', 'is_scheduled', 
              'schedule_frequency', 'next_run']
    
    def test_func(self):
        # Vérifier si l'utilisateur est le créateur du rapport
        report = self.get_object()
        return report.created_by == self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _("Rapport mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('analytics:report-detail', kwargs={'pk': self.object.pk})

# ViewSets pour l'API REST
class DashboardViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les tableaux de bord.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        # Ne montrer que les tableaux de bord de l'utilisateur et les tableaux publics
        return Dashboard.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).order_by('-is_default', 'title')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class DashboardWidgetViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les widgets de tableau de bord.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Ne montrer que les widgets des tableaux de bord de l'utilisateur
        return DashboardWidget.objects.filter(
            dashboard__user=self.request.user
        ).order_by('dashboard', 'position_y', 'position_x')
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        widget = self.get_object()
        try:
            service = WidgetService(widget)
            data = service.refresh_data()
            return Response({
                'success': True,
                'data': data,
                'message': _("Widget rafraîchi avec succès.")
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)