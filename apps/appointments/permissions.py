from rest_framework import permissions
from django.db.models import Q

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement aux propriétaires d'un objet de l'éditer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les permissions d'écriture ne sont accordées qu'au propriétaire de l'objet
        return obj.user == request.user

class IsRecipientOrRequester(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement au demandeur ou au destinataire
    d'un rendez-vous de l'accéder ou le modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est le demandeur ou le destinataire
        return request.user == obj.requester or request.user == obj.recipient