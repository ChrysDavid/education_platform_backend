from rest_framework import permissions
from django.db.models import Q

class IsOwner(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement au propriétaire d'un objet de l'éditer.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            # Vérifier si l'objet est public (si applicable)
            if hasattr(obj, 'is_public') and obj.is_public:
                return True
            
        # Vérifier si l'utilisateur est le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False

class IsOwnDataOnly(permissions.BasePermission):
    """
    Permission personnalisée pour permettre uniquement à un utilisateur de voir ses propres données,
    sauf s'il est administrateur.
    """
    
    def has_permission(self, request, view):
        # Les administrateurs peuvent tout voir
        if request.user.is_staff:
            return True
        
        # Les utilisateurs normaux ne peuvent voir que leurs propres données
        user_id = request.query_params.get('user_id')
        if user_id and int(user_id) != request.user.id:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs peuvent tout voir
        if request.user.is_staff:
            return True
        
        # Les utilisateurs normaux ne peuvent voir que leurs propres données
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False