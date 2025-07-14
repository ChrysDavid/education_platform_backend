"""
Configuration des URLs pour l'API mobile du projet education_platform.
"""

from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Configuration de Swagger pour la documentation de l'API
schema_view = get_schema_view(
    openapi.Info(
        title="Plateforme Éducative API",
        default_version='v1',
        description="API pour la plateforme de mise en relation entre professeurs, conseillers d'orientation et élèves/étudiants",
        terms_of_service="https://www.votreplatforme.com/terms/",
        contact=openapi.Contact(email="contact@votreplatforme.com"),
        license=openapi.License(name="Licence propriétaire"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Documentation API avec Swagger
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Authentification REST Framework
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('rest_framework.urls')),
    
    # Routes API pour chaque application
    path('accounts/', include('apps.accounts.urls.mobile')),
    path('schools/', include('apps.schools.urls.mobile')),
    path('messaging/', include('apps.messaging.urls.mobile')),
    path('appointments/', include('apps.appointments.urls.mobile')),
    path('notifications/', include('apps.notifications.urls.mobile')),
    path('forum/', include('apps.forum.urls.mobile')),
    path('resources/', include('apps.resources.urls.mobile')),
    path('orientation/', include('apps.orientation.urls.mobile')),
    path('analytics/', include('apps.analytics.urls.mobile')),
]