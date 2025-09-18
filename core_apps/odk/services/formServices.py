import logging
from typing import Dict, List

from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin

logger = logging.getLogger(__name__)


class ODKFormService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des formulaires ODK"""

    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def get_project_forms(self, project_id: int) -> List[Dict]:
        """Récupère les formulaires d'un projet spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )

            forms_data = self._make_request("GET", f"projects/{project_id}/forms")

            self._log_action(
                "list_forms",
                "form",
                str(project_id),
                {"count": len(forms_data), "odk_account": self.current_account["id"]},
                success=True,
            )

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
        """Récupère un formulaire spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )

            form_data = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}"
            )

            self._log_action(
                "get_form",
                "form",
                f"{project_id}/{form_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
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
                    f" The user {self.django_user.username} has not right on project id: {project_id}"
                )

            # Déterminer le Content-Type selon l’extension
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

            # Envoi du fichier en tant que corps brut de la requête
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
