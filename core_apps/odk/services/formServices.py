import logging
from typing import Dict, List

from .baseService import BaseODKService
from .exceptions import ODKValidationError
from .permissionServices import ODKPermissionMixin

logger = logging.getLogger(__name__)


class ODKFormService(BaseODKService, ODKPermissionMixin):
    """Service for ODK forms management"""

    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def get_project_forms(self, project_id: int) -> List[Dict]:
        """Retrieve forms for a specific project"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            forms_data = self._make_request("GET", f"projects/{project_id}/forms")
            return forms_data

        except Exception as e:
            self._log_action(
                "list_forms",
                "form",
                str(project_id),
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_form(self, project_id: int, form_id: str) -> Dict:
        """Retrieve a specific form"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            form_data = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}"
            )
            return form_data

        except Exception as e:
            self._log_action(
                "get_form",
                "form",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def create_form(
        self,
        project_id: int,
        form_data,
        filename,
        form_id=None,
        ignore_warnings=False,
        publish=False,
    ) -> dict:

        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )
            # Determine Content-Type based on extension
            if filename.endswith(".xlsx"):
                content_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif filename.endswith(".xls"):
                content_type = "application/vnd.ms-excel"
            else:
                content_type = "application/xml"

            headers = {"Content-Type": content_type}
            if content_type != "application/xml" and form_id:
                headers["X-XlsForm-FormId-Fallback"] = form_id

            params = {}
            if ignore_warnings:
                params["ignoreWarnings"] = "true"
            if publish:
                params["publish"] = "true"

            # Send file as raw request body
            form = self._make_request(
                "POST",
                f"projects/{project_id}/forms/",
                data=form_data,
                headers=headers,
                params=params,
            )
            self._log_action(
                "create_form",
                "form",
                f"{project_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return form
        except Exception as e:
            self._log_action(
                "create_form",
                "form",
                f"{project_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def delete_form(self, project_id: int, form_id: str) -> Dict:
        """Delete a specific form (move to trash)"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            result = self._make_request(
                "DELETE", f"projects/{project_id}/forms/{form_id}"
            )
            self._log_action(
                "delete_form",
                "form",
                f"project:{project_id}/form:{form_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return result

        except Exception as e:
            self._log_action(
                "delete_form",
                "form",
                f"project:{project_id}/form:{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    # ================================
    # MVP SERVICES FOR DRAFT MANAGEMENT
    # ================================

    def get_form_draft(self, project_id: int, form_id: str) -> Dict:
        """Retrieve form draft details"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            draft_data = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}/draft"
            )
            return draft_data

        except ODKValidationError:
            # Relancer les erreurs de validation ODK sans modification
            raise
        except Exception as e:
            self._log_action(
                "get_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def create_or_update_draft(
        self,
        project_id: int,
        form_id: str,
        form_data,
        filename: str,
        ignore_warnings: bool = False,
    ) -> Dict:
        """Create or update a form draft"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            # Determine Content-Type based on extension
            if filename.endswith(".xlsx"):
                content_type = (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            elif filename.endswith(".xls"):
                content_type = "application/vnd.ms-excel"
            else:
                content_type = "application/xml"

            headers = {"Content-Type": content_type}

            params = {}
            if ignore_warnings:
                params["ignoreWarnings"] = "true"

            draft = self._make_request(
                "POST",
                f"projects/{project_id}/forms/{form_id}/draft",
                data=form_data,
                headers=headers,
                params=params,
            )

            self._log_action(
                "create_update_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return draft

        except ODKValidationError:
            # Relancer les erreurs de validation ODK sans modification
            raise
        except Exception as e:
            self._log_action(
                "create_update_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def publish_draft(self, project_id: int, form_id: str, version: str = None) -> Dict:
        """Publish a draft as a form version"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            params = {}
            if version:
                params["version"] = version

            result = self._make_request(
                "POST",
                f"projects/{project_id}/forms/{form_id}/draft/publish",
                params=params,
            )
            return result
        except ODKValidationError:
            raise
        except Exception as e:
            self._log_action(
                "publish_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "version": version,
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def delete_draft(self, project_id: int, form_id: str) -> Dict:
        """Delete a form draft"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            result = self._make_request(
                "DELETE", f"projects/{project_id}/forms/{form_id}/draft"
            )

            self._log_action(
                "delete_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return result

        except Exception as e:
            self._log_action(
                "delete_draft",
                "form_draft",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_draft_submissions(self, project_id: int, form_id: str) -> List[Dict]:
        """Get test submissions for a draft"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            submissions = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}/draft/submissions"
            )
            return submissions

        except Exception as e:
            self._log_action(
                "get_draft_submissions",
                "form_draft",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_form_versions(self, project_id: int, form_id: str) -> List[Dict]:
        """Get all published versions of a form"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )
            versions = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}/versions"
            )

            return versions

        except Exception as e:
            self._log_action(
                "get_form_versions",
                "form",
                f"{project_id}/{form_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_form_version_xml(self, project_id: int, form_id: str, version: str) -> str:
        """Get XML for a specific form version"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} does not have access to project {project_id}"
                )

            xml_data = self._make_request(
                "GET",
                f"projects/{project_id}/forms/{form_id}/versions/{version}.xml",
                return_json=False,
            )
            return xml_data

        except Exception as e:
            self._log_action(
                "get_form_version_xml",
                "form",
                f"{project_id}/{form_id}/{version}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise
