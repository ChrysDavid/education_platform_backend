from django import forms
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Max
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from ..models import (
    Conversation, ConversationParticipant, Message, 
    MessageReaction, MessageRead
)
from ..forms import (
    ConversationForm, DirectMessageForm, MessageForm, 
    MessageReactionForm
)

User = get_user_model()


class ConversationListView(LoginRequiredMixin, ListView):
    """
    Vue pour afficher la liste des conversations de l'utilisateur.
    """
    model = Conversation
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'
    
    def get_queryset(self):
        # Récupérer les conversations où l'utilisateur est participant
        participant_conversations = ConversationParticipant.objects.filter(
            user=self.request.user
        ).values_list('conversation_id', flat=True)
        
        # Récupérer les conversations
        queryset = Conversation.objects.filter(
            id__in=participant_conversations
        ).annotate(
            last_message_date=Max('messages__created_at')
        ).order_by('-last_message_date')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les participants et derniers messages pour chaque conversation
        conversations_data = []
        for conversation in context['conversations']:
            # Récupérer les participants (sauf l'utilisateur actuel)
            participants = User.objects.filter(
                conversations__conversation=conversation
            ).exclude(id=self.request.user.id)
            
            # Récupérer le dernier message
            last_message = Message.objects.filter(
                conversation=conversation
            ).order_by('-created_at').first()
            
            # Récupérer le nombre de messages non lus
            try:
                participant = ConversationParticipant.objects.get(
                    conversation=conversation,
                    user=self.request.user
                )
                unread_count = Message.objects.filter(
                    conversation=conversation,
                    created_at__gt=participant.last_read_at
                ).exclude(sender=self.request.user).count()
            except ConversationParticipant.DoesNotExist:
                unread_count = 0
            
            conversations_data.append({
                'conversation': conversation,
                'participants': participants,
                'last_message': last_message,
                'unread_count': unread_count
            })
        
        context['conversations_data'] = conversations_data
        
        # Ajouter le formulaire de message direct
        context['direct_message_form'] = DirectMessageForm(user=self.request.user)
        
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    """
    Vue pour afficher une conversation et ses messages.
    """
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur est participant à la conversation
        conversation = self.get_object()
        if not ConversationParticipant.objects.filter(conversation=conversation, user=request.user).exists():
            messages.error(request, _("Vous n'êtes pas autorisé à accéder à cette conversation."))
            return redirect('messaging:conversation_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.object
        
        # Récupérer les messages avec pagination
        messages_list = Message.objects.filter(
            conversation=conversation
        ).select_related('sender').order_by('created_at')
        
        # Ajouter les lectures et réactions pour chaque message
        for message in messages_list:
            message.read_by = message.reads.all()
            message.all_reactions = message.reactions.all()
        
        context['messages_list'] = messages_list
        
        # Ajouter les participants
        context['participants'] = ConversationParticipant.objects.filter(
            conversation=conversation
        ).select_related('user')
        
        # Ajouter le formulaire pour envoyer un message
        context['message_form'] = MessageForm(
            conversation=conversation,
            user=self.request.user
        )
        
        # Ajouter les infos du participant actuel
        context['current_participant'] = get_object_or_404(
            ConversationParticipant,
            conversation=conversation,
            user=self.request.user
        )
        
        # Marquer la conversation comme lue
        context['current_participant'].mark_as_read()
        
        return context


class ConversationCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour créer une nouvelle conversation.
    """
    model = Conversation
    form_class = ConversationForm
    template_name = 'messaging/conversation_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("La conversation a été créée avec succès."))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('messaging:conversation_detail', kwargs={'pk': self.object.pk})


class DirectMessageCreateView(LoginRequiredMixin, FormView):
    """
    Vue pour envoyer un message direct à un utilisateur.
    """
    form_class = DirectMessageForm
    template_name = 'messaging/direct_message_form.html'
    success_url = reverse_lazy('messaging:conversation_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Préremplir le destinataire si fourni dans l'URL
        recipient_id = self.kwargs.get('recipient_id')
        if recipient_id:
            initial = kwargs.get('initial', {})
            initial['recipient'] = recipient_id
            kwargs['initial'] = initial
        
        return kwargs
    
    def form_valid(self, form):
        conversation, message = form.save()
        messages.success(self.request, _("Votre message a été envoyé avec succès."))
        return redirect('messaging:conversation_detail', pk=conversation.pk)


class MessageCreateView(LoginRequiredMixin, CreateView):
    """
    Vue pour envoyer un message dans une conversation.
    """
    model = Message
    form_class = MessageForm
    
    def dispatch(self, request, *args, **kwargs):
        # Récupérer la conversation
        self.conversation = get_object_or_404(Conversation, pk=self.kwargs['conversation_id'])
        
        # Vérifier que l'utilisateur est participant à la conversation
        if not ConversationParticipant.objects.filter(conversation=self.conversation, user=request.user).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': _("Vous n'êtes pas autorisé à envoyer des messages dans cette conversation.")}, status=403)
            
            messages.error(request, _("Vous n'êtes pas autorisé à envoyer des messages dans cette conversation."))
            return redirect('messaging:conversation_list')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['conversation'] = self.conversation
        return kwargs
    
    def form_valid(self, form):
        message = form.save()
        
        # Pour les requêtes AJAX, renvoyer le message créé
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_name': message.sender.get_full_name(),
                'sender_id': message.sender.id,
                'message_type': message.message_type,
            })
        
        messages.success(self.request, _("Votre message a été envoyé avec succès."))
        return redirect('messaging:conversation_detail', pk=self.conversation.pk)
    
    def form_invalid(self, form):
        # Pour les requêtes AJAX, renvoyer les erreurs
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'errors': form.errors}, status=400)
        
        messages.error(self.request, _("Une erreur est survenue lors de l'envoi du message."))
        return redirect('messaging:conversation_detail', pk=self.conversation.pk)


@login_required
@require_POST
def mark_message_as_read(request, pk):
    """
    Vue pour marquer un message comme lu.
    """
    message = get_object_or_404(Message, pk=pk)
    
    # Vérifier que l'utilisateur est participant à la conversation
    if not ConversationParticipant.objects.filter(conversation=message.conversation, user=request.user).exists():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': _("Vous n'êtes pas autorisé à accéder à ce message.")}, status=403)
        
        return HttpResponseForbidden()
    
    # Marquer le message comme lu s'il ne l'est pas déjà
    if not MessageRead.objects.filter(message=message, user=request.user).exists():
        MessageRead.objects.create(message=message, user=request.user)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('messaging:conversation_detail', pk=message.conversation.pk)


@login_required
@require_POST
def mark_conversation_as_read(request, pk):
    """
    Vue pour marquer tous les messages d'une conversation comme lus.
    """
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Vérifier que l'utilisateur est participant à la conversation
    try:
        participant = ConversationParticipant.objects.get(conversation=conversation, user=request.user)
    except ConversationParticipant.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': _("Vous n'êtes pas participant à cette conversation.")}, status=403)
        
        messages.error(request, _("Vous n'êtes pas participant à cette conversation."))
        return redirect('messaging:conversation_list')
    
    # Marquer tous les messages comme lus
    messages_to_read = Message.objects.filter(
        conversation=conversation
    ).exclude(
        reads__user=request.user
    )
    
    reads_to_create = [
        MessageRead(message=message, user=request.user)
        for message in messages_to_read
    ]
    
    if reads_to_create:
        MessageRead.objects.bulk_create(reads_to_create)
    
    # Mettre à jour la date de dernière lecture
    participant.mark_as_read()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('messaging:conversation_detail', pk=conversation.pk)


@login_required
@require_POST
def add_reaction(request, message_id):
    """
    Vue pour ajouter une réaction à un message.
    """
    message = get_object_or_404(Message, pk=message_id)
    
    # Vérifier que l'utilisateur est participant à la conversation
    if not ConversationParticipant.objects.filter(conversation=message.conversation, user=request.user).exists():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': _("Vous n'êtes pas autorisé à réagir à ce message.")}, status=403)
        
        return HttpResponseForbidden()
    
    # Récupérer la réaction
    reaction = request.POST.get('reaction')
    
    if not reaction:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': _("La réaction est requise.")}, status=400)
        
        messages.error(request, _("La réaction est requise."))
        return redirect('messaging:conversation_detail', pk=message.conversation.pk)
    
    # Vérifier si l'utilisateur a déjà ajouté cette réaction
    existing_reaction = MessageReaction.objects.filter(
        message=message,
        user=request.user,
        reaction=reaction
    ).first()
    
    if existing_reaction:
        # Supprimer la réaction existante
        existing_reaction.delete()
        action = 'removed'
    else:
        # Ajouter la nouvelle réaction
        MessageReaction.objects.create(
            message=message,
            user=request.user,
            reaction=reaction
        )
        action = 'added'
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Renvoyer toutes les réactions pour ce message
        reactions = MessageReaction.objects.filter(message=message)
        reaction_data = {}
        
        for r in reactions:
            if r.reaction not in reaction_data:
                reaction_data[r.reaction] = {
                    'count': 0,
                    'users': []
                }
            
            reaction_data[r.reaction]['count'] += 1
            reaction_data[r.reaction]['users'].append({
                'id': r.user.id,
                'name': r.user.get_full_name()
            })
        
        return JsonResponse({
            'status': 'success',
            'action': action,
            'reactions': reaction_data
        })
    
    return redirect('messaging:conversation_detail', pk=message.conversation.pk)