from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

class Appointment(models.Model):
    """
    Modèle représentant un rendez-vous entre deux utilisateurs.
    Par exemple, un étudiant peut prendre rendez-vous avec un conseiller d'orientation,
    ou un professeur peut programmer une consultation avec un étudiant.
    """
    STATUS_CHOICES = (
        ('pending', _('En attente')),
        ('confirmed', _('Confirmé')),
        ('rescheduled', _('Reporté')),
        ('cancelled', _('Annulé')),
        ('completed', _('Terminé')),
        ('no_show', _('Absence')),
    )
    
    MEETING_TYPE_CHOICES = (
        ('in_person', _('En personne')),
        ('video', _('Vidéoconférence')),
        ('phone', _('Téléphone')),
        ('chat', _('Chat textuel')),
    )
    
    # Relations avec les utilisateurs
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requested_appointments',
        verbose_name=_('demandeur')
    )
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_appointments',
        verbose_name=_('destinataire')
    )
    
    # Informations sur le rendez-vous
    title = models.CharField(_('titre'), max_length=255)
    schedule_time = models.DateTimeField(_('date et heure prévues'))
    end_time = models.DateTimeField(_('heure de fin'), null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(_('durée (minutes)'), default=30)
    purpose = models.TextField(_('objectif'), blank=True)
    location = models.CharField(_('lieu'), max_length=255, blank=True)
    meeting_type = models.CharField(
        _('type de rencontre'),
        max_length=20,
        choices=MEETING_TYPE_CHOICES,
        default='in_person'
    )
    meeting_link = models.URLField(_('lien de la réunion'), blank=True, null=True)
    
    # État du rendez-vous
    status = models.CharField(
        _('statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Dates de création et modification
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    # Notes et feedback
    notes = models.TextField(_('notes'), blank=True)
    requester_feedback = models.TextField(_('feedback du demandeur'), blank=True)
    recipient_feedback = models.TextField(_('feedback du destinataire'), blank=True)
    
    # Métadonnées
    reminder_sent = models.BooleanField(_('rappel envoyé'), default=False)
    
    class Meta:
        verbose_name = _('rendez-vous')
        verbose_name_plural = _('rendez-vous')
        ordering = ['-schedule_time']
        indexes = [
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['schedule_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.requester.get_full_name()} avec {self.recipient.get_full_name()} ({self.get_status_display()})"
    
    def clean(self):
        """Validation supplémentaire pour les rendez-vous."""
        # Vérifier que requester et recipient sont différents
        if self.requester == self.recipient:
            raise ValidationError(_('Le demandeur et le destinataire ne peuvent pas être la même personne.'))
        
        # Vérifier que le rendez-vous est dans le futur lors de la création
        if self.pk is None and self.schedule_time < timezone.now():
            raise ValidationError(_('La date et l\'heure du rendez-vous doivent être dans le futur.'))
        
        # Vérifier que l'heure de fin est après l'heure de début
        if self.end_time and self.end_time <= self.schedule_time:
            raise ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))
    
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour calculer l'heure de fin."""
        # Si l'heure de fin n'est pas spécifiée, calculer à partir de la durée
        if not self.end_time and self.schedule_time:
            import datetime
            self.end_time = self.schedule_time + datetime.timedelta(minutes=self.duration_minutes)
        
        # Appel à la méthode clean() pour la validation
        self.clean()
        
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Confirme le rendez-vous."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save(update_fields=['status', 'updated_at'])
    
    def reschedule(self, new_schedule_time, new_duration_minutes=None):
        """Replanifie le rendez-vous."""
        if self.status in ['pending', 'confirmed']:
            self.schedule_time = new_schedule_time
            if new_duration_minutes:
                self.duration_minutes = new_duration_minutes
            
            # Recalculer l'heure de fin
            import datetime
            self.end_time = self.schedule_time + datetime.timedelta(minutes=self.duration_minutes)
            
            self.status = 'rescheduled'
            self.save(update_fields=['schedule_time', 'duration_minutes', 'end_time', 'status', 'updated_at'])
    
    def cancel(self):
        """Annule le rendez-vous."""
        if self.status in ['pending', 'confirmed', 'rescheduled']:
            self.status = 'cancelled'
            self.save(update_fields=['status', 'updated_at'])
    
    def complete(self):
        """Marque le rendez-vous comme terminé."""
        if self.status in ['confirmed', 'rescheduled']:
            self.status = 'completed'
            self.save(update_fields=['status', 'updated_at'])
    
    def mark_no_show(self):
        """Marque le rendez-vous comme une absence."""
        if self.status in ['confirmed', 'rescheduled']:
            self.status = 'no_show'
            self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_past(self):
        """Indique si le rendez-vous est dans le passé."""
        return self.schedule_time < timezone.now()
    
    @property
    def is_upcoming(self):
        """Indique si le rendez-vous est à venir."""
        return self.schedule_time > timezone.now() and self.status in ['confirmed', 'rescheduled']
    
    @property
    def needs_action(self):
        """Indique si le rendez-vous nécessite une action."""
        return self.status == 'pending'

class AppointmentSlot(models.Model):
    """
    Modèle représentant un créneau de disponibilité pour les rendez-vous.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointment_slots',
        verbose_name=_('utilisateur')
    )
    
    day_of_week = models.PositiveSmallIntegerField(
        _('jour de la semaine'),
        choices=[
            (0, _('Lundi')),
            (1, _('Mardi')),
            (2, _('Mercredi')),
            (3, _('Jeudi')),
            (4, _('Vendredi')),
            (5, _('Samedi')),
            (6, _('Dimanche')),
        ]
    )
    
    start_time = models.TimeField(_('heure de début'))
    end_time = models.TimeField(_('heure de fin'))
    
    location = models.CharField(_('lieu'), max_length=255, blank=True)
    
    is_active = models.BooleanField(_('actif'), default=True)
    
    # Champs pour les créneaux récurrents
    recurring = models.BooleanField(_('récurrent'), default=True)
    start_date = models.DateField(_('date de début'), null=True, blank=True)
    end_date = models.DateField(_('date de fin'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('créneau de rendez-vous')
        verbose_name_plural = _('créneaux de rendez-vous')
        ordering = ['day_of_week', 'start_time', 'end_time']
        unique_together = ('user', 'day_of_week', 'start_time', 'end_time')
    
    def __str__(self):
        day_name = dict(self._meta.get_field('day_of_week').choices)[self.day_of_week]
        return f"{self.user.get_full_name()} - {day_name} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def clean(self):
        """Validation supplémentaire pour les créneaux."""
        # Vérifier que l'heure de fin est après l'heure de début
        if self.end_time <= self.start_time:
            raise ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))
        
        # Vérifier que les dates sont cohérentes pour les créneaux non récurrents
        if not self.recurring and self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(_('La date de fin doit être après la date de début.'))
    
    def is_available(self, date_time):
        """
        Vérifie si un créneau est disponible à une date et heure donnée.
        """
        if not self.is_active:
            return False
        
        # Vérifier si la date correspond au jour de la semaine
        if date_time.weekday() != self.day_of_week:
            return False
        
        # Vérifier si l'heure est dans le créneau
        time = date_time.time()
        if time < self.start_time or time >= self.end_time:
            return False
        
        # Vérifier les dates pour les créneaux non récurrents
        if not self.recurring:
            date = date_time.date()
            if self.start_date and date < self.start_date:
                return False
            if self.end_date and date > self.end_date:
                return False
        
        # Vérifier s'il y a déjà un rendez-vous à cette heure
        existing_appointments = Appointment.objects.filter(
            recipient=self.user,
            schedule_time__date=date_time.date(),
            status__in=['confirmed', 'rescheduled']
        )
        
        for appointment in existing_appointments:
            if (date_time >= appointment.schedule_time and 
                date_time < appointment.end_time):
                return False
        
        return True

class AppointmentException(models.Model):
    """
    Modèle représentant une exception aux créneaux réguliers.
    Par exemple, un jour férié ou une absence.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointment_exceptions',
        verbose_name=_('utilisateur')
    )
    
    date = models.DateField(_('date'))
    
    reason = models.CharField(_('raison'), max_length=255)
    is_all_day = models.BooleanField(_('toute la journée'), default=True)
    
    start_time = models.TimeField(_('heure de début'), null=True, blank=True)
    end_time = models.TimeField(_('heure de fin'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('exception de rendez-vous')
        verbose_name_plural = _('exceptions de rendez-vous')
        ordering = ['date', 'start_time']
        unique_together = ('user', 'date', 'start_time', 'end_time')
    
    def __str__(self):
        if self.is_all_day:
            return f"{self.user.get_full_name()} - {self.date} - {self.reason}"
        return f"{self.user.get_full_name()} - {self.date} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')} - {self.reason}"
    
    def clean(self):
        """Validation supplémentaire pour les exceptions."""
        # Si ce n'est pas toute la journée, les heures de début et de fin sont requises
        if not self.is_all_day:
            if not self.start_time:
                raise ValidationError(_('L\'heure de début est requise pour les exceptions partielles.'))
            if not self.end_time:
                raise ValidationError(_('L\'heure de fin est requise pour les exceptions partielles.'))
            if self.end_time <= self.start_time:
                raise ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))

class AppointmentReminder(models.Model):
    """
    Modèle représentant un rappel de rendez-vous.
    """
    REMINDER_TYPE_CHOICES = (
        ('email', _('Email')),
        ('push', _('Notification push')),
        ('sms', _('SMS')),
        ('all', _('Tous')),
    )
    
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('rendez-vous')
    )
    
    reminder_type = models.CharField(
        _('type de rappel'),
        max_length=10,
        choices=REMINDER_TYPE_CHOICES,
        default='email'
    )
    
    minutes_before = models.PositiveIntegerField(
        _('minutes avant'),
        default=60
    )
    
    sent = models.BooleanField(_('envoyé'), default=False)
    sent_at = models.DateTimeField(_('envoyé le'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('rappel de rendez-vous')
        verbose_name_plural = _('rappels de rendez-vous')
        ordering = ['appointment', 'minutes_before']
        unique_together = ('appointment', 'reminder_type', 'minutes_before')
    
    def __str__(self):
        return f"Rappel {self.get_reminder_type_display()} pour {self.appointment} ({self.minutes_before} minutes avant)"
    
    def mark_sent(self):
        """Marque le rappel comme envoyé."""
        self.sent = True
        self.sent_at = timezone.now()
        self.save(update_fields=['sent', 'sent_at'])
    
    @property
    def scheduled_time(self):
        """Calcule l'heure à laquelle le rappel doit être envoyé."""
        import datetime
        return self.appointment.schedule_time - datetime.timedelta(minutes=self.minutes_before)