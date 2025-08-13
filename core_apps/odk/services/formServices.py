from typing import Dict, List
import logging
from .baseService import BaseODKService
from .permissionServices import ODKPermissionMixin
logger = logging.getLogger(__name__)

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

    def create_form(self, project_id: int, form_data, is_xlsx=False) -> Dict:
        """
        Crée un nouveau formulaire dans un projet.
        
        Args:
            project_id: ID du projet ODK
            form_data: Données du formulaire (XML en texte ou binaire, ou XLSX en binaire)
            is_xlsx: Indique si les données sont au format XLSX (True) ou XML (False)
            
        Returns:
            Dict: Informations sur le formulaire créé
            
        Raises:
            PermissionError: Si l'utilisateur n'a pas accès au projet
            Exception: Pour toute autre erreur lors de la création du formulaire
        """
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(
                    f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}"
                )

            # Préparer les données du formulaire selon le format
            if is_xlsx:
                # Pour les fichiers XLSX, utiliser directement les données binaires
                form_bytes = form_data if isinstance(form_data, bytes) else form_data
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                filename = "form.xlsx"
            else:
                # Pour les fichiers XML, encoder en bytes si nécessaire
                if isinstance(form_data, str):
                    form_bytes = form_data.encode('utf-8')
                else:
                    form_bytes = form_data
                content_type = "application/xml"
                filename = "form.xml"

            # Préparer le fichier avec le type de contenu approprié
            files = {"formId": (filename, form_bytes, content_type)}

            form = self._make_request(
                "POST", f"projects/{project_id}/forms", files=files
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