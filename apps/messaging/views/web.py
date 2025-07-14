from django import forms
from django.views.generic import UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.contrib.auth import get_user_model

from ..models import (
    Conversation, ConversationParticipant, Message
)
from ..forms import (
    ConversationForm, ConversationParticipantForm
)

User = get_user_model()


class ConversationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier une conversation.
    """
    model = Conversation
    form_class = ConversationForm
    template_name = 'messaging/conversation_form.html'
    
    def test_func(self):
        # Vérifier que l'utilisateur est administrateur de la conversation
        conversation = self.get_object()
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=self.request.user
            )
            return participant.is_admin
        except ConversationParticipant.DoesNotExist:
            return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La conversation a été mise à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.object.pk})


class ConversationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour supprimer une conversation.
    """
    model = Conversation
    template_name = 'messaging/conversation_confirm_delete.html'
    success_url = reverse_lazy('messaging:conversation_list')
    
    def test_func(self):
        # Vérifier que l'utilisateur est administrateur de la conversation
        conversation = self.get_object()
        try:
            participant = ConversationParticipant.objects.get(
                conversation=conversation,
                user=self.request.user
            )
            return participant.is_admin
        except ConversationParticipant.DoesNotExist:
            return False
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("La conversation a été supprimée avec succès."))
        return super().delete(request, *args, **kwargs)


class ParticipantAddView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Vue pour ajouter un participant à une conversation.
    """
    template_name = 'messaging/participant_form.html'
    form_class = forms.Form
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.conversation = get_object_or_404(Conversation, pk=self.kwargs['conversation_id'])
    
    def test_func(self):
        # Vérifier que l'utilisateur est administrateur de la conversation
        try:
            participant = ConversationParticipant.objects.get(
                conversation=self.conversation,
                user=self.request.user
            )
            return participant.is_admin
        except ConversationParticipant.DoesNotExist:
            return False
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Ajouter un champ pour sélectionner les utilisateurs
        form.fields['users'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.filter(is_active=True).exclude(
                conversations__conversation=self.conversation
            ),
            label=_("Utilisateurs"),
            widget=forms.SelectMultiple(attrs={'class': 'form-select'})
        )
        
        return form
    
    def form_valid(self, form):
        users = form.cleaned_data['users']
        
        # Ajouter les utilisateurs à la conversation
        for user in users:
            self.conversation.add_participant(user)
        
        # Ajouter un message système
        if len(users) == 1:
            message = _(f"{users[0].get_full_name()} a rejoint la conversation.")
        else:
            user_names = ", ".join(user.get_full_name() for user in users)
            message = _(f"{user_names} ont rejoint la conversation.")
        
        Message.objects.create(
            conversation=self.conversation,
            message_type='system',
            content=message
        )
        
        messages.success(self.request, _("Les participants ont été ajoutés avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.conversation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conversation'] = self.conversation
        return context


class ParticipantRemoveView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vue pour retirer un participant d'une conversation.
    """
    model = ConversationParticipant
    template_name = 'messaging/participant_confirm_delete.html'
    pk_url_kwarg = 'participant_id'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.conversation = get_object_or_404(Conversation, pk=self.kwargs['conversation_id'])
    
    def test_func(self):
        # Vérifier que l'utilisateur est administrateur de la conversation ou se retire lui-même
        participant_to_remove = self.get_object()
        
        # S'il s'agit de se retirer soi-même
        if participant_to_remove.user == self.request.user:
            return True
        
        # Sinon, vérifier que l'utilisateur est administrateur
        try:
            current_participant = ConversationParticipant.objects.get(
                conversation=self.conversation,
                user=self.request.user
            )
            return current_participant.is_admin
        except ConversationParticipant.DoesNotExist:
            return False
    
    def get_queryset(self):
        return ConversationParticipant.objects.filter(conversation=self.conversation)
    
    def delete(self, request, *args, **kwargs):
        participant = self.get_object()
        user_name = participant.user.get_full_name()
        
        # Supprimer le participant
        response = super().delete(request, *args, **kwargs)
        
        # Ajouter un message système
        if participant.user == request.user:
            message = _(f"{user_name} a quitté la conversation.")
        else:
            message = _(f"{user_name} a été retiré de la conversation par {request.user.get_full_name()}.")
        
        Message.objects.create(
            conversation=self.conversation,
            message_type='system',
            content=message
        )
        
        messages.success(request, _("Le participant a été retiré avec succès."))
        
        # Si l'utilisateur s'est retiré lui-même, rediriger vers la liste des conversations
        if participant.user == request.user:
            return redirect('messaging:conversation_list')
        
        return response
    
    def get_success_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.conversation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conversation'] = self.conversation
        return context


class ParticipantUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vue pour modifier les paramètres d'un participant.
    """
    model = ConversationParticipant
    form_class = ConversationParticipantForm
    template_name = 'messaging/participant_form.html'
    pk_url_kwarg = 'participant_id'
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.conversation = get_object_or_404(Conversation, pk=self.kwargs['conversation_id'])
    
    def test_func(self):
        participant = self.get_object()
        
        # Si l'utilisateur modifie ses propres paramètres
        if participant.user == self.request.user:
            # Il ne peut pas modifier son statut d'administrateur
            self.can_change_admin = False
            return True
        
        # Sinon, vérifier que l'utilisateur est administrateur
        try:
            current_participant = ConversationParticipant.objects.get(
                conversation=self.conversation,
                user=self.request.user
            )
            self.can_change_admin = current_participant.is_admin
            return current_participant.is_admin
        except ConversationParticipant.DoesNotExist:
            return False
    
    def get_queryset(self):
        return ConversationParticipant.objects.filter(conversation=self.conversation)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Si l'utilisateur ne peut pas modifier le statut d'administrateur
        if not getattr(self, 'can_change_admin', True):
            form.fields['is_admin'].disabled = True
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, _("Les paramètres du participant ont été mis à jour avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.conversation.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conversation'] = self.conversation
        return context