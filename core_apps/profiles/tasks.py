from uuid import UUID
from celery import shared_task
from core_apps.common.drive_storage import GoogleDriveStorage
from django.core.files.storage import FileSystemStorage
from .models import Profile


@shared_task(name="upload_avatar_to_google_drive")
def upload_avatar_to_google_drive(profile_id: UUID, image_content: bytes) -> None:
    profile = Profile.objects.get(id=profile_id)
    storage = GoogleDriveStorage()
    filename = f"avatar_{profile_id}.jpg"
    file_url = storage._save(filename, image_content)
    profile.avatar = file_url
    profile.save()

# @shared_task(name="upload_avatar_to_media")
# def upload_avatar_to_media(profile_id: UUID, image_content: bytes) -> None:
#     profile = Profile.objects.get(id=profile_id)
#     storage = FileSystemStorage()
#     filename = f"avatar_{profile_id}.jpg"
#     file_url = storage.save(filename, image_content)
#     profile.avatar = file_url
#     profile.save()
