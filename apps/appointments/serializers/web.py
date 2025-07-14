from rest_framework import serializers
from ..models import AppointmentSlot, AppointmentException
from django.utils.translation import gettext_lazy as _

class AppointmentSlotSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentSlot
        fields = ['id', 'user', 'day_of_week', 'day_of_week_display', 'start_time', 
                  'end_time', 'location', 'is_active', 'recurring', 'start_date', 
                  'end_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_day_of_week_display(self, obj):
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
    
    def validate(self, data):
        # Vérifier que l'heure de fin est après l'heure de début
        if data.get('end_time') and data.get('start_time') and data['end_time'] <= data['start_time']:
            raise serializers.ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))
        
        # Vérifier que les dates sont cohérentes pour les créneaux non récurrents
        if not data.get('recurring', True) and data.get('start_date') and data.get('end_date') and data['end_date'] < data['start_date']:
            raise serializers.ValidationError(_('La date de fin doit être après la date de début.'))
        
        return data

class AppointmentExceptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentException
        fields = ['id', 'user', 'date', 'reason', 'is_all_day', 'start_time', 
                  'end_time', 'created_at']
        read_only_fields = ['created_at']
    
    def validate(self, data):
        # Si ce n'est pas toute la journée, les heures de début et de fin sont requises
        if not data.get('is_all_day', True):
            if not data.get('start_time'):
                raise serializers.ValidationError(_('L\'heure de début est requise pour les exceptions partielles.'))
            if not data.get('end_time'):
                raise serializers.ValidationError(_('L\'heure de fin est requise pour les exceptions partielles.'))
            if data.get('end_time') <= data.get('start_time'):
                raise serializers.ValidationError(_('L\'heure de fin doit être après l\'heure de début.'))
        
        return data