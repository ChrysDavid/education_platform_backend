"""
Configuration des URLs pour le site web du projet education_platform.
"""

from django.urls import path, include

urlpatterns = [
    # Routes web pour chaque application
    path('accounts/', include('apps.accounts.urls.web')),
    path('verification/', include('apps.verification.urls')),
    path('schools/', include('apps.schools.urls.web')),
    path('messaging/', include('apps.messaging.urls.web')),
    path('appointments/', include('apps.appointments.urls.web')),
    path('notifications/', include('apps.notifications.urls.web')),
    path('forum/', include('apps.forum.urls.web')),
    path('resources/', include('apps.resources.urls.web')),
    path('orientation/', include('apps.orientation.urls.web')),
    path('analytics/', include('apps.analytics.urls.web')),
]