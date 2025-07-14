from datetime import timedelta
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model

from rest_framework import viewsets, permissions
from rest_framework.response import Response

from ..models import Appointment, AppointmentSlot, AppointmentException
from ..serializers import AppointmentSlotSerializer, AppointmentExceptionSerializer
from ..permissions import IsOwnerOrReadOnly

User = get_user_model()

# Classes de base pour les vues Django
class AppointmentBaseView(LoginRequiredMixin):
    model = Appointment
    context_object_name = 'appointment'

class AppointmentSlotBaseView(LoginRequiredMixin):
    model = AppointmentSlot
    context_object_name = 'slot'

class AppointmentExceptionBaseView(LoginRequiredMixin):
    model = AppointmentException
    context_object_name = 'exception'

class AppointmentUpdateView(AppointmentBaseView, UserPassesTestMixin, UpdateView):
    template_name = 'appointments/appointment_form.html'
    fields = ['title', 'schedule_time', 'duration_minutes', 'purpose', 
              'location', 'meeting_type', 'meeting_link']
    
    def test_func(self):
        # Vérifier que l'utilisateur est le demandeur ou le destinataire
        appointment = self.get_object()
        return (appointment.requester == self.request.user or 
                appointment.recipient == self.request.user)
    
    def get_queryset(self):
        # L'utilisateur ne peut modifier que ses propres rendez-vous
        return Appointment.objects.filter(
            (Q(requester=self.request.user) | Q(recipient=self.request.user)) &
            ~Q(status__in=['cancelled', 'completed', 'no_show'])
        )
    
    def form_valid(self, form):
        # Recalculer l'heure de fin
        if form.instance.schedule_time:
            form.instance.end_time = form.instance.schedule_time + timedelta(minutes=form.instance.duration_minutes)
        
        # Si la date a changé, mettre à jour le statut
        old_appointment = self.get_object()
        if old_appointment.schedule_time != form.instance.schedule_time:
            if form.instance.status == 'confirmed':
                form.instance.status = 'rescheduled'
                messages.info(self.request, _('Le rendez-vous a été reporté.'))
        
        messages.success(self.request, _('Rendez-vous mis à jour avec succès.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.object.pk})

class ManageAppointmentSlotsView(AppointmentSlotBaseView, ListView):
    template_name = 'appointments/manage_slots.html'
    context_object_name = 'slots'
    
    def get_queryset(self):
        return AppointmentSlot.objects.filter(user=self.request.user).order_by('day_of_week', 'start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les exceptions
        context['exceptions'] = AppointmentException.objects.filter(
            user=self.request.user,
            date__gte=timezone.now().date()
        ).order_by('date')
        
        return context

class AppointmentSlotCreateView(AppointmentSlotBaseView, CreateView):
    template_name = 'appointments/slot_form.html'
    fields = ['day_of_week', 'start_time', 'end_time', 'location', 
              'is_active', 'recurring', 'start_date', 'end_date']
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _('Créneau de rendez-vous créé avec succès.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:manage_slots')

class AppointmentSlotUpdateView(AppointmentSlotBaseView, UserPassesTestMixin, UpdateView):
    template_name = 'appointments/slot_form.html'
    fields = ['day_of_week', 'start_time', 'end_time', 'location', 
              'is_active', 'recurring', 'start_date', 'end_date']
    
    def test_func(self):
        # Vérifier que l'utilisateur est le propriétaire du créneau
        slot = self.get_object()
        return slot.user == self.request.user
    
    def get_queryset(self):
        return AppointmentSlot.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _('Créneau de rendez-vous mis à jour avec succès.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:manage_slots')

class AppointmentSlotDeleteView(AppointmentSlotBaseView, UserPassesTestMixin, DeleteView):
    template_name = 'appointments/slot_confirm_delete.html'
    
    def test_func(self):
        # Vérifier que l'utilisateur est le propriétaire du créneau
        slot = self.get_object()
        return slot.user == self.request.user
    
    def get_queryset(self):
        return AppointmentSlot.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, _('Créneau de rendez-vous supprimé.'))
        return reverse('appointments:manage_slots')

class AppointmentExceptionCreateView(AppointmentExceptionBaseView, CreateView):
    template_name = 'appointments/exception_form.html'
    fields = ['date', 'reason', 'is_all_day', 'start_time', 'end_time']
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _('Exception de disponibilité créée avec succès.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:manage_slots')

class AppointmentExceptionUpdateView(AppointmentExceptionBaseView, UserPassesTestMixin, UpdateView):
    template_name = 'appointments/exception_form.html'
    fields = ['date', 'reason', 'is_all_day', 'start_time', 'end_time']
    
    def test_func(self):
        # Vérifier que l'utilisateur est le propriétaire de l'exception
        exception = self.get_object()
        return exception.user == self.request.user
    
    def get_queryset(self):
        return AppointmentException.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, _('Exception de disponibilité mise à jour avec succès.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:manage_slots')

class AppointmentExceptionDeleteView(AppointmentExceptionBaseView, UserPassesTestMixin, DeleteView):
    template_name = 'appointments/exception_confirm_delete.html'
    
    def test_func(self):
        # Vérifier que l'utilisateur est le propriétaire de l'exception
        exception = self.get_object()
        return exception.user == self.request.user
    
    def get_queryset(self):
        return AppointmentException.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, _('Exception de disponibilité supprimée.'))
        return reverse('appointments:manage_slots')

# Viewsets REST API
class AppointmentSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les créneaux de rendez-vous.
    """
    serializer_class = AppointmentSlotSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user')
        if user_id:
            return AppointmentSlot.objects.filter(user_id=user_id, is_active=True)
        return AppointmentSlot.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class AppointmentExceptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les exceptions de disponibilité.
    """
    serializer_class = AppointmentExceptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user')
        if user_id:
            return AppointmentException.objects.filter(user_id=user_id)
        return AppointmentException.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)