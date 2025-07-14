from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone

from apps.accounts.models import User

def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur."""
    return user.is_staff or user.type == 'administrator'

@login_required
@user_passes_test(is_admin)
def verification_list(request):
    """
    Affiche la liste des utilisateurs non vérifiés ou en attente (sauf les administrateurs)
    """
    status_filter = request.GET.get('status', 'all')
    
    # Filtrer selon le statut sélectionné
    if status_filter == 'unverified':
        users_to_verify = User.objects.filter(
            verification_status='unverified',
            type__in=['student', 'pupil', 'teacher', 'advisor']  # Exclut les administrateurs
        )
    elif status_filter == 'pending':
        users_to_verify = User.objects.filter(
            verification_status='pending',
            type__in=['student', 'pupil', 'teacher', 'advisor']
        )
    else:  # 'all' ou autre valeur par défaut
        users_to_verify = User.objects.filter(
            verification_status__in=['unverified', 'pending'],
            type__in=['student', 'pupil', 'teacher', 'advisor']
        )
    
    # Ordonner par date de demande (si disponible) ou par date d'inscription
    users_to_verify = users_to_verify.order_by('-verification_requested_date', '-date_joined')
    
    return render(request, 'dashboard/pages/verification/verification_list.html', {
        'users_to_verify': users_to_verify,
        'status_filter': status_filter
    })

@login_required
@user_passes_test(is_admin)
def user_verification_detail(request, user_id):
    """
    Affiche les détails d'un utilisateur pour vérification.
    """
    user = get_object_or_404(User, id=user_id)
    profile = user.get_profile_info()
    
    # Récupérer les documents disponibles pour cet utilisateur
    documents = {
        'profile_picture': user.profile_picture if user.profile_picture else None,
        'identity_document': user.identity_document if user.identity_document else None,
    }
    
    # Ajouter des documents spécifiques au type d'utilisateur
    if user.type == 'teacher' and hasattr(user, 'teacher_profile'):
        documents['degree_document'] = user.teacher_profile.degree_document if user.teacher_profile.degree_document else None
        documents['cv'] = user.teacher_profile.cv if user.teacher_profile.cv else None
    elif user.type == 'advisor' and hasattr(user, 'advisor_profile'):
        documents['portfolio'] = user.advisor_profile.portfolio if user.advisor_profile.portfolio else None
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('verification_notes', '')
        
        if action == 'approve':
            user.complete_verification('verified', notes)
            messages.success(request, f"Le compte de {user.get_full_name()} a été approuvé avec succès.")
        elif action == 'reject':
            user.complete_verification('rejected', notes)
            messages.warning(request, f"Le compte de {user.get_full_name()} a été rejeté.")
        else:
            messages.error(request, "Action invalide.")
        
        return redirect('verification:verification_list')
    
    context = {
        'user': user,
        'profile': profile,
        'documents': documents,
        'verification_status_choices': User.VERIFICATION_STATUS_CHOICES,
        'user_type_display': dict(User.USER_TYPE_CHOICES).get(user.type, user.type),
    }
    
    return render(request, 'dashboard/pages/verification/verification_user_detail.html', context)