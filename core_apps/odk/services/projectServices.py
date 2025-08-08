from typing import Dict, List

from core_apps.odk.models import ODKProjects

from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin


class ODKProjectService(BaseODKService, ODKPermissionMixin):
    """Service pour la gestion des projets ODK"""

    def get_projects(self) -> List[Dict]:
        """Récupère tous les projets depuis ODK Central"""
        try:
            projects = self._make_request("GET", "projects")

            self._log_action(
                "list_projects",
                "project",
                0,
                {"count": len(projects), "odk_account": self.current_account["id"]},
                success=True,
            )

            return projects
        except Exception as e:
            self._log_action(
                "list_projects",
                "project",
                "all",
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
                0,
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
                "all",
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

    def create_project(self, name: str, description: str = "") -> Dict:
        """Crée un nouveau projet dans ODK Central"""
        try:
            if not self._user_can_create_project():
                raise PermissionError(
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas les droits pour créer un projet"
                )

            project_data = {
                "name": name,
                "description": description,
                "created_by": self.django_user,
            }

            project = self._make_request("POST", "projects", json=project_data)

            self._log_action(
                "create_project",
                "project",
                str(project.get("id", 0)),
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

    def sync_project(self, project_id: int) -> ODKProjects:
        """Synchronise un projet ODK dans la base Django"""
        project_data = self.get_project(project_id)

        django_project, created = ODKProjects.objects.update_or_create(
            odk_id=project_data["id"],
            defaults={
                "name": project_data["name"],
                "description": project_data.get("description", ""),
                "archived": project_data.get("archived", False),
                "created_by": self.django_user if created else None,
            },
        )

        self._log_action(
            "sync_project",
            "project",
            str(project_id),
            {
                "created": created,
                "django_id": django_project.id,
                "odk_account": self.current_account["id"],
            },
            success=True,
        )

        return django_project
