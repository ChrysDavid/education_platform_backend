import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

# Validateur pour les numéros de téléphone
phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message=_("Le numéro de téléphone doit être au format : '+999999999'. 9 à 15 chiffres autorisés.")
)

# Validateur pour les mots de passe
def validate_password_strength(password):
    """
    Valide la robustesse d'un mot de passe.
    
    Args:
        password: Le mot de passe à valider
        
    Raises:
        ValidationError: Si le mot de passe n'est pas assez robuste
    """
    # Vérifier la longueur minimale
    if len(password) < 8:
        raise ValidationError(
            _("Le mot de passe doit contenir au moins 8 caractères."),
            code='password_too_short',
        )
    
    # Vérifier la présence d'au moins un chiffre
    if not any(char.isdigit() for char in password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins un chiffre."),
            code='password_no_digit',
        )
    
    # Vérifier la présence d'au moins une lettre majuscule
    if not any(char.isupper() for char in password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins une lettre majuscule."),
            code='password_no_upper',
        )
    
    # Vérifier la présence d'au moins une lettre minuscule
    if not any(char.islower() for char in password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins une lettre minuscule."),
            code='password_no_lower',
        )
    
    # Vérifier la présence d'au moins un caractère spécial
    if not any(not char.isalnum() for char in password):
        raise ValidationError(
            _("Le mot de passe doit contenir au moins un caractère spécial."),
            code='password_no_special',
        )

# Validateur pour les adresses email
def validate_email_domain(email):
    """
    Valide le domaine d'une adresse email.
    
    Args:
        email: L'adresse email à valider
        
    Raises:
        ValidationError: Si le domaine n'est pas autorisé
    """
    # Liste des domaines interdits (exemple)
    banned_domains = [
        'tempmail.com',
        'throwawaymail.com',
        'mailinator.com',
        'guerrillamail.com',
    ]
    
    domain = email.split('@')[-1].lower()
    
    if domain in banned_domains:
        raise ValidationError(
            _("L'adresse email utilise un domaine non autorisé."),
            code='invalid_email_domain',
        )

# Validateur pour les noms et prénoms
def validate_name(name):
    """
    Valide un nom ou prénom.
    
    Args:
        name: Le nom à valider
        
    Raises:
        ValidationError: Si le nom contient des caractères interdits
    """
    # Vérifier la longueur minimale
    if len(name) < 2:
        raise ValidationError(
            _("Le nom doit contenir au moins 2 caractères."),
            code='name_too_short',
        )
    
    # Vérifier les caractères autorisés (lettres, espaces, tirets, apostrophes)
    if not re.match(r"^[\p{L}\s\-']+$", name, re.UNICODE):
        raise ValidationError(
            _("Le nom ne doit contenir que des lettres, espaces, tirets et apostrophes."),
            code='invalid_name_chars',
        )