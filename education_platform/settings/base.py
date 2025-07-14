"""
Configuration de base pour tous les environnements du projet education_platform.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    # Applications Django par défaut
    'django.contrib.admin',          # Interface d'administration
    'django.contrib.auth',           # Système d'authentification
    'django.contrib.contenttypes',   # Framework de type de contenu
    'django.contrib.sessions',       # Framework de sessions
    'django.contrib.messages',       # Framework de messages
    'django.contrib.staticfiles',    # Gestion des fichiers statiques
    
    # Applications tierces
    'rest_framework',                # Django REST Framework pour API
    'rest_framework.authtoken',      # Authentification par token
    'rest_framework_simplejwt',
    'corsheaders',                   # Gestion CORS pour API
    'django_filters',                # Filtrage avancé pour API
    'drf_yasg',                      # Documentation API Swagger/OpenAPI
    
    # Vos applications personnalisées avec leur chemin complet
    'apps.accounts',                 # Gestion des utilisateurs
    'apps.verification.apps.VerificationConfig', # Système de vérification des profils
    'apps.schools',                  # Gestion des établissements scolaires
    'apps.messaging',                # Système de messagerie
    'apps.appointments',             # Gestion des rendez-vous
    'apps.notifications',            # Système de notifications
    'apps.forum',                    # Forum de discussion
    'apps.resources',                # Ressources pédagogiques
    'apps.orientation',              # Orientation et évaluations
    'apps.analytics',                # Analytique et rapports
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'education_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'education_platform.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Utilisateur personnalisé
AUTH_USER_MODEL = 'accounts.User'

# Configuration de la plateforme
PLATFORM_NAME = "Plateforme Éducative"
CONTACT_EMAIL = "contact@votreplateforme.com"
SUPPORT_EMAIL = "support@votreplateforme.com"
DEFAULT_FROM_EMAIL = "no-reply@votreplateforme.com"

# Internationalization
LANGUAGE_CODE = 'fr-fr'  # Français pour la Côte d'Ivoire
TIME_ZONE = 'Africa/Abidjan'  # Fuseau horaire de la Côte d'Ivoire
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Swagger settings for API documentation
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}