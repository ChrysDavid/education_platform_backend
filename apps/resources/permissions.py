from rest_framework import permissions


class IsResourceOwnerOrAdmin(permissions.BasePermission):
    """
    Permission qui autorise seulement le créateur de la ressource ou un administrateur.
    """
    def has_object_permission(self, request, view, obj):
        # Autorisation en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # En écriture, seulement le créateur ou un administrateur
        return obj.created_by == request.user or request.user.is_staff


class CanReviewResource(permissions.BasePermission):
    """
    Permission qui vérifie si un utilisateur peut évaluer une ressource.
    """
    def has_permission(self, request, view):
        # Autorisation en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # En écriture, il faut être authentifié
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Autorisation en lecture pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # En écriture, vérifier si l'utilisateur peut évaluer
        # Un utilisateur ne peut pas évaluer sa propre ressource
        if obj.resource.created_by == request.user:
            return False
        
        # Seul l'auteur de l'évaluation ou un administrateur peut la modifier
        return obj.user == request.user or request.user.is_staff


class IsCollectionOwnerOrAdmin(permissions.BasePermission):
    """
    Permission qui autorise seulement le créateur de la collection ou un administrateur.
    """
    def has_object_permission(self, request, view, obj):
        # Autorisation en lecture pour tout le monde si la collection est publique
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.created_by == request.user or request.user.is_staff
        
        # En écriture, seulement le créateur ou un administrateur
        return obj.created_by == request.user or request.user.is_staff


class IsCommentOwnerOrAdmin(permissions.BasePermission):
    """
    Permission qui autorise seulement l'auteur du commentaire ou un administrateur.
    """
    def has_object_permission(self, request, view, obj):
        # Autorisation en lecture pour tout le monde si le commentaire est public
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user or request.user.is_staff
        
        # En écriture, seulement l'auteur ou un administrateur
        return obj.user == request.user or request.user.is_staff