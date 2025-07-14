from rest_framework import serializers
from ..models import AppointmentReminder
from django.utils.translation import gettext_lazy as _

class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = ['id', 'reminder_type', 'minutes_before', 'sent', 'sent_at']
        read_only_fields = ['sent', 'sent_at']