"""
Configuration de test pour le projet education_platform.
"""

from .base import *

# Désactivation du débug pour les tests
DEBUG = False

# Base de données en mémoire pour accélérer les tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Email backend de test
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Hashage des mots de passe plus rapide pour les tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Désactivation du cache pour les tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Désactivation des middlewares non essentiels pour les tests
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if middleware not in {
        'corsheaders.middleware.CorsMiddleware',
    }
]