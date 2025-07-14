from rest_framework import serializers
from ..models import Appointment, AppointmentReminder
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .base import AppointmentReminderSerializer

class AppointmentSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    meeting_type_display = serializers.CharField(source='get_meeting_type_display', read_only=True)
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'requester', 'recipient', 'requester_name', 'recipient_name',
                  'title', 'schedule_time', 'end_time', 'duration_minutes', 
                  'purpose', 'location', 'meeting_type', 'meeting_type_display',
                  'meeting_link', 'status', 'status_display', 'notes',
                  'requester_feedback', 'recipient_feedback', 'created_at',
                  'updated_at', 'reminders', 'is_past', 'is_upcoming']
        read_only_fields = ['created_at', 'updated_at', 'is_past', 'is_upcoming']
    
    def get_requester_name(self, obj):
        return obj.requester.get_full_name()
    
    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name()
    
    def validate(self, data):
        # Vérifier que requester et recipient sont différents
        if data.get('requester') == data.get('recipient'):
            raise serializers.ValidationError(_('Le demandeur et le destinataire ne peuvent pas être la même personne.'))
        
        # Vérifier que le rendez-vous est dans le futur lors de la création
        schedule_time = data.get('schedule_time')
        if schedule_time and not self.instance and schedule_time < timezone.now():
            raise serializers.ValidationError(_('La date et l\'heure du rendez-vous doivent être dans le futur.'))
        
        # Vérifier que l'heure de fin est après l'heure de début
        end_time = data.get('end_time')
        if schedule_time and end_time and end_time <= schedule_time:
            raise serializers.ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))
        
        return data

class AppointmentCreateSerializer(AppointmentSerializer):
    """
    Sérialiseur pour la création de rendez-vous avec des validations supplémentaires
    et la possibilité de créer des rappels.
    """
    reminders = AppointmentReminderSerializer(many=True, required=False)
    
    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + ['reminder_sent']
        read_only_fields = AppointmentSerializer.Meta.read_only_fields + ['reminder_sent']
    
    def create(self, validated_data):
        reminders_data = validated_data.pop('reminders', [])
        appointment = Appointment.objects.create(**validated_data)
        
        # Créer les rappels
        for reminder_data in reminders_data:
            AppointmentReminder.objects.create(appointment=appointment, **reminder_data)
        
        return appointment

class AppointmentUpdateSerializer(AppointmentSerializer):
    """
    Sérialiseur pour la mise à jour de rendez-vous.
    """
    class Meta(AppointmentSerializer.Meta):
        read_only_fields = AppointmentSerializer.Meta.read_only_fields + ['requester', 'recipient']
    
    def validate_status(self, value):
        if self.instance and self.instance.status == 'cancelled' and value != 'cancelled':
            raise serializers.ValidationError(_('Un rendez-vous annulé ne peut pas être réactivé.'))
        if self.instance and self.instance.status == 'completed' and value != 'completed':
            raise serializers.ValidationError(_('Un rendez-vous terminé ne peut pas être modifié.'))
        return value

class AvailabilitySerializer(serializers.Serializer):
    date = serializers.DateField(required=True)
    available_slots = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            allow_empty=True
        )
    )

class NextAvailableSlotSerializer(serializers.Serializer):
    next_available_datetime = serializers.DateTimeField(allow_null=True)
    next_available_date = serializers.DateField(allow_null=True)
    next_available_slot = serializers.DictField(
        child=serializers.CharField(),
        allow_null=True
    )