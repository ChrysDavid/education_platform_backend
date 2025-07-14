"""
Configuration des URLs principales pour le projet education_platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Interface d'administration Django
    path('superadmin/', admin.site.urls),
    
    # Inclusion des URLs pour le site web
    path('auth/', include('education_platform.web_urls')),
    
    # Inclusion des URLs pour l'API mobile
    path('api/', include('education_platform.api_urls')),
]

# Servir les fichiers media et statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)