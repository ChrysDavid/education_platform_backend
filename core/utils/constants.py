"""
Constantes partagées pour tout le projet.
"""

# Formats de date
DATE_FORMAT = '%d/%m/%Y'
DATETIME_FORMAT = '%d/%m/%Y %H:%M'
ISO_DATE_FORMAT = '%Y-%m-%d'
ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

# Limites de taille de fichier (en octets)
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_PROFILE_PICTURE_SIZE = 2 * 1024 * 1024  # 2 MB
MAX_VERIFICATION_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB

# Extensions de fichier autorisées
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif']
ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']

# Paramètres de pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Types d'utilisateur
USER_TYPES = {
    'student': 'Étudiant',
    'teacher': 'Enseignant',
    'advisor': 'Conseiller d\'orientation',
    'administrator': 'Administrateur',
}

# Statuts de vérification
VERIFICATION_STATUSES = {
    'unverified': 'Non vérifié',
    'pending': 'En attente',
    'verified': 'Vérifié',
    'rejected': 'Rejeté',
}

# Types de documents de vérification
VERIFICATION_DOCUMENT_TYPES = {
    'identity': 'Pièce d\'identité',
    'diploma': 'Diplôme',
    'certificate': 'Certificat ou attestation',
    'proof_of_residence': 'Justificatif de domicile',
    'professional_card': 'Carte professionnelle',
    'school_certificate': 'Certificat de scolarité',
    'other': 'Autre document',
}