from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    NotificationType, UserNotificationPreference, Notification, 
    NotificationTemplate, DeviceToken
)


class NotificationTypeForm(forms.ModelForm):
    """
    Formulaire pour les types de notification.
    """
    class Meta:
        model = NotificationType
        fields = [
            'code', 'name', 'description', 'title_template', 'body_template',
            'has_email', 'has_in_app', 'has_push', 'icon', 'color',
            'is_active', 'default_user_preference', 'order'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'title_template': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'has_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_in_app': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_user_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserNotificationPreferenceForm(forms.ModelForm):
    """
    Formulaire pour les préférences de notification des utilisateurs.
    """
    class Meta:
        model = UserNotificationPreference
        fields = ['email_enabled', 'in_app_enabled', 'push_enabled']
        widgets = {
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationTemplateForm(forms.ModelForm):
    """
    Formulaire pour les modèles de notification.
    """
    class Meta:
        model = NotificationTemplate
        fields = [
            'code', 'name', 'description', 'notification_type',
            'subject_template', 'email_template', 'title_template',
            'body_template', 'is_active'
        ]
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'email_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'title_template': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer uniquement les types de notification actifs
        self.fields['notification_type'].queryset = NotificationType.objects.filter(is_active=True)


class DeviceTokenForm(forms.ModelForm):
    """
    Formulaire pour les tokens d'appareil.
    """
    class Meta:
        model = DeviceToken
        fields = ['user', 'token', 'platform', 'device_name', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'token': forms.TextInput(attrs={'class': 'form-control'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'device_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationPreferencesUpdateForm(forms.Form):
    """
    Formulaire pour mettre à jour les préférences de notification en masse.
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if not self.user:
            return
        
        # Ajouter un champ pour chaque type de notification
        for notification_type in NotificationType.objects.filter(is_active=True).order_by('order', 'name'):
            # Récupérer les préférences existantes ou créer des nouvelles
            try:
                preference = UserNotificationPreference.objects.get(
                    user=self.user,
                    notification_type=notification_type
                )
            except UserNotificationPreference.DoesNotExist:
                preference = UserNotificationPreference(
                    user=self.user,
                    notification_type=notification_type,
                    email_enabled=notification_type.default_user_preference,
                    in_app_enabled=notification_type.default_user_preference,
                    push_enabled=notification_type.default_user_preference
                )
            
            # Ajouter les champs pour ce type de notification
            prefix = f"notification_{notification_type.id}"
            
            if notification_type.has_email:
                self.fields[f"{prefix}_email"] = forms.BooleanField(
                    label=_("Email"),
                    required=False,
                    initial=preference.email_enabled,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
            
            if notification_type.has_in_app:
                self.fields[f"{prefix}_in_app"] = forms.BooleanField(
                    label=_("Dans l'application"),
                    required=False,
                    initial=preference.in_app_enabled,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
            
            if notification_type.has_push:
                self.fields[f"{prefix}_push"] = forms.BooleanField(
                    label=_("Push"),
                    required=False,
                    initial=preference.push_enabled,
                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                )
    
    def save(self):
        """
        Enregistre les préférences de notification.
        """
        if not self.user:
            return
        
        for notification_type in NotificationType.objects.filter(is_active=True):
            prefix = f"notification_{notification_type.id}"
            
            # Initialiser avec les valeurs par défaut
            email_enabled = notification_type.default_user_preference
            in_app_enabled = notification_type.default_user_preference
            push_enabled = notification_type.default_user_preference
            
            # Mettre à jour avec les valeurs du formulaire
            if notification_type.has_email and f"{prefix}_email" in self.cleaned_data:
                email_enabled = self.cleaned_data[f"{prefix}_email"]
            
            if notification_type.has_in_app and f"{prefix}_in_app" in self.cleaned_data:
                in_app_enabled = self.cleaned_data[f"{prefix}_in_app"]
            
            if notification_type.has_push and f"{prefix}_push" in self.cleaned_data:
                push_enabled = self.cleaned_data[f"{prefix}_push"]
            
            # Créer ou mettre à jour la préférence
            UserNotificationPreference.objects.update_or_create(
                user=self.user,
                notification_type=notification_type,
                defaults={
                    'email_enabled': email_enabled,
                    'in_app_enabled': in_app_enabled,
                    'push_enabled': push_enabled
                }
            )