"""
Configuration de développement pour le projet education_platform.
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-change-this-in-production-and-use-env-variables'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'education_platform',
#         'USER': 'postgres',  # Changez pour votre nom d'utilisateur
#         'PASSWORD': 'postgres',  # Changez pour votre mot de passe
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }


# Email settings - console backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS settings - permissive for development
CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.1.5", 
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]

# Désactivation des mesures de sécurité qui peuvent gêner le développement
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False