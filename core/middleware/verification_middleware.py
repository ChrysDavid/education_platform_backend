"""
core/middleware/verification_middleware.py
Middleware pour vérifier le statut de vérification des utilisateurs.
Ce middleware restreint l'accès à certaines fonctionnalités pour les utilisateurs non vérifiés.
"""

import re
from django.conf import settings
from django.http import JsonResponse
from django.urls import resolve

class VerificationCheckMiddleware:
    """
    Middleware qui vérifie le statut de vérification des utilisateurs
    et limite l'accès aux API en fonction de leur statut.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Endpoints d'API qui sont autorisés même pour les utilisateurs non vérifiés
        self.allowed_paths = [
            r'^/api/accounts/login/?$',
            r'^/api/accounts/register/?$',
            r'^/api/accounts/verify/?$',
            r'^/api/accounts/submit-documents/?$',
            r'^/api/accounts/verification-status/?$',
            r'^/api/forum/posts/?$',  # Lecture seule pour les forums
            r'^/api/resources/public/?$',  # Ressources publiques
            r'^/admin/.*$',  # Interface d'admin
            r'^/api/docs/.*$',  # Documentation API
            r'^/api/redoc/.*$',  # Documentation API
            r'^/api-auth/.*$',  # Authentification API
        ]
        
        # Endpoints d'API qui sont limités pour les utilisateurs non vérifiés
        # Ils peuvent lire (GET) mais pas modifier (POST, PUT, DELETE)
        self.read_only_paths = [
            r'^/api/forum/posts/\d+/?$',  # Détails d'un post forum
            r'^/api/schools/.*$',  # Informations sur les écoles
            r'^/api/resources/.*$',  # Consultation des ressources
        ]
    
    def __call__(self, request):
        # Ignorer les chemins qui ne sont pas des API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Vérifier si le chemin est autorisé sans restriction
        for pattern in self.allowed_paths:
            if re.match(pattern, request.path):
                return self.get_response(request)
        
        # Si l'utilisateur n'est pas authentifié, ne pas appliquer de restrictions
        # car DRF s'en chargera avec ses propres permissions
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Vérifier si l'utilisateur a un statut de vérification valide
        if hasattr(request.user, 'verification_status') and request.user.verification_status == 'verified':
            return self.get_response(request)
        
        # Pour les chemins en lecture seule, autoriser uniquement les méthodes GET
        for pattern in self.read_only_paths:
            if re.match(pattern, request.path) and request.method == 'GET':
                return self.get_response(request)
        
        # Pour toutes les autres routes, vérifier le statut selon la méthode HTTP
        if request.method == 'GET':
            # Permettre la lecture pour tous les utilisateurs authentifiés
            return self.get_response(request)
        else:
            # Bloquer les méthodes d'écriture pour les utilisateurs non vérifiés
            return JsonResponse({
                'error': 'Accès refusé',
                'message': 'Votre compte n\'est pas encore vérifié. Veuillez soumettre les documents requis pour la vérification.'
            }, status=403)