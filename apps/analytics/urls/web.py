from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import views

app_name = 'analytics'

# Création d'un routeur pour les API REST
router = DefaultRouter()
router.register(r'dashboards', views.DashboardViewSet, basename='dashboard')
router.register(r'widgets', views.DashboardWidgetViewSet, basename='widget')

urlpatterns = [
    # URLs pour la gestion des tableaux de bord
    path('dashboards/', views.DashboardListView.as_view(), name='dashboard-list'),
    path('dashboards/<int:pk>/', views.DashboardDetailView.as_view(), name='dashboard-detail'),
    path('dashboards/create/', views.DashboardCreateView.as_view(), name='dashboard-create'),
    path('dashboards/<int:pk>/update/', views.DashboardUpdateView.as_view(), name='dashboard-update'),
    path('dashboards/<int:pk>/delete/', views.DashboardDeleteView.as_view(), name='dashboard-delete'),
    
    # URLs pour la gestion des widgets
    path('dashboards/<int:dashboard_id>/widgets/create/', views.WidgetCreateView.as_view(), name='widget-create'),
    path('widgets/<int:pk>/update/', views.WidgetUpdateView.as_view(), name='widget-update'),
    path('widgets/<int:pk>/delete/', views.WidgetDeleteView.as_view(), name='widget-delete'),
    path('widgets/<int:pk>/refresh/', views.WidgetRefreshView.as_view(), name='widget-refresh'),
    
    # URLs pour la gestion des rapports
    path('reports/create/', views.ReportCreateView.as_view(), name='report-create'),
    path('reports/<int:pk>/update/', views.ReportUpdateView.as_view(), name='report-update'),
    
    # APIs pour les widgets
    path('api/widgets/<int:pk>/data/', views.WidgetDataAPIView.as_view(), name='widget-data-api'),
    
    # URLs du routeur API
    path('api/', include(router.urls)),
]