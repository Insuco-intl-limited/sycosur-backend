from typing import Dict, List

from .baseService import BaseODKService
from .exceptions import ODKValidationError
from .permissionServices import ODKPermissionMixin


class ODKSubmissionService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des soumissions ODK"""

    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def get_form_submissions(self, project_id: int, form_id: str) -> List[Dict]:
        """Récupère les soumissions d'un formulaire spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )
            submissions = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}/submissions",
                headers={"X-Extended-Metadata": "true"}
            )
            return submissions

        except Exception as e:
            self._log_action(
                "list_submissions",
                "submission",
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

    def get_submission(self, project_id: int, form_id: str, instance_id: str) -> Dict:
        """Récupère une soumission spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )

            submission = self._make_request(
                "GET",
                f"projects/{project_id}/forms/{form_id}/submissions/{instance_id}",
                headers={"X-Extended-Metadata": "true"}
            )
            return submission

        except Exception as e:
            self._log_action(
                "get_submission",
                "submission",
                f"{project_id}/{form_id}/{instance_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def export_submissions_csv(self, project_id: int, form_id: str) -> bytes:
        """Exporte les soumissions d'un formulaire en CSV"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )
            # Pour les exports, l'API retourne du contenu binaire
            response = self._make_request(
                "GET",
                f"projects/{project_id}/forms/{form_id}/submissions.csv",
                return_json=False,
            )
            return response
        except ODKValidationError:
            raise
        except Exception as e:
            self._log_action(
                "export_submissions_csv",
                "submission",
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
