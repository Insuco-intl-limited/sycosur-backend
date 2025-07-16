from django.core.files.temp import NamedTemporaryFile

import requests

from core_apps.common.drive_storage import GoogleDriveStorage
from core_apps.profiles.models import Profile


def save_profile(backend, user, response, *args, **kwargs):
    if backend.name == "google-oauth2":
        avatar_url = response.get("picture", None)
        if avatar_url:
            response = requests.get(avatar_url)
            if response.status_code == 200:
                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(response.content)
                img_temp.flush()

                storage = GoogleDriveStorage()
                profile, created = Profile.objects.get_or_create(user=user)
                profile.avatar.save(f"{user.email}_avatar.jpg", img_temp, save=True)
