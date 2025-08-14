from typing import Dict, List
from django.utils import timezone
import logging

from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin
logger = logging.getLogger(__name__)

class ODKProjectService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des projets ODK"""
    def __init__(self, django_user, request=None):
        super().__init__(django_user, request=request)

    def ensure_odk_project_exists(self, django_project):
        """
        Ensures that an ODK project exists for the given Django project.
        If the Django project doesn't have an ODK project yet, creates one.
        Returns the ODK project ID.
        """
        # If the project already has an ODK ID, return it
        if django_project.odk_id is not None:
            return django_project.odk_id

        # Create a new project in ODK Central
        try:
            project_data = {
                "name": django_project.name,
                "description": django_project.description or "",
            }

            odk_project = self.create_project(
                name=project_data["name"],
                description=project_data["description"]
            )
            logger.info(f"ODK project ID: {odk_project['id']}")
            # Update the Django project with the ODK project ID
            django_project.odk_id = odk_project["id"]
            django_project.last_sync = timezone.now()
            django_project.save()

            self._log_action(
                "link_django_project_to_odk",
                "project",
                str(odk_project["id"]),
                {
                    "django_project_id": django_project.pkid,
                    "odk_account": self.current_account["id"],
                },
                success=True,
            )

            return django_project.odk_id

        except Exception as e:
            self._log_action(
                "link_django_project_to_odk",
                "project",
                str(django_project.id),
                {
                    "error": str(e),
                    "django_project_id": django_project.pkid,
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_projects(self) -> List[Dict]:
        """Récupère tous les projets depuis ODK Central"""
        try:
            projects = self._make_request("GET", "projects")

            self._log_action(
                "list_projects",
                "project",
                "all projects",
                {"count": len(projects), "odk_account": self.current_account["id"]},
                success=True,
            )

            return projects
        except Exception as e:
            self._log_action(
                "list_projects",
                "project",
                "all projects",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_accessible_projects(self) -> List[Dict]:
        """Récupère les projets accessibles par l'utilisateur actuel"""
        try:
            # Récupérer tous les projets depuis ODK Central
            all_projects = self.get_projects()

            # Filtrer les projets selon les permissions de l'utilisateur
            accessible_projects = []
            for project in all_projects:
                if self._user_can_access_project_id(project["id"]):
                    accessible_projects.append(project)

            self._log_action(
                "list_accessible_projects",
                "project",
                f"{self.django_user.first_name}' projects",
                {
                    "total_projects": len(all_projects),
                    "accessible_count": len(accessible_projects),
                    "odk_account": self.current_account["id"],
                },
                success=True,
            )

            return accessible_projects

        except Exception as e:
            self._log_action(
                "list_accessible_projects",
                "project",
                f"{self.django_user.first_name}' projects",
                {
                    "error": str(e),
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    def get_project(self, project_id: int) -> Dict:
        """Récupère un projet spécifique depuis ODK Central"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}"
                )

            project = self._make_request("GET", f"projects/{project_id}")

            self._log_action(
                "get_project",
                "project",
                str(project_id),
                {"odk_account": self.current_account["id"]},
                success=True,
            )

            return project
        except Exception as e:
            self._log_action(
                "get_project",
                "project",
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

    def delete_project(self, project_id: int) -> None:
        """Delete a project from ODK Central"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"User {self.django_user.get_full_name()} does not have permission to delete project {project_id}"
                )

            self._make_request("DELETE", f"projects/{project_id}")

            self._log_action(
                "delete_project",
                "project",
                str(project_id),
                {"odk_account": self.current_account["id"]},
                success=True,
            )
        except Exception as e:
            self._log_action(
                "delete_project",
                "project",
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

    def create_project(self, name: str, description: str = "") -> Dict:
        """Create a new project in ODK Central"""
        try:
            if not self._user_can_create_project():
                raise PermissionError(
                    f"User {self.django_user.get_full_name()} does not have permission to create a project"
                )

            project_data = {
                "name": name,
                "description": description,
            }

            project = self._make_request("POST", "projects", json=project_data)

            self._log_action(
                "create_project",
                "project",
                str(project.id),
                {"name": name, "odk_account": self.current_account["id"]},
                success=True,
            )

            return project
        except Exception as e:
            self._log_action(
                "create_project",
                "project",
                "new",
                {
                    "error": str(e),
                    "name": name,
                    "odk_account": (
                        self.current_account["id"] if self.current_account else None
                    ),
                },
                success=False,
            )
            raise

    # def sync_project(self, project_id: int) -> ODKProjects:
    #     """Synchronise un projet ODK dans la base Django"""
    #     project_data = self.get_project(project_id)
    #
    #     django_project, created = ODKProjects.objects.update_or_create(
    #         odk_id=project_data["id"],
    #         defaults={
    #             "name": project_data["name"],
    #             "description": project_data.get("description", ""),
    #             "archived": project_data.get("archived", False),
    #             "created_by": self.django_user if created else None,
    #         },
    #     )
    #
    #     self._log_action(
    #         "sync_project",
    #         "project",
    #         str(project_id),
    #         {
    #             "created": created,
    #             "django_id": django_project.id,
    #             "odk_account": self.current_account["id"],
    #         },
    #         success=True,
    #     )
    #
    #     return django_project
