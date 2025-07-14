# apps/accounts/views/web.py
from django.views.generic import (
    TemplateView, FormView, UpdateView, ListView, 
    DetailView, CreateView, RedirectView
)
from django.contrib.auth.views import (
    LoginView as AuthLoginView,
    PasswordChangeView as AuthPasswordChangeView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth import authenticate, login
from django.db.models import Q
from django.http import HttpResponseRedirect

from ..models import User, Student, Teacher, Advisor
from ..forms import (
    # LoginForm,
    RegistrationForm as RegisterForm,
    StudentProfileForm,
    TeacherProfileForm,
    AdvisorProfileForm,
    PasswordChangeForm,
    PasswordResetRequestForm,
    SetPasswordForm
)
from ..services import AccountService
from ..permissions import IsAdministratorMixin, AdminRequiredMixin




class DashboardView(AdminRequiredMixin, TemplateView):
    """
    Vue pour le tableau de bord administrateur.
    Accessible uniquement aux administrateurs et superutilisateurs.
    """
    template_name = 'dashboard/pages/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajoutez ici les données spécifiques au dashboard
        context['page_title'] = "Tableau de bord administrateur"
        context['active_menu'] = "dashboard"
        
        # Exemple de statistiques
        from ..models import User
        context['user_count'] = User.objects.count()
        context['verified_users'] = User.objects.filter(verification_status='verified').count()
        context['pending_verifications'] = User.objects.filter(verification_status='pending').count()
        
        return context




class LoginView(AuthLoginView):
    """
    Vue pour la connexion des utilisateurs au site web.
    """
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        email = form.cleaned_data.get('username')  # ou 'email' selon votre formulaire
        password = form.cleaned_data.get('password')
        
        print(f"Tentative de connexion avec email: {email}")
        
        user = authenticate(self.request, username=email, password=password)  # ou email=email selon votre backend
        
        if user is not None:
            print(f"Authentification réussie pour {email}, type: {user.type}")
            login(self.request, user)
            return HttpResponseRedirect(self.get_success_url())
        else:
            print(f"Échec d'authentification pour {email}")
            return self.form_invalid(form)


    def get_success_url(self):
        user = self.request.user
        print(f"User type: {user.type}, Is superuser: {user.is_superuser}")
        
        if user.type == 'administrator' or user.is_superuser:
            print("Redirection vers admin_dashboard")
            return reverse_lazy('accounts:admin_dashboard')
        elif user.type == 'student':
            return reverse_lazy('accounts:student_dashboard')
        elif user.type == 'teacher':
            return reverse_lazy('accounts:teacher_dashboard')
        elif user.type == 'advisor':
            return reverse_lazy('accounts:advisor_dashboard')
        return reverse_lazy('accounts:profile')



class RegisterView(FormView):
    """
    Vue pour l'inscription des utilisateurs au site web.
    """
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('accounts:login')
    
    def get(self, request, *args, **kwargs):
        # Récupérer le user_type des kwargs de l'URL
        self.user_type = kwargs.get('user_type')
        return super().get(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Passer le type d'utilisateur si spécifié
        if hasattr(self, 'user_type') and self.user_type:
            kwargs['initial'] = {'user_type': self.user_type}
        return kwargs
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Inscription réussie. Veuillez vous connecter."))
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Vue pour afficher et mettre à jour le profil utilisateur sur le site web.
    """
    template_name = 'accounts/profile.html'
    fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth', 'address', 'city']
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, _("Profil mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['verification_status'] = user.get_verification_status_display()
        
        # Ajouter le formulaire de profil spécifique selon le type d'utilisateur
        if user.type == 'student' and hasattr(user, 'student_profile'):
            context['profile_form'] = StudentProfileForm(instance=user.student_profile)
        elif user.type == 'teacher' and hasattr(user, 'teacher_profile'):
            context['profile_form'] = TeacherProfileForm(instance=user.teacher_profile)
        elif user.type == 'advisor' and hasattr(user, 'advisor_profile'):
            context['profile_form'] = AdvisorProfileForm(instance=user.advisor_profile)
        
        return context


class PasswordChangeView(LoginRequiredMixin, AuthPasswordChangeView):
    """
    Vue pour changer le mot de passe sur le site web.
    """
    template_name = 'accounts/password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('accounts:profile')
    
    def form_valid(self, form):
        messages.success(self.request, _("Votre mot de passe a été modifié avec succès."))
        return super().form_valid(form)












class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'dashboard/pages/user_list.html'
    context_object_name = 'users'
    paginate_by = 10  # Pagination avec 10 utilisateurs par page
    
    def test_func(self):
        # Vérifie si l'utilisateur connecté est autorisé à voir cette page
        # Par exemple, seul un admin peut voir cette liste
        return self.request.user.is_staff or self.request.user.type == 'administrator'
    
    def get_queryset(self):
        # Exclure les administrateurs de la liste
        queryset = User.objects.exclude(type='administrator')
        
        # Récupérer les paramètres de recherche et de filtrage
        search_query = self.request.GET.get('search', '')
        user_type = self.request.GET.get('type', '')
        verification_status = self.request.GET.get('verification_status', '')
        
        # Appliquer la recherche si une requête est fournie
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query) | 
                Q(email__icontains=search_query)
            )
        
        # Filtrer par type d'utilisateur si spécifié
        if user_type:
            queryset = queryset.filter(type=user_type)
            
        # Filtrer par statut de vérification si spécifié
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les choix pour les filtres
        context['user_types'] = User.USER_TYPE_CHOICES
        context['verification_statuses'] = User.VERIFICATION_STATUS_CHOICES
        
        # Conserver les paramètres de recherche pour la pagination
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_status'] = self.request.GET.get('verification_status', '')
        
        return context

class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Vue pour afficher les détails d'un utilisateur sur le site web (administrateurs).
    """
    model = User
    template_name = 'dashboard/pages/user_detail.html'
    context_object_name = 'user_detail'
    
    def test_func(self):
        # Vérifie si l'utilisateur connecté est autorisé à voir cette page
        return self.request.user.is_staff or self.request.user.type == 'administrator'
    
    def get_object(self, queryset=None):
        # Récupérer l'utilisateur mais s'assurer qu'il n'est pas un administrateur
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        if user.type == 'administrator' and not self.request.user.is_superuser:
            # Si l'utilisateur est un admin et que le demandeur n'est pas un superuser
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Récupérer le profil spécifique de l'utilisateur
        context['profile'] = user.get_profile_info()
        
        return context
    








class PendingVerificationsView(LoginRequiredMixin, IsAdministratorMixin, ListView):
    """
    Vue pour lister les demandes de vérification en attente sur le site web (administrateurs).
    """
    model = User
    template_name = 'accounts/pending_verifications.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return User.objects.filter(verification_status='pending').order_by('verification_requested_date')


class ProcessVerificationView(LoginRequiredMixin, IsAdministratorMixin, UpdateView):
    """
    Vue pour traiter une demande de vérification sur le site web (administrateurs).
    """
    model = User
    template_name = 'accounts/process_verification.html'
    fields = ['verification_notes']
    
    def post(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Vérifier si l'utilisateur est en attente de vérification
        if user.verification_status != 'pending':
            messages.error(request, _("Cet utilisateur n'est pas en attente de vérification."))
            return redirect('accounts:pending_verifications')
        
        # Récupérer les données de la requête
        approved = 'approve' in request.POST
        notes = request.POST.get('verification_notes', '')
        
        # Traiter la demande de vérification
        success = AccountService.verify_user(
            user=user,
            admin=request.user,
            approved=approved,
            notes=notes
        )
        
        if success:
            action = "approuvée" if approved else "rejetée"
            messages.success(request, _(f"La demande de vérification a été {action} avec succès."))
            return redirect('accounts:pending_verifications')
        
        messages.error(request, _("Impossible de traiter la demande de vérification. Veuillez réessayer plus tard."))
        return redirect('accounts:process_verification', pk=user.pk)


class UserStatisticsView(LoginRequiredMixin, IsAdministratorMixin, TemplateView):
    """
    Vue pour afficher des statistiques utilisateurs sur le site web (administrateurs).
    """
    template_name = 'accounts/user_statistics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = AccountService.get_user_stats()
        return context


class PasswordResetRequestView(FormView):
    """
    Vue pour demander la réinitialisation de mot de passe sur le site web.
    """
    template_name = 'accounts/password_reset_request.html'
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            
            # Envoyer l'email de réinitialisation
            success = AccountService.send_password_reset_email(user, token)
            
            if not success:
                messages.error(self.request, _("Impossible d'envoyer l'email de réinitialisation. Veuillez réessayer plus tard."))
                return super().form_invalid(form)
        except User.DoesNotExist:
            # Ne rien faire, on ne veut pas révéler que l'utilisateur n'existe pas
            pass
        
        # Pour des raisons de sécurité, toujours afficher un message de succès
        messages.success(self.request, _("Si cette adresse email est associée à un compte, un email de réinitialisation sera envoyé."))
        return super().form_valid(form)


class PasswordResetConfirmView(FormView):
    """
    Vue pour confirmer et effectuer la réinitialisation du mot de passe sur le site web.
    """
    template_name = 'accounts/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier le token et l'uid avant d'afficher le formulaire
        self.uid = kwargs.get('uidb64')
        self.token = kwargs.get('token')
        
        try:
            # Décodage de l'UID
            uid = force_str(urlsafe_base64_decode(self.uid))
            self.user = User.objects.get(pk=uid)
            
            # Vérification du token
            if not default_token_generator.check_token(self.user, self.token):
                messages.error(request, _("Le lien de réinitialisation de mot de passe est invalide ou a expiré."))
                return redirect('accounts:password_reset_request')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            self.user = None
            messages.error(request, _("Le lien de réinitialisation de mot de passe est invalide."))
            return redirect('accounts:password_reset_request')
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Mise à jour du mot de passe
        self.user.set_password(form.cleaned_data['new_password1'])
        self.user.save()
        
        messages.success(self.request, _("Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter avec votre nouveau mot de passe."))
        return super().form_valid(form)