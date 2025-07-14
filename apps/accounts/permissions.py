# apps/accounts/permissions.py
from rest_framework import permissions

from django.contrib.auth.mixins import UserPassesTestMixin

from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

class AdminRequiredMixin:
    """
    Mixin pour vérifier que l'utilisateur est administrateur ou superutilisateur.
    Redirige vers la page de login avec un message d'erreur si non autorisé.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour accéder à cette page.")
            return redirect('accounts:login')
            
        if not (request.user.type == 'administrator' or request.user.is_superuser):
            messages.error(request, "Accès réservé aux administrateurs.")
            return redirect('accounts:profile')
            
        return super().dispatch(request, *args, **kwargs)
    

class IsAdministratorMixin(UserPassesTestMixin):
    """
    Mixin pour vérifier que l'utilisateur est un administrateur.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.type == 'administrator' or 
            self.request.user.is_superuser
        )
    
    def handle_no_permission(self):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(self.request, "Accès refusé : vous devez être administrateur.")
        return redirect('accounts:login')

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement le propriétaire d'un objet
    ou un administrateur à le modifier.
    """
    
    def has_object_permission(self, request, view, obj):
        # Les administrateurs ont toutes les autorisations
        if request.user.type == 'administrator' or request.user.is_superuser:
            return True
        
        # Le propriétaire de l'objet a l'autorisation
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Si l'objet est l'utilisateur lui-même
        return obj == request.user


class IsVerified(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les utilisateurs vérifiés.
    """
    message = "Votre compte doit être vérifié pour accéder à cette fonctionnalité."
    
    def has_permission(self, request, view):
        # Les administrateurs sont toujours autorisés
        if request.user.is_authenticated and (request.user.type == 'administrator' or request.user.is_superuser):
            return True
        
        # Vérifier si l'utilisateur est vérifié
        return request.user.is_authenticated and request.user.verification_status == 'verified'


class IsTeacher(permissions.BasePermission):
    """
    Permission pour autoriser seulement les enseignants.
    """
    message = "Seuls les enseignants ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'teacher'


class IsAdvisor(permissions.BasePermission):
    """
    Permission pour autoriser seulement les conseillers d'orientation.
    """
    message = "Seuls les conseillers d'orientation ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'advisor'


class IsStudent(permissions.BasePermission):
    """
    Permission pour autoriser seulement les étudiants.
    """
    message = "Seuls les étudiants ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'student'
    


class IsPupil(permissions.BasePermission):
    """
    Permission pour autoriser seulement les élèves.
    """
    message = "Seuls les élèves ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'pupil'



class IsAdministrator(permissions.BasePermission):
    """
    Permission pour autoriser seulement les administrateurs.
    """
    message = "Seuls les administrateurs ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.type == 'administrator' or request.user.is_superuser)


class IsVerifiedTeacher(permissions.BasePermission):
    """
    Permission pour autoriser seulement les enseignants vérifiés.
    """
    message = "Seuls les enseignants vérifiés ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.type == 'teacher' and 
                request.user.verification_status == 'verified')


class IsVerifiedAdvisor(permissions.BasePermission):
    """
    Permission pour autoriser seulement les conseillers vérifiés.
    """
    message = "Seuls les conseillers vérifiés ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.type == 'advisor' and 
                request.user.verification_status == 'verified')


class IsVerifiedStudent(permissions.BasePermission):
    """
    Permission pour autoriser seulement les étudiants vérifiés.
    """
    message = "Seuls les étudiants vérifiés ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.type == 'student' and 
                request.user.verification_status == 'verified')
    


class IsVerifiedPupil(permissions.BasePermission):
    """
    Permission pour autoriser seulement les élèves vérifiés.
    """
    message = "Seuls les élèves vérifiés ont accès à cette fonctionnalité."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.type == 'pupil' and 
                request.user.verification_status == 'verified')




class ReadOnly(permissions.BasePermission):
    """
    Permission pour autoriser seulement les requêtes en lecture.
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS