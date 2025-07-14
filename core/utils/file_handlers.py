import os
import uuid
import mimetypes
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

from .constants import (
    MAX_FILE_SIZE, 
    MAX_PROFILE_PICTURE_SIZE,
    ALLOWED_IMAGE_EXTENSIONS, 
    ALLOWED_DOCUMENT_EXTENSIONS
)

def validate_file_size(file, max_size=MAX_FILE_SIZE):
    """
    Valide la taille d'un fichier.
    
    Args:
        file: Le fichier à valider
        max_size: Taille maximale en octets
        
    Returns:
        bool: True si la taille est valide, False sinon
    """
    return file.size <= max_size

def validate_file_extension(file, allowed_extensions=None):
    """
    Valide l'extension d'un fichier.
    
    Args:
        file: Le fichier à valider
        allowed_extensions: Liste des extensions autorisées
        
    Returns:
        bool: True si l'extension est valide, False sinon
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_DOCUMENT_EXTENSIONS
    
    # Récupérer l'extension du fichier (en minuscules)
    ext = os.path.splitext(file.name)[1].lower()
    
    return ext in allowed_extensions

def generate_unique_filename(filename):
    """
    Génère un nom de fichier unique pour éviter les collisions.
    
    Args:
        filename: Le nom de fichier d'origine
        
    Returns:
        str: Le nouveau nom de fichier unique
    """
    # Récupérer l'extension du fichier
    ext = os.path.splitext(filename)[1].lower()
    
    # Générer un UUID unique
    unique_id = uuid.uuid4().hex
    
    # Créer le nouveau nom de fichier
    new_filename = f"{unique_id}{ext}"
    
    return new_filename

def compress_image(image_file, max_size=(800, 800), quality=85, format='JPEG'):
    """
    Compresse une image pour réduire sa taille.
    
    Args:
        image_file: Le fichier image à compresser
        max_size: Tuple (largeur, hauteur) maximale
        quality: Qualité de compression (0-100)
        format: Format de sortie ('JPEG', 'PNG', etc.)
        
    Returns:
        ContentFile: Le fichier image compressé
    """
    img = Image.open(image_file)
    
    # Convertir en RGB si l'image est en mode RGBA (pour JPEG)
    if img.mode == 'RGBA' and format == 'JPEG':
        img = img.convert('RGB')
    
    # Redimensionner l'image si nécessaire
    img.thumbnail(max_size, Image.LANCZOS)
    
    # Créer un fichier temporaire pour stocker l'image compressée
    output = ContentFile(b'')
    
    # Sauvegarder l'image compressée
    img.save(output, format=format, quality=quality, optimize=True)
    
    # Remettre le curseur au début du fichier
    output.seek(0)
    
    return output

def save_upload_file(uploaded_file, directory='uploads'):
    """
    Sauvegarde un fichier téléchargé avec un nom unique.
    
    Args:
        uploaded_file: Le fichier téléchargé
        directory: Le répertoire de destination
        
    Returns:
        str: Le chemin du fichier sauvegardé
    """
    # Générer un nom de fichier unique
    filename = generate_unique_filename(uploaded_file.name)
    
    # Construire le chemin de destination
    path = os.path.join(directory, filename)
    
    # Sauvegarder le fichier
    if default_storage.exists(path):
        default_storage.delete(path)
    
    path = default_storage.save(path, uploaded_file)
    
    return path

def save_profile_picture(image_file, user_id):
    """
    Sauvegarde une image de profil utilisateur.
    
    Args:
        image_file: Le fichier image
        user_id: L'identifiant de l'utilisateur
        
    Returns:
        str: Le chemin de l'image sauvegardée
    """
    # Valider la taille du fichier
    if not validate_file_size(image_file, MAX_PROFILE_PICTURE_SIZE):
        raise ValueError("L'image est trop grande. La taille maximale est de 2 Mo.")
    
    # Valider l'extension du fichier
    if not validate_file_extension(image_file, ALLOWED_IMAGE_EXTENSIONS):
        raise ValueError("Format d'image non supporté. Utilisez JPG, PNG ou GIF.")
    
    # Compresser l'image
    compressed_image = compress_image(image_file)
    
    # Générer un nom de fichier unique
    filename = f"profile_{user_id}_{uuid.uuid4().hex}.jpg"
    
    # Construire le chemin de destination
    path = os.path.join('profile_pictures', filename)
    
    # Sauvegarder l'image
    if default_storage.exists(path):
        default_storage.delete(path)
    
    path = default_storage.save(path, compressed_image)
    
    return path