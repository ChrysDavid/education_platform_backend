from rest_framework import permissions


class IsSchoolOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement le propriétaire d'une école
    ou un administrateur à la modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toutes les autorisations
        if request.user.is_staff or request.user.is_superuser or request.user.type == 'administrator':
            return True
        
        # Le propriétaire de l'école a l'autorisation
        # Note: Cette logique dépendra de votre modèle de données exact
        # et de comment vous définissez "propriétaire" d'une école
        if hasattr(obj, 'admin_contact_email') and obj.admin_contact_email == request.user.email:
            return True
        
        return False


class CanReviewSchool(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les utilisateurs vérifiés
    à laisser un avis sur une école.
    """
    message = "Seuls les utilisateurs vérifiés peuvent laisser un avis."
    
    def has_permission(self, request, view):
        # Les administrateurs sont toujours autorisés
        if request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser or request.user.type == 'administrator'
        ):
            return True
        
        # Lecture autorisée pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est vérifié
        return request.user.is_authenticated and request.user.verification_status == 'verified'


class IsReviewAuthorOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement l'auteur d'un avis
    ou un administrateur à le modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toutes les autorisations
        if request.user.is_staff or request.user.is_superuser or request.user.type == 'administrator':
            return True
        
        # L'auteur de l'avis a l'autorisation
        return obj.user == request.user


class CanModifySchoolContent(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser la modification du contenu d'une école
    (départements, programmes, médias, etc.).
    """
    
    def has_permission(self, request, view):
        # Les administrateurs sont toujours autorisés
        if request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser or request.user.type == 'administrator'
        ):
            return True
        
        # Lecture autorisée pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur est un enseignant vérifié
        if request.user.is_authenticated and request.user.type == 'teacher' and request.user.verification_status == 'verified':
            # Vérifier si l'enseignant est lié à l'école
            # Cette logique dépendra de votre modèle de données exact
            return hasattr(request.user, 'teacher_profile') and request.user.teacher_profile.school_id == view.kwargs.get('school_id')
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les requêtes en lecture.
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS