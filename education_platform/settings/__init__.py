"""
Ce fichier détermine quel fichier de configuration charger en fonction de l'environnement.
"""

import os

# Déterminer quel environnement utiliser (default: development)
environment = os.environ.get('DJANGO_SETTINGS_MODULE', 'development')

# Charger la configuration appropriée
if environment == 'production':
    from .production import *
elif environment == 'test':
    from .test import *
else:
    from .development import *