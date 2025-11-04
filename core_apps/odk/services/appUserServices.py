import logging
from typing import Dict, List

from .baseService import BaseODKService
from .exceptions import ODKValidationError
from .permissionServices import ODKPermissionMixin

logger = logging.getLogger(__name__)


class ODKAppUserService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des utilisateurs d'application ODK (App Users)"""

    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def _validate_project_access(self, project_id: int) -> None:
        """Extract common permission validation logic"""
        if not self._user_can_access_project_id(project_id):
            raise PermissionError(
                f"User {self.django_user.username} cannot access project {project_id}"
            )

    def get_project_app_users(self, project_id: int):
        """Récupère tous les utilisateurs d'application d'un projet spécifique"""
        try:
            self._validate_project_access(project_id)
            app_users_data = self._make_request(
                "GET", f"projects/{project_id}/app-users"
            )

            return app_users_data
        except Exception as e:
            self._log_action(
                "list_app_users",
                "app_user",
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

    def create_app_user(self, project_id: int, display_name: str) -> Dict:
        """Crée un nouvel utilisateur d'application pour un projet"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas les droits pour modifier le projet {project_id}"
                )

            payload = {"displayName": display_name}
            app_user = self._make_request(
                "POST", f"projects/{project_id}/app-users", json=payload
            )

            self._log_action(
                "create_app_user",
                "app_user",
                f"{project_id}",
                {
                    "display_name": display_name,
                    "odk_account": self.current_account["id"],
                },
                success=True,
            )
            return app_user

        except Exception as e:
            self._log_action(
                "create_app_user",
                "app_user",
                f"{project_id}",
                {
                    "display_name": display_name,
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def delete_app_user(self, project_id: int, app_user_id: str) -> bool:
        """Supprime un utilisateur d'application"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} has no modification right on the project"
                )
            self._make_request(
                "DELETE", f"projects/{project_id}/app-users/{app_user_id}"
            )
            self._log_action(
                "delete_app_user",
                "app_user",
                f"{project_id}/{app_user_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return True

        except Exception as e:
            self._log_action(
                "delete_app_user",
                "app_user",
                f"{project_id}/{app_user_id}",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def revoke_app_user_access(self, project_id: int, token) -> bool:
        """Révoque l'accès d'un utilisateur d'application sans le supprimer"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas les droits pour modifier le projet {project_id}"
                )
            if not token or len(token) != 64:
                raise ValueError("Invalid token format")

            # Révoquer la session en supprimant le token
            self._make_request("DELETE", f"sessions/{token}")

            self._log_action(
                "revoke_app_user",
                "app_user",
                f"{project_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )
            return True
        except Exception as e:
            self._log_action(
                "revoke_app_user",
                "app_user",
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

    def assign_form_to_user(self, project_id: int, form_id: str, app_user_id: int):
        """Assign a form to an app user"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} has no modification right on the project"
                )
            self._make_request(
                "POST",
                f"projects/{project_id}/forms/{form_id}/assignments/app-user/{app_user_id}",
            )
        except ODKValidationError:
            raise
        except Exception as e:
            raise e

    def unassgin_form_to_user(self, project_id: int, form_id: str, app_user_id: int):
        """Unassign a form from an app user"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"User {self.django_user.username} has no modification right on the project"
                )
            self._make_request(
                "DELETE",
                f"projects/{project_id}/forms/{form_id}/assignments/app-user/{app_user_id}",
            )
        except ODKValidationError:
            raise
        except Exception as e:
            raise e

    def list_forms_app_users(self, project_id: int, form_id: str):
        """List all forms assigned to an app user"""
        try:
            self._validate_project_access(project_id)
            forms_data = self._make_request(
                "GET", f"projects/{project_id}/forms/{form_id}/assignments/app-user"
            )
            return forms_data
        except ODKValidationError:
            raise
        except Exception as e:
            raise e
