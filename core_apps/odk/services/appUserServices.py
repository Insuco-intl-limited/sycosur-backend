import logging
from typing import Dict, List

from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin

logger = logging.getLogger(__name__)


class ODKAppUserService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des utilisateurs d'application ODK (App Users)"""

    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def get_project_app_users(self, project_id: int) :
        """Récupère tous les utilisateurs d'application d'un projet spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )
            app_users_data = self._make_request("GET", f"projects/{project_id}/app-users")

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

    def get_app_user(self, project_id: int, app_user_id: str) -> Dict:
        """Récupère un utilisateur d'application spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas accès au projet {project_id}"
                )

            app_user_data = self._make_request(
                "GET", f"projects/{project_id}/app-users/{app_user_id}"
            )

            self._log_action(
                "get_app_user",
                "app_user",
                f"{project_id}/{app_user_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )

            return app_user_data

        except Exception as e:
            self._log_action(
                "get_app_user",
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

    def create_app_user(self, project_id: int, display_name: str) -> Dict:
        """Crée un nouvel utilisateur d'application pour un projet"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas les droits pour modifier le projet {project_id}"
                )

            payload = {"displayName": display_name}
            app_user = self._make_request(
                "POST",
                f"projects/{project_id}/app-users",
                json=payload
            )

            self._log_action(
                "create_app_user",
                "app_user",
                f"{project_id}",
                {"display_name": display_name, "odk_account": self.current_account["id"]},
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
                    f"L'utilisateur {self.django_user.username} n'a pas les droits pour modifier le projet {project_id}"
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

    def revoke_app_user_access(self, project_id: int, app_user_id: str) -> bool:
        """Révoque l'accès d'un utilisateur d'application sans le supprimer"""
        try:
            if not self._user_can_modify_project(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.username} n'a pas les droits pour modifier le projet {project_id}"
                )

            # Récupérer les informations de l'app user pour obtenir son token
            app_user = self.get_app_user(project_id, app_user_id)
            
            if not app_user.get("token"):
                # L'utilisateur a déjà été révoqué
                return True
                
            # Révoquer la session en supprimant le token
            self._make_request("DELETE", f"sessions/{app_user['token']}")

            self._log_action(
                "revoke_app_user",
                "app_user",
                f"{project_id}/{app_user_id}",
                {"odk_account": self.current_account["id"]},
                success=True,
            )

            return True

        except Exception as e:
            self._log_action(
                "revoke_app_user",
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