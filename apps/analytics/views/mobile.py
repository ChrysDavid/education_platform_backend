from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, Http404, HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.core.paginator import Paginator

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from datetime import datetime, timedelta
import json
import csv

from ..models import (
    UserActivity, Report, Dashboard, DashboardWidget,
    Metric, MetricValue, AnalyticsEvent
)
from ..services import MetricService, WidgetService, ReportService, StatsService
from ..permissions import IsOwner, IsOwnDataOnly

# Vue principale pour le tableau de bord analytics
class AnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'analytics/dashboard.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur ou a des permissions spéciales
        return self.request.user.is_staff or hasattr(self.request.user, 'has_analytics_access')
    
    def get(self, request):
        # Récupérer le tableau de bord par défaut de l'utilisateur
        try:
            dashboard = Dashboard.objects.filter(user=request.user, is_default=True).first()
            if not dashboard:
                # Si aucun tableau de bord par défaut, prendre le premier ou en créer un
                dashboard = Dashboard.objects.filter(user=request.user).first()
                if not dashboard:
                    dashboard = Dashboard.objects.create(
                        user=request.user,
                        title=_("Mon tableau de bord"),
                        is_default=True
                    )
        except Exception as e:
            messages.error(request, _("Erreur lors du chargement du tableau de bord: {}").format(str(e)))
            dashboard = None
        
        # Récupérer les widgets du tableau de bord
        widgets = []
        if dashboard:
            widgets = dashboard.widgets.all().order_by('position_y', 'position_x')
        
        # Préparer le contexte
        context = {
            'dashboard': dashboard,
            'widgets': widgets,
            'stats': {
                'users': StatsService.get_user_stats(),
                'appointments': StatsService.get_appointment_stats(),
                'resources': StatsService.get_resource_stats()
            }
        }
        
        return render(request, self.template_name, context)

# Vues pour les rapports
class ReportListView(LoginRequiredMixin, ListView):
    model = Report
    template_name = 'analytics/report_list.html'
    context_object_name = 'reports'
    
    def get_queryset(self):
        # Ne montrer que les rapports créés par l'utilisateur
        return Report.objects.filter(created_by=self.request.user).order_by('-created_at')

class ReportDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Report
    template_name = 'analytics/report_detail.html'
    context_object_name = 'report'
    
    def test_func(self):
        # Vérifier si l'utilisateur est le créateur du rapport
        report = self.get_object()
        return report.created_by == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Si le rapport est au format JSON ou HTML, afficher une prévisualisation
        if report.file and report.report_format in ['json', 'html']:
            try:
                with report.file.open('r') as f:
                    content = f.read().decode('utf-8')
                    context['report_content'] = content
            except Exception as e:
                context['report_error'] = str(e)
        
        return context

class ReportGenerateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier si l'utilisateur est le créateur du rapport
        report_id = self.kwargs.get('pk')
        report = get_object_or_404(Report, pk=report_id)
        return report.created_by == self.request.user
    
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        try:
            report.generate()
            messages.success(request, _("Rapport généré avec succès."))
            return redirect('analytics:report-detail', pk=report.pk)
        except Exception as e:
            messages.error(request, _("Erreur lors de la génération du rapport: {}").format(str(e)))
            return redirect('analytics:report-detail', pk=report.pk)

class ReportDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier si l'utilisateur est le créateur du rapport
        report_id = self.kwargs.get('pk')
        report = get_object_or_404(Report, pk=report_id)
        return report.created_by == self.request.user
    
    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        
        if not report.file:
            messages.error(request, _("Ce rapport n'a pas encore été généré."))
            return redirect('analytics:report-detail', pk=report.pk)
        
        # Préparer la réponse HTTP
        response = HttpResponse(
            report.file.read(),
            content_type=self._get_content_type(report.report_format)
        )
        
        # Définir le nom du fichier
        filename = f"{report.title}_{timezone.now().strftime('%Y%m%d')}.{report.report_format}"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    
    def _get_content_type(self, format):
        content_types = {
            'pdf': 'application/pdf',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'json': 'application/json',
            'html': 'text/html',
        }
        return content_types.get(format, 'application/octet-stream')

# Vues pour les métriques
class MetricListView(LoginRequiredMixin, ListView):
    model = Metric
    template_name = 'analytics/metric_list.html'
    context_object_name = 'metrics'
    
    def get_queryset(self):
        # Afficher toutes les métriques publiques ou créées par l'utilisateur
        return Metric.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        ).order_by('name')

class MetricDetailView(LoginRequiredMixin, DetailView):
    model = Metric
    template_name = 'analytics/metric_detail.html'
    context_object_name = 'metric'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        metric = self.get_object()
        
        # Récupérer les valeurs historiques de la métrique
        values = MetricValue.objects.filter(metric=metric).order_by('-timestamp')[:50]
        context['values'] = values
        
        # Calculer la valeur actuelle
        try:
            service = MetricService(metric)
            current_value = service.get_value()
            context['current_value'] = current_value
        except Exception as e:
            context['error'] = str(e)
        
        return context

# Vues pour l'activité utilisateur
class UserActivityListView(LoginRequiredMixin, ListView):
    model = UserActivity
    template_name = 'analytics/user_activity_list.html'
    context_object_name = 'activities'
    paginate_by = 50
    
    def get_queryset(self):
        # Pour les administrateurs, afficher toutes les activités
        # Pour les utilisateurs normaux, afficher uniquement leurs activités
        if self.request.user.is_staff:
            queryset = UserActivity.objects.all()
        else:
            queryset = UserActivity.objects.filter(user=self.request.user)
        
        # Filtres
        action_type = self.request.GET.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        start_date = self.request.GET.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        end_date = self.request.GET.get('end_date')
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les filtres actuels au contexte
        context['current_filters'] = {
            'action_type': self.request.GET.get('action_type', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', '')
        }
        
        # Liste des types d'action disponibles
        context['action_types'] = [choice[0] for choice in UserActivity.ACTION_TYPES]
        
        return context

# Vues pour les statistiques
class UserStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'analytics/user_stats.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur
        return self.request.user.is_staff
    
    def get(self, request):
        # Récupérer les dates de début et de fin
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        # Récupérer les statistiques
        stats = StatsService.get_user_stats(start_date, end_date)
        
        context = {
            'stats': stats,
            'start_date': start_date or (timezone.now().date() - timedelta(days=30)),
            'end_date': end_date or timezone.now().date()
        }
        
        return render(request, self.template_name, context)

class ResourceStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'analytics/resource_stats.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur
        return self.request.user.is_staff
    
    def get(self, request):
        # Récupérer les dates de début et de fin
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        # Récupérer les statistiques
        stats = StatsService.get_resource_stats(start_date, end_date)
        
        context = {
            'stats': stats,
            'start_date': start_date or (timezone.now().date() - timedelta(days=30)),
            'end_date': end_date or timezone.now().date()
        }
        
        return render(request, self.template_name, context)

class AppointmentStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'analytics/appointment_stats.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur
        return self.request.user.is_staff
    
    def get(self, request):
        # Récupérer les dates de début et de fin
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        # Récupérer les statistiques
        stats = StatsService.get_appointment_stats(start_date, end_date)
        
        context = {
            'stats': stats,
            'start_date': start_date or (timezone.now().date() - timedelta(days=30)),
            'end_date': end_date or timezone.now().date()
        }
        
        return render(request, self.template_name, context)

class OrientationStatsView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'analytics/orientation_stats.html'
    
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur
        return self.request.user.is_staff
    
    def get(self, request):
        # Récupérer les dates de début et de fin
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        
        # Récupérer les statistiques
        stats = StatsService.get_orientation_stats(start_date, end_date)
        
        context = {
            'stats': stats,
            'start_date': start_date or (timezone.now().date() - timedelta(days=30)),
            'end_date': end_date or timezone.now().date()
        }
        
        return render(request, self.template_name, context)


# API pour les widgets et métriques
class WidgetDataAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier si l'utilisateur est le propriétaire du dashboard du widget
        widget_id = self.kwargs.get('pk')
        widget = get_object_or_404(DashboardWidget, pk=widget_id)
        return widget.dashboard.user == self.request.user or widget.dashboard.is_public
    
    def get(self, request, pk):
        widget = get_object_or_404(DashboardWidget, pk=pk)
        
        # Récupérer les données du widget
        try:
            service = WidgetService(widget)
            data = service.refresh_data()
            return JsonResponse({
                'success': True,
                'data': data,
                'last_updated': widget.config.get('last_updated')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class MetricValueAPIView(LoginRequiredMixin, View):
    def get(self, request, pk):
        metric = get_object_or_404(Metric, pk=pk)
        
        # Vérifier si la métrique est publique ou appartient à l'utilisateur
        if not metric.is_public and getattr(metric, 'created_by', None) != request.user:
            return JsonResponse({
                'success': False,
                'message': _("Vous n'êtes pas autorisé à accéder à cette métrique.")
            }, status=403)
        
        # Récupérer les paramètres
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        interval = request.GET.get('interval', 'day')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _("Format de date de début invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _("Format de date de fin invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        # Calculer la valeur de la métrique
        try:
            service = MetricService(metric)
            value = service.get_value(start_date, end_date, interval)
            return JsonResponse({
                'success': True,
                'value': value,
                'metric': {
                    'id': metric.id,
                    'name': metric.name,
                    'display_name': metric.display_name,
                    'unit': metric.unit
                },
                'params': {
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                    'interval': interval
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)

class StatsAPIView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier si l'utilisateur est administrateur
        return self.request.user.is_staff
    
    def get(self, request, stat_type):
        # Récupérer les dates de début et de fin
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _("Format de date de début invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': _("Format de date de fin invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        # Récupérer les statistiques selon le type demandé
        if stat_type == 'users':
            stats = StatsService.get_user_stats(start_date, end_date)
        elif stat_type == 'resources':
            stats = StatsService.get_resource_stats(start_date, end_date)
        elif stat_type == 'appointments':
            stats = StatsService.get_appointment_stats(start_date, end_date)
        elif stat_type == 'orientation':
            stats = StatsService.get_orientation_stats(start_date, end_date)
        else:
            return JsonResponse({
                'success': False,
                'message': _("Type de statistiques non reconnu.")
            }, status=400)
        
        # Convertir les dates en chaînes pour le JSON
        stats['start_date'] = stats['start_date'].strftime('%Y-%m-%d') if stats.get('start_date') else None
        stats['end_date'] = stats['end_date'].strftime('%Y-%m-%d') if stats.get('end_date') else None
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })

class TrackEventAPIView(APIView):
    """
    API pour le suivi d'événements analytiques.
    Cette API peut être appelée depuis le frontend pour suivre des événements utilisateur.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Récupérer les données de l'événement
        event_name = request.data.get('event_name')
        properties = request.data.get('properties', {})
        
        if not event_name:
            return Response({
                'success': False,
                'message': _("Le nom de l'événement est requis.")
            }, status=400)
        
        try:
            # Suivre l'événement
            event = AnalyticsEvent.track(
                event_name=event_name,
                user=request.user,
                properties=properties,
                request=request
            )
            
            return Response({
                'success': True,
                'message': _("Événement suivi avec succès."),
                'event_id': event.id
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)

# ViewSets pour l'API REST
class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les activités utilisateur.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated, IsOwnDataOnly]
    
    def get_queryset(self):
        # Pour les administrateurs, afficher toutes les activités
        # Pour les utilisateurs normaux, afficher uniquement leurs activités
        if self.request.user.is_staff:
            queryset = UserActivity.objects.all()
        else:
            queryset = UserActivity.objects.filter(user=self.request.user)
        
        # Filtres
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')

class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les rapports.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Report.objects.filter(created_by=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        report = self.get_object()
        try:
            report.generate()
            return Response({
                'success': True,
                'message': _("Rapport généré avec succès.")
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)

class MetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les métriques.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Afficher toutes les métriques publiques ou créées par l'utilisateur
        return Metric.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user)
        ).order_by('name')
    
    @action(detail=True, methods=['get'])
    def value(self, request, pk=None):
        metric = self.get_object()
        
        # Récupérer les paramètres
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        interval = request.query_params.get('interval', 'day')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date de début invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': _("Format de date de fin invalide. Utilisez YYYY-MM-DD.")
                }, status=400)
        
        # Calculer la valeur de la métrique
        try:
            service = MetricService(metric)
            value = service.get_value(start_date, end_date, interval)
            return Response({
                'success': True,
                'value': value,
                'metric': {
                    'id': metric.id,
                    'name': metric.name,
                    'display_name': metric.display_name,
                    'unit': metric.unit
                },
                'params': {
                    'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                    'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                    'interval': interval
                }
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=500)

class AnalyticsEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint pour les événements analytiques.
    """
    serializer_class = None  # À implémenter avec un serializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        # Seuls les administrateurs peuvent voir tous les événements
        if not self.request.user.is_staff:
            return AnalyticsEvent.objects.none()
        
        queryset = AnalyticsEvent.objects.all()
        
        # Filtres
        event_name = self.request.query_params.get('event_name')
        if event_name:
            queryset = queryset.filter(event_name=event_name)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__gte=start_date)
            except ValueError:
                pass
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(timestamp__date__lte=end_date)
            except ValueError:
                pass
        
        return queryset.order_by('-timestamp')