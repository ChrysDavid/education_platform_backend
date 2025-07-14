from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .. import views

app_name = 'analytics'

# Création d'un routeur pour les API REST
router = DefaultRouter()
router.register(r'reports', views.ReportViewSet, basename='report')
router.register(r'user-activities', views.UserActivityViewSet, basename='user-activity')
router.register(r'events', views.AnalyticsEventViewSet, basename='event')
router.register(r'metrics', views.MetricViewSet, basename='metric')

urlpatterns = [
    # URLs standards pour les utilisateurs
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('reports/', views.ReportListView.as_view(), name='report-list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('reports/<int:pk>/generate/', views.ReportGenerateView.as_view(), name='report-generate'),
    path('reports/<int:pk>/download/', views.ReportDownloadView.as_view(), name='report-download'),
    path('metrics/', views.MetricListView.as_view(), name='metric-list'),
    path('metrics/<int:pk>/', views.MetricDetailView.as_view(), name='metric-detail'),
    path('user-activities/', views.UserActivityListView.as_view(), name='user-activity-list'),
    path('stats/users/', views.UserStatsView.as_view(), name='user-stats'),
    path('stats/resources/', views.ResourceStatsView.as_view(), name='resource-stats'),
    path('stats/appointments/', views.AppointmentStatsView.as_view(), name='appointment-stats'),
    path('stats/orientation/', views.OrientationStatsView.as_view(), name='orientation-stats'),
    
    # APIs pour les données
    path('api/stats/<str:stat_type>/', views.StatsAPIView.as_view(), name='stats-api'),
    path('api/metrics/<int:pk>/value/', views.MetricValueAPIView.as_view(), name='metric-value-api'),
    path('api/track-event/', views.TrackEventAPIView.as_view(), name='track-event-api'),
    
    # URLs du routeur API
    path('api/', include(router.urls)),
]