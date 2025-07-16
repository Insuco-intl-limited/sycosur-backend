import io
import logging
import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

logger = logging.getLogger(__name__)


@deconstructible
class GoogleDriveStorage(Storage):
    def __init__(self):
        self.service = self._get_service()
        self.folder_id = getattr(settings, "GOOGLE_DRIVE_FOLDER_ID", None)
        if not self.folder_id:
            raise ImproperlyConfigured("GOOGLE_DRIVE_FOLDER_ID must be set in settings")

    def _get_service(self):
        """Initialize Google Drive service"""
        try:
            service_account_file = getattr(
                settings, "GOOGLE_SERVICE_ACCOUNT_FILE", None
            )
            if not service_account_file or not os.path.exists(service_account_file):
                raise ImproperlyConfigured(
                    "GOOGLE_SERVICE_ACCOUNT_FILE must be set and file must exist"
                )

            creds = Credentials.from_service_account_file(
                service_account_file, scopes=["https://www.googleapis.com/auth/drive"]
            )
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error initializing Google Drive service: {e}")
            raise

    def _save(self, name, content):
        """Save file to Google Drive"""
        try:
            # File metadata
            file_metadata = {"name": name, "parents": [self.folder_id]}

            # File content
            content.seek(0)  # Return to start of file
            media = MediaIoBaseUpload(
                io.BytesIO(content.read()),
                mimetype=self._get_mimetype(name),
                resumable=True,
            )

            # Upload file with shared drive support
            file = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=True,  # Enable shared drive support
                )
                .execute()
            )

            # Make file public
            self._make_public(file.get("id"))

            logger.info(f"File {name} uploaded successfully, ID: {file.get('id')}")
            return file.get("id")

        except Exception as e:
            logger.error(f"Error saving {name}: {e}")
            raise

    def _make_public(self, file_id):
        """Make file public"""
        try:
            permission = {"type": "anyone", "role": "reader"}
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                supportsAllDrives=True,  # Enable shared drive support
            ).execute()
        except Exception as e:
            logger.warning(f"Unable to make file public: {e}")

    def _get_mimetype(self, name):
        """Determine MIME type based on extension"""
        extension = name.lower().split(".")[-1]
        mimetypes = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        # get the file type otherwise return application/octet-stream (generic type of binary files)
        return mimetypes.get(extension, "application/octet-stream")

    def delete(self, name):
        """Delete file from Google Drive"""
        try:
            self.service.files().delete(
                fileId=name, supportsAllDrives=True  # Enable shared drive support
            ).execute()
            logger.info(f"File {name} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting {name}: {e}")

    def exists(self, name):
        """Check if file exists"""
        try:
            self.service.files().get(
                fileId=name, supportsAllDrives=True  # Enable shared drive support
            ).execute()
            return True
        except:
            return False

    def url(self, name):
        """Return public URL for file"""
        if not name:
            return None
        return f"https://drive.google.com/thumbnail?id={name}&sz=w400-h300"

    def size(self, name):
        """Return file size"""
        try:
            file = (
                self.service.files()
                .get(
                    fileId=name,
                    fields="size",
                    supportsAllDrives=True,  # Enable shared drive support
                )
                .execute()
            )
            return int(file.get("size", 0))
        except:
            return 0

    def get_valid_name(self, name):
        """Clean filename"""
        import re

        # Replace non-alphanumeric characters with underscores
        name = re.sub(r"[^\w\-_\.]", "_", name)
        return name

    # method to resize the image
    def resize_file(self, name, widht: int, height: int):
        """Resize image file stored in Google Drive"""
        try:
            # Download file
            request = self.service.files().get_media(
                fileId=name, supportsAllDrives=True
            )
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()

            # Resize image
            from PIL import Image

            file.seek(0)
            image = Image.open(file)
            resized_image = image.resize((widht, height), Image.Resampling.LANCZOS)

            # Save resized image to buffer
            output = io.BytesIO()
            resized_image.save(output, format=image.format)
            output.seek(0)

            # Update file in Drive
            media = MediaIoBaseUpload(
                output, mimetype=self._get_mimetype(name), resumable=True
            )

            self.service.files().update(
                fileId=name, media_body=media, supportsAllDrives=True
            ).execute()

            return True
        except Exception as e:
            logger.error(f"Error resizing file {name}: {e}")
            return False
