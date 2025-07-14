from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, View, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from datetime import datetime, timedelta, date
import calendar

from ..models import Appointment, AppointmentException, AppointmentSlot
from ..serializers import (
    AppointmentSerializer, AppointmentCreateSerializer, AppointmentUpdateSerializer,
    AvailabilitySerializer, NextAvailableSlotSerializer
)
from ..permissions import IsRecipientOrRequester

User = get_user_model()

# Classes de base pour les vues Django
class AppointmentBaseView(LoginRequiredMixin):
    model = Appointment
    context_object_name = 'appointment'

class AppointmentCalendarView(AppointmentBaseView, View):
    template_name = 'appointments/calendar.html'
    
    def get(self, request, *args, **kwargs):
        # Par défaut, afficher le mois en cours
        now = timezone.now()
        year = int(request.GET.get('year', now.year))
        month = int(request.GET.get('month', now.month))
        
        # Créer un calendrier pour le mois spécifié
        cal = calendar.monthcalendar(year, month)
        
        # Récupérer tous les rendez-vous de l'utilisateur pour ce mois
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        appointments = Appointment.objects.filter(
            (Q(requester=request.user) | Q(recipient=request.user)) &
            (Q(schedule_time__gte=start_date) & Q(schedule_time__lt=end_date))
        ).order_by('schedule_time')
        
        # Organiser les rendez-vous par jour
        appointments_by_day = {}
        for appointment in appointments:
            day = appointment.schedule_time.day
            if day not in appointments_by_day:
                appointments_by_day[day] = []
            appointments_by_day[day].append(appointment)
        
        context = {
            'calendar': cal,
            'appointments_by_day': appointments_by_day,
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'prev_month': (month - 1) if month > 1 else 12,
            'prev_year': year if month > 1 else year - 1,
            'next_month': (month + 1) if month < 12 else 1,
            'next_year': year if month < 12 else year + 1,
        }
        
        return render(request, self.template_name, context)

class MyAppointmentsView(AppointmentBaseView, ListView):
    model = Appointment
    template_name = 'appointments/my_appointments.html'
    context_object_name = 'appointments'
    paginate_by = 10
    
    def get_queryset(self):
        user = self.request.user
        filter_type = self.request.GET.get('filter', 'upcoming')
        
        queryset = Appointment.objects.filter(
            Q(requester=user) | Q(recipient=user)
        )
        
        if filter_type == 'upcoming':
            queryset = queryset.filter(
                schedule_time__gte=timezone.now(),
                status__in=['pending', 'confirmed', 'rescheduled']
            )
        elif filter_type == 'past':
            queryset = queryset.filter(
                Q(schedule_time__lt=timezone.now()) |
                Q(status__in=['completed', 'cancelled', 'no_show'])
            )
        elif filter_type == 'pending':
            queryset = queryset.filter(status='pending')
        elif filter_type == 'confirmed':
            queryset = queryset.filter(status__in=['confirmed', 'rescheduled'])
        
        return queryset.order_by('schedule_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.request.GET.get('filter', 'upcoming')
        context['total_appointments'] = self.get_queryset().count()
        return context

class AppointmentDetailView(AppointmentBaseView, DetailView):
    template_name = 'appointments/appointment_detail.html'
    
    def get_queryset(self):
        # L'utilisateur ne peut voir que ses propres rendez-vous
        return Appointment.objects.filter(
            Q(requester=self.request.user) | Q(recipient=self.request.user)
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        appointment = self.get_object()
        
        # Vérifier si l'utilisateur est le demandeur ou le destinataire
        context['is_requester'] = appointment.requester == self.request.user
        context['is_recipient'] = appointment.recipient == self.request.user
        
        # Ajouter des informations sur les actions possibles
        context['can_cancel'] = appointment.status in ['pending', 'confirmed', 'rescheduled']
        context['can_confirm'] = appointment.status == 'pending' and context['is_recipient']
        context['can_complete'] = appointment.status in ['confirmed', 'rescheduled'] and context['is_recipient']
        context['can_reschedule'] = appointment.status in ['pending', 'confirmed', 'rescheduled']
        
        return context

class AppointmentCreateView(AppointmentBaseView, CreateView):
    template_name = 'appointments/appointment_form.html'
    fields = ['recipient', 'title', 'schedule_time', 'duration_minutes', 
              'purpose', 'location', 'meeting_type', 'meeting_link']
    
    def form_valid(self, form):
        form.instance.requester = self.request.user
        
        # Calcul automatique de l'heure de fin
        if form.instance.schedule_time:
            form.instance.end_time = form.instance.schedule_time + timedelta(minutes=form.instance.duration_minutes)
        
        messages.success(self.request, _('Rendez-vous créé avec succès.'))
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filtrer les destinataires possibles (exclure l'utilisateur actuel)
        form.fields['recipient'].queryset = User.objects.exclude(id=self.request.user.id)
        return form
    
    def get_success_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.object.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Si un utilisateur destinataire est spécifié dans l'URL
        recipient_id = self.request.GET.get('recipient')
        if recipient_id:
            try:
                initial['recipient'] = User.objects.get(pk=recipient_id)
            except User.DoesNotExist:
                pass
        
        # Si une date/heure est spécifiée dans l'URL
        schedule_time = self.request.GET.get('schedule_time')
        if schedule_time:
            try:
                initial['schedule_time'] = datetime.fromisoformat(schedule_time)
            except ValueError:
                pass
        
        return initial

class AppointmentCancelView(AppointmentBaseView, UserPassesTestMixin, View):
    def test_func(self):
        # Vérifier que l'utilisateur est le demandeur ou le destinataire
        appointment = get_object_or_404(Appointment, pk=self.kwargs['pk'])
        return (appointment.requester == self.request.user or 
                appointment.recipient == self.request.user)
    
    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs['pk'])
        
        if appointment.status in ['cancelled', 'completed', 'no_show']:
            messages.error(request, _('Ce rendez-vous ne peut pas être annulé.'))
            return redirect('appointments:detail', pk=appointment.pk)
        
        appointment.status = 'cancelled'
        appointment.save()
        
        messages.success(request, _('Le rendez-vous a été annulé.'))
        return redirect('appointments:detail', pk=appointment.pk)

class AppointmentConfirmView(AppointmentBaseView, UserPassesTestMixin, View):
    def test_func(self):
        # Seul le destinataire peut confirmer un rendez-vous
        appointment = get_object_or_404(Appointment, pk=self.kwargs['pk'])
        return appointment.recipient == self.request.user
    
    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs['pk'])
        
        if appointment.status != 'pending':
            messages.error(request, _('Ce rendez-vous ne peut pas être confirmé.'))
            return redirect('appointments:detail', pk=appointment.pk)
        
        appointment.status = 'confirmed'
        appointment.save()
        
        messages.success(request, _('Le rendez-vous a été confirmé.'))
        return redirect('appointments:detail', pk=appointment.pk)

class AppointmentCompleteView(AppointmentBaseView, UserPassesTestMixin, View):
    def test_func(self):
        # Seul le destinataire peut marquer un rendez-vous comme terminé
        appointment = get_object_or_404(Appointment, pk=self.kwargs['pk'])
        return appointment.recipient == self.request.user
    
    def post(self, request, *args, **kwargs):
        appointment = get_object_or_404(Appointment, pk=kwargs['pk'])
        
        if appointment.status not in ['confirmed', 'rescheduled']:
            messages.error(request, _('Ce rendez-vous ne peut pas être marqué comme terminé.'))
            return redirect('appointments:detail', pk=appointment.pk)
        
        appointment.status = 'completed'
        appointment.save()
        
        messages.success(request, _('Le rendez-vous a été marqué comme terminé.'))
        return redirect('appointments:detail', pk=appointment.pk)

class AppointmentRescheduleView(AppointmentBaseView, UserPassesTestMixin, UpdateView):
    template_name = 'appointments/appointment_reschedule.html'
    fields = ['schedule_time', 'duration_minutes']
    
    def test_func(self):
        # Vérifier que l'utilisateur est le demandeur ou le destinataire
        appointment = self.get_object()
        return (appointment.requester == self.request.user or 
                appointment.recipient == self.request.user)
    
    def get_queryset(self):
        # L'utilisateur ne peut reprogrammer que les rendez-vous en attente ou confirmés
        return Appointment.objects.filter(
            (Q(requester=self.request.user) | Q(recipient=self.request.user)) &
            Q(status__in=['pending', 'confirmed', 'rescheduled'])
        )
    
    def form_valid(self, form):
        # Recalculer l'heure de fin
        if form.instance.schedule_time:
            form.instance.end_time = form.instance.schedule_time + timedelta(minutes=form.instance.duration_minutes)
        
        # Mettre à jour le statut
        if form.instance.status == 'confirmed':
            form.instance.status = 'rescheduled'
        
        messages.success(self.request, _('Le rendez-vous a été reprogrammé.'))
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.object.pk})

# Vues API REST
class UserAvailabilityView(APIView):
    """
    Vue API pour récupérer les disponibilités d'un utilisateur à une date donnée.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id, format=None):
        # Vérifier que l'utilisateur existe
        recipient = get_object_or_404(User, pk=user_id)
        
        # Récupérer la date demandée (par défaut aujourd'hui)
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        try:
            requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': _('Format de date invalide. Utilisez YYYY-MM-DD.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier que la date est dans le futur
        if requested_date < timezone.now().date():
            return Response(
                {'error': _('La date doit être dans le futur.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les créneaux disponibles pour ce jour de la semaine
        weekday = requested_date.weekday()
        slots = AppointmentSlot.objects.filter(
            user=recipient,
            day_of_week=weekday,
            is_active=True
        )
        
        # Vérifier si la date est dans les plages de dates des créneaux
        valid_slots = []
        for slot in slots:
            if not slot.recurring:
                if slot.start_date and slot.start_date > requested_date:
                    continue
                if slot.end_date and slot.end_date < requested_date:
                    continue
            valid_slots.append(slot)
        
        # Vérifier s'il y a des exceptions pour cette date
        exceptions = AppointmentException.objects.filter(
            user=recipient,
            date=requested_date
        )
        
        # Créer une liste de créneaux disponibles
        available_slots = []
        for slot in valid_slots:
            # Vérifier s'il y a une exception qui couvre toute la journée
            if exceptions.filter(is_all_day=True).exists():
                continue
            
            # Préparer les heures de début et de fin
            start_datetime = datetime.combine(requested_date, slot.start_time)
            end_datetime = datetime.combine(requested_date, slot.end_time)
            
            # Diviser le créneau en intervalles de 30 minutes
            current = start_datetime
            while current < end_datetime:
                # Vérifier si ce créneau horaire est couvert par une exception
                if any(
                    not e.is_all_day and
                    datetime.combine(requested_date, e.start_time) <= current and
                    datetime.combine(requested_date, e.end_time) > current
                    for e in exceptions
                ):
                    current += timedelta(minutes=30)
                    continue
                
                # Vérifier s'il y a déjà un rendez-vous à cette heure
                if Appointment.objects.filter(
                    recipient=recipient,
                    schedule_time__lte=current,
                    end_time__gt=current,
                    status__in=['confirmed', 'rescheduled']
                ).exists():
                    current += timedelta(minutes=30)
                    continue
                
                # Ajouter le créneau disponible
                available_slots.append({
                    'start_time': current.strftime('%H:%M'),
                    'end_time': (current + timedelta(minutes=30)).strftime('%H:%M'),
                    'timestamp': current.isoformat()
                })
                
                current += timedelta(minutes=30)
        
        # Préparer la réponse
        serializer = AvailabilitySerializer({
            'date': requested_date,
            'available_slots': available_slots
        })
        
        return Response(serializer.data)

class NextAvailableSlotView(APIView):
    """
    Vue API pour récupérer le prochain créneau disponible pour un utilisateur.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, user_id, format=None):
        # Vérifier que l'utilisateur existe
        recipient = get_object_or_404(User, pk=user_id)
        
        # Date de début de recherche (par défaut aujourd'hui)
        start_date = timezone.now().date()
        
        # Nombre maximum de jours à vérifier
        max_days = int(request.query_params.get('max_days', 30))
        
        # Chercher le prochain créneau disponible
        next_slot = None
        next_date = None
        
        for day_offset in range(max_days):
            check_date = start_date + timedelta(days=day_offset)
            
            # Simuler une requête pour récupérer les disponibilités
            temp_request = type('TempRequest', (), {})()
            temp_request.query_params = {'date': check_date.isoformat()}
            
            response = self.get_availability(recipient, temp_request)
            
            if response.data['available_slots']:
                next_slot = response.data['available_slots'][0]
                next_date = check_date
                break
        
        # Préparer la réponse
        if next_slot:
            next_datetime = datetime.fromisoformat(next_slot['timestamp'])
            serializer = NextAvailableSlotSerializer({
                'next_available_datetime': next_datetime,
                'next_available_date': next_date,
                'next_available_slot': next_slot
            })
            return Response(serializer.data)
        else:
            return Response({
                'next_available_datetime': None,
                'next_available_date': None,
                'next_available_slot': None,
                'message': _('Aucun créneau disponible dans les {} prochains jours.').format(max_days)
            })
    
    def get_availability(self, recipient, request):
        """
        Réutilise la logique de UserAvailabilityView pour récupérer les disponibilités.
        """
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        requested_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Récupérer les créneaux disponibles pour ce jour de la semaine
        weekday = requested_date.weekday()
        slots = AppointmentSlot.objects.filter(
            user=recipient,
            day_of_week=weekday,
            is_active=True
        )
        
        # Vérifier si ASSISTANT: la date est dans les plages de dates des créneaux
        valid_slots = []
        for slot in slots:
            if not slot.recurring:
                if slot.start_date and slot.start_date > requested_date:
                    continue
                if slot.end_date and slot.end_date < requested_date:
                    continue
            valid_slots.append(slot)
        
        # Vérifier s'il y a des exceptions pour cette date
        exceptions = AppointmentException.objects.filter(
            user=recipient,
            date=requested_date
        )
        
        # Créer une liste de créneaux disponibles
        available_slots = []
        for slot in valid_slots:
            # Vérifier s'il y a une exception qui couvre toute la journée
            if exceptions.filter(is_all_day=True).exists():
                continue
            
            # Préparer les heures de début et de fin
            start_datetime = datetime.combine(requested_date, slot.start_time)
            end_datetime = datetime.combine(requested_date, slot.end_time)
            
            # Diviser le créneau en intervalles de 30 minutes
            current = start_datetime
            while current < end_datetime:
                # Vérifier si ce créneau horaire est couvert par une exception
                if any(
                    not e.is_all_day and
                    datetime.combine(requested_date, e.start_time) <= current and
                    datetime.combine(requested_date, e.end_time) > current
                    for e in exceptions
                ):
                    current += timedelta(minutes=30)
                    continue
                
                # Vérifier s'il y a déjà un rendez-vous à cette heure
                if Appointment.objects.filter(
                    recipient=recipient,
                    schedule_time__lte=current,
                    end_time__gt=current,
                    status__in=['confirmed', 'rescheduled']
                ).exists():
                    current += timedelta(minutes=30)
                    continue
                
                # Si c'est aujourd'hui, ne pas retourner les créneaux passés
                if requested_date == timezone.now().date() and current <= timezone.now():
                    current += timedelta(minutes=30)
                    continue
                
                # Ajouter le créneau disponible
                available_slots.append({
                    'start_time': current.strftime('%H:%M'),
                    'end_time': (current + timedelta(minutes=30)).strftime('%H:%M'),
                    'timestamp': current.isoformat()
                })
                
                current += timedelta(minutes=30)
        
        # Préparer la réponse
        return Response({
            'date': requested_date,
            'available_slots': available_slots
        })

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour les rendez-vous.
    """
    permission_classes = [permissions.IsAuthenticated, IsRecipientOrRequester]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'purpose', 'location']
    ordering_fields = ['schedule_time', 'created_at', 'status']
    ordering = ['-schedule_time']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(
            Q(requester=user) | Q(recipient=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        
        # Vérifier que l'utilisateur est le destinataire
        if appointment.recipient != request.user:
            return Response(
                {'error': _('Seul le destinataire peut confirmer un rendez-vous.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le rendez-vous est en attente
        if appointment.status != 'pending':
            return Response(
                {'error': _('Ce rendez-vous ne peut pas être confirmé.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.confirm()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        
        # Vérifier que le rendez-vous peut être annulé
        if appointment.status in ['cancelled', 'completed', 'no_show']:
            return Response(
                {'error': _('Ce rendez-vous ne peut pas être annulé.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.cancel()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        
        # Vérifier que l'utilisateur est le destinataire
        if appointment.recipient != request.user:
            return Response(
                {'error': _('Seul le destinataire peut marquer un rendez-vous comme terminé.')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifier que le rendez-vous peut être marqué comme terminé
        if appointment.status not in ['confirmed', 'rescheduled']:
            return Response(
                {'error': _('Ce rendez-vous ne peut pas être marqué comme terminé.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.complete()
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        appointment = self.get_object()
        
        # Vérifier que le rendez-vous peut être reprogrammé
        if appointment.status not in ['pending', 'confirmed', 'rescheduled']:
            return Response(
                {'error': _('Ce rendez-vous ne peut pas être reprogrammé.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier les données de reprogrammation
        serializer = self.get_serializer(appointment, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if 'schedule_time' not in request.data:
            return Response(
                {'error': _('La date et l\'heure de rendez-vous sont requises.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convertir la chaîne en datetime
        try:
            new_schedule_time = datetime.fromisoformat(request.data['schedule_time'])
        except ValueError:
            return Response(
                {'error': _('Format de date et heure invalide.')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtenir la nouvelle durée si fournie
        new_duration_minutes = request.data.get('duration_minutes', appointment.duration_minutes)
        
        # Reprogrammer le rendez-vous
        appointment.reschedule(new_schedule_time, new_duration_minutes)
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        queryset = self.get_queryset().filter(
            schedule_time__gte=timezone.now(),
            status__in=['pending', 'confirmed', 'rescheduled']
        ).order_by('schedule_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        queryset = self.get_queryset().filter(
            Q(schedule_time__lt=timezone.now()) |
            Q(status__in=['completed', 'cancelled', 'no_show'])
        ).order_by('-schedule_time')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)