from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, AppointmentSlot, AppointmentException, AppointmentReminder

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester_name', 'recipient_name', 'schedule_time', 'status', 'meeting_type')
    list_filter = ('status', 'meeting_type', 'schedule_time')
    search_fields = ('title', 'requester__first_name', 'requester__last_name', 
                    'recipient__first_name', 'recipient__last_name', 'purpose')
    date_hierarchy = 'schedule_time'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('title', 'requester', 'recipient', 'status')
        }),
        (_('Planification'), {
            'fields': ('schedule_time', 'end_time', 'duration_minutes', 'meeting_type', 'location', 'meeting_link')
        }),
        (_('Détails'), {
            'fields': ('purpose', 'notes')
        }),
        (_('Feedback'), {
            'fields': ('requester_feedback', 'recipient_feedback'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at', 'reminder_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def requester_name(self, obj):
        return obj.requester.get_full_name()
    requester_name.short_description = _('Demandeur')
    
    def recipient_name(self, obj):
        return obj.recipient.get_full_name()
    recipient_name.short_description = _('Destinataire')
    
    # Actions personnalisées
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'mark_as_completed']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, _(f'{updated} rendez-vous ont été confirmés.'))
    mark_as_confirmed.short_description = _('Marquer comme confirmés')
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'confirmed', 'rescheduled']).update(status='cancelled')
        self.message_user(request, _(f'{updated} rendez-vous ont été annulés.'))
    mark_as_cancelled.short_description = _('Marquer comme annulés')
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status__in=['confirmed', 'rescheduled']).update(status='completed')
        self.message_user(request, _(f'{updated} rendez-vous ont été marqués comme terminés.'))
    mark_as_completed.short_description = _('Marquer comme terminés')

@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'day_of_week_display', 'start_time', 'end_time', 'is_active', 'recurring')
    list_filter = ('is_active', 'recurring', 'day_of_week')
    search_fields = ('user__first_name', 'user__last_name', 'location')
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = _('Utilisateur')
    
    def day_of_week_display(self, obj):
        days = {
            0: _('Lundi'),
            1: _('Mardi'),
            2: _('Mercredi'),
            3: _('Jeudi'),
            4: _('Vendredi'),
            5: _('Samedi'),
            6: _('Dimanche'),
        }
        return days.get(obj.day_of_week)
    day_of_week_display.short_description = _('Jour de la semaine')
    
    actions = ['activate_slots', 'deactivate_slots']
    
    def activate_slots(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} créneaux ont été activés.'))
    activate_slots.short_description = _('Activer les créneaux sélectionnés')
    
    def deactivate_slots(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} créneaux ont été désactivés.'))
    deactivate_slots.short_description = _('Désactiver les créneaux sélectionnés')

@admin.register(AppointmentException)
class AppointmentExceptionAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'date', 'is_all_day', 'start_time', 'end_time', 'reason')
    list_filter = ('is_all_day', 'date')
    search_fields = ('user__first_name', 'user__last_name', 'reason')
    date_hierarchy = 'date'
    
    def user_name(self, obj):
        return obj.user.get_full_name()
    user_name.short_description = _('Utilisateur')

@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ('appointment_title', 'reminder_type', 'minutes_before', 'sent', 'sent_at')
    list_filter = ('reminder_type', 'sent')
    search_fields = ('appointment__title', 'appointment__requester__first_name', 
                    'appointment__requester__last_name', 'appointment__recipient__first_name', 
                    'appointment__recipient__last_name')
    readonly_fields = ('sent', 'sent_at', 'created_at')
    
    def appointment_title(self, obj):
        return obj.appointment.title
    appointment_title.short_description = _('Rendez-vous')
    
    actions = ['mark_as_sent']
    
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(sent=False).update(sent=True, sent_at=timezone.now())
        self.message_user(request, _(f'{updated} rappels ont été marqués comme envoyés.'))
    mark_as_sent.short_description = _('Marquer comme envoyés')