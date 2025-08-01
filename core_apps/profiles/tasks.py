from uuid import UUID
from celery import shared_task
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from .models import Profile, avatar_upload_path


@shared_task(name="upload_avatar_to_media")
def upload_avatar_to_media(profile_id: UUID, image_content: bytes, original_filename: str) -> None:
    profile = Profile.objects.get(id=profile_id)
    storage = FileSystemStorage()
    
    # Utiliser la fonction avatar_upload_path pour générer le bon chemin
    filename = avatar_upload_path(profile, original_filename)
    
    # Créer un ContentFile à partir des bytes
    content_file = ContentFile(image_content, name=original_filename)
    
    # Sauvegarder le fichier
    file_url = storage.save(filename, content_file)
    
    # Mettre à jour le profile avec le nouveau chemin
    profile.avatar = file_url
    profile.save()
