import os
import io
import logging
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from google.oauth2.service_account import Credentials
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


@deconstructible
class GoogleDriveStorage(Storage):
    def __init__(self):
        self.service = self._get_service()
        self.folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        if not self.folder_id:
            raise ImproperlyConfigured("GOOGLE_DRIVE_FOLDER_ID must be set in settings")

    def _get_service(self):
        """Initialise le service Google Drive"""
        try:
            service_account_file = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)
            if not service_account_file or not os.path.exists(service_account_file):
                raise ImproperlyConfigured("GOOGLE_SERVICE_ACCOUNT_FILE must be set and file must exist")

            creds = Credentials.from_service_account_file(
                service_account_file,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service Google Drive: {e}")
            raise

    def _save(self, name, content):
        """Sauvegarde le fichier sur Google Drive"""
        try:
            # Métadonnées du fichier
            file_metadata = {
                'name': name,
                'parents': [self.folder_id]
            }

            # Contenu du fichier
            content.seek(0)  # Retour au début du fichier
            media = MediaIoBaseUpload(
                io.BytesIO(content.read()),
                mimetype=self._get_mimetype(name),
                resumable=True
            )

            # Upload du fichier
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            # Rendre le fichier public
            self._make_public(file.get('id'))

            logger.info(f"Fichier {name} uploadé avec succès, ID: {file.get('id')}")
            return file.get('id')

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {name}: {e}")
            raise

    def _make_public(self, file_id):
        """Rend le fichier public"""
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
        except Exception as e:
            logger.warning(f"Impossible de rendre le fichier public: {e}")

    def _get_mimetype(self, name):
        """Détermine le type MIME basé sur l'extension"""
        extension = name.lower().split('.')[-1]
        mimetypes = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        return mimetypes.get(extension, 'application/octet-stream')

    def delete(self, name):
        """Supprime le fichier de Google Drive"""
        try:
            self.service.files().delete(fileId=name).execute()
            logger.info(f"Fichier {name} supprimé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de {name}: {e}")

    def exists(self, name):
        """Vérifie si le fichier existe"""
        try:
            self.service.files().get(fileId=name).execute()
            return True
        except:
            return False

    def url(self, name):
        """Retourne l'URL publique du fichier"""
        if not name:
            return None
        return f"https://drive.google.com/uc?id={name}&export=download"

    def size(self, name):
        """Retourne la taille du fichier"""
        try:
            file = self.service.files().get(fileId=name, fields='size').execute()
            return int(file.get('size', 0))
        except:
            return 0

    def get_valid_name(self, name):
        """Nettoie le nom du fichier"""
        import re
        # Remplace les caractères non-alphanumériques par des underscores
        name = re.sub(r'[^\w\-_\.]', '_', name)
        return name