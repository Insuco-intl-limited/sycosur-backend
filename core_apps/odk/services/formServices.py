from typing import Dict, List

from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin


class ODKFormService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des formulaires ODK"""

    def get_project_forms(self, project_id: int) -> List[Dict]:
        """Récupère les formulaires d'un projet spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}"
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
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}"
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

    def create_form(self, project_id: int, form_xml: str) -> Dict:
        """Crée un nouveau formulaire dans un projet"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}"
                )

            # L'API ODK attend un fichier XML
            files = {"xml_file": ("form.xml", form_xml, "application/xml")}

            form = self._make_request(
                "POST", f"projects/{project_id}/forms", files=files
            )

            self._log_action(
                "create_form",
                "form",
                f"{project_id}/{form.get('xmlFormId', 'unknown')}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )

            return form
        except Exception as e:
            self._log_action(
                "create_form",
                "form",
                f"{project_id}/new",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise
