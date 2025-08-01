from django.conf import settings
from .poolServices import ODKAccountPool
import requests
import logging
import time
import json
import threading
from queue import Queue
from datetime import timedelta
from typing import Dict, Any, Optional, List
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from core_apps.odk.utils import get_ssl_verify
from core_apps.odk.models import ODKProjects, ODKProjectPermissions, ODKUserSessions, ODKAuditLogs

odk_account_pool = ODKAccountPool()
logger = logging.getLogger(__name__)
class ODKCentralService:
    """Service to interact with ODK Central API"""

    def __init__(self, django_user):
        self.django_user = django_user
        self.base_url = getattr(settings, 'ODK_CENTRAL_URL', 'https://odk.insuco.net/v1')
        self.current_account = None
        self.current_session_data = None

    def __enter__(self):
        """Context manager for acquiring an ODK account from the pool"""
        self.current_account = odk_account_pool.get_account()
        self.current_session_data = odk_account_pool.get_session_for_account(
            self.current_account
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Libère le compte dans le pool"""
        if self.current_account:
            odk_account_pool.return_account(self.current_account)

    def _get_or_create_token(self) -> str:
        """Récupère ou crée un token ODK valide pour le compte courant"""
        if not self.current_account:
            raise Exception("Aucun compte ODK attribué")

        session_data = self.current_session_data
        account = self.current_account

        # Vérifie si on a déjà un token valide
        if (session_data['token'] and session_data['expires_at'] and
                timezone.now() < session_data['expires_at']):
            return session_data['token']

        # self.verify_ssl = get_ssl_verify()
        # Sinon, authentification
        try:
            response = session_data['session'].post(
                f"{self.base_url}/sessions",
                json={
                    "email": account['email'],
                    "password": account['password']
                },
                verify = get_ssl_verify()
            )
            response.raise_for_status()

            token = response.json().get("token")
            expires_at = timezone.now() + timedelta(hours=23)  # 23h pour éviter les expirations

            # Met à jour les données de session
            session_data['token'] = token
            session_data['expires_at'] = expires_at
            session_data['session'].headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            })

            # Enregistre également le token pour l'utilisateur Django
            thread_id = threading.current_thread().ident
            ODKUserSessions.objects.update_or_create(
                user=self.django_user,
                defaults={
                    'odk_token': token,
                    'token_expired_at': expires_at,
                    'actor_id': account['id']
                }
            )

            logger.info(f"Authentification ODK réussie pour le compte {account['id']} (threads: {thread_id})")
            return token

        except Exception as e:
            thread_id = threading.current_thread().ident
            logger.error(f"Échec d'authentification ODK pour le compte {account['id']}: {e} (thread: {thread_id})")
            raise

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Effectue une requête vers ODK Central avec retry et gestion d'erreurs"""

        # Utilise la configuration ou les valeurs par défaut
        max_retries = getattr(settings, 'ODK_MAX_RETRIES', 3)
        timeout = getattr(settings, 'ODK_REQUEST_TIMEOUT', 30)

        # Ajoute le timeout par défaut s'il n'est pas spécifié
        if 'timeout' not in kwargs:
            kwargs['timeout'] = timeout
        if 'verify' not in kwargs:
            kwargs['verify'] = get_ssl_verify()

        for attempt in range(max_retries):
            try:
                self._get_or_create_token()
                session = self.current_session_data['session']

                logger.debug(
                    f"Tentative {attempt+1}/{max_retries} - {method} {self.base_url}/{endpoint}"
                )

                response = session.request(
                    method,
                    f"{self.base_url}/{endpoint}",
                    **kwargs
                )
                response.raise_for_status()

                # Pour les requêtes qui ne retournent pas de JSON
                if response.status_code == 204 or not response.content:
                    return {"success": True, "status_code": response.status_code}

                return response.json()

            except requests.exceptions.ConnectionError as e:
                # Problème de connexion au serveur
                logger.error(
                    f"Erreur de connexion à ODK Central ({self.base_url}): {e}"
                )
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponentiel
                    logger.info(f"Nouvelle tentative dans {wait_time} secondes...")
                    time.sleep(wait_time)
                    continue
                raise Exception(
                    f"Impossible de se connecter au serveur ODK Central. "
                    f"Vérifiez que l'URL '{self.base_url}' est correcte et que le serveur est accessible."
                )
            except requests.exceptions.Timeout as e:
                # Timeout de la requête
                logger.error(f"Timeout lors de la connexion à ODK Central: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Nouvelle tentative dans {wait_time} secondes...")
                    time.sleep(wait_time)
                    continue
                raise Exception(
                    f"Le serveur ODK Central ne répond pas dans le délai imparti ({timeout}s). "
                    f"Vérifiez l'état du serveur ou augmentez la valeur de ODK_REQUEST_TIMEOUT."
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:  # Token expiré
                    logger.warning(f"Token expiré pour le compte {self.current_account['id']}, rafraîchissement...")
                    self.current_session_data['token'] = None
                    if attempt < max_retries - 1:
                        continue
                # Autres erreurs HTTP
                status_code = e.response.status_code
                logger.error(f"Erreur HTTP {status_code} lors de la requête à ODK Central: {e}")

                if status_code == 404:
                    raise Exception(f"Ressource non trouvée: {endpoint}")
                elif status_code == 403:
                    raise Exception(f"Accès refusé à la ressource: {endpoint}")
                elif status_code >= 500:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Erreur serveur, nouvelle tentative dans {wait_time} secondes...")
                        time.sleep(wait_time)
                        continue
                    raise Exception(f"Erreur serveur ODK Central ({status_code}). Veuillez réessayer plus tard.")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON: {e}")
                raise Exception("Le serveur ODK Central a retourné une réponse invalide.")
            except Exception as e:
                logger.error(f"Erreur inattendue lors de la requête à ODK Central: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Nouvelle tentative dans {wait_time} secondes...")
                    time.sleep(wait_time)
                    continue
                raise

        raise Exception(f"Nombre maximum de tentatives dépassé pour {method} {endpoint}")

    def get_projects(self) -> List[Dict]:
        """Récupère tous les projets depuis ODK Central"""
        try:
            projects = self._make_request('GET', 'projects')

            self._log_action(
                'list_projects',
                'project',
                0,
                {
                    'count': len(projects),
                    'odk_account': self.current_account['id']
                },
                success=True
            )

            return projects
        except Exception as e:
            self._log_action(
                'list_projects',
                'project',
                'all',
                {
                    'error': str(e),
                    'odk_account': self.current_account['id'] if self.current_account else None
                },
                success=False
            )
            raise

    def get_accessible_projects(self) -> List[Dict]:
        """Récupère les projets ODK accessibles à l'utilisateur Django"""
        try:
            # Récupère tous les projets depuis ODK
            all_projects = self.get_projects()

            # Filtre selon les permissions Django
            accessible_projects = []
            for project_data in all_projects:
                if self._user_can_access_project_id(project_data['id']):
                    # Ajoute des informations supplémentaires
                    try:
                        django_project = ODKProjects.objects.get(odk_id=project_data['id'])
                        permission = django_project.get_user_permission(self.django_user)

                        project_data['django_permission'] = permission.permission_level if permission else None
                        project_data['django_id'] = django_project.id
                        project_data['last_sync'] = django_project.last_sync.isoformat()
                    except ODKProjects.DoesNotExist:
                        project_data['django_permission'] = None
                        project_data['django_id'] = None
                        project_data['last_sync'] = None

                    accessible_projects.append(project_data)

            return accessible_projects

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets accessibles: {e}")
            raise

    def get_project(self, project_id: int) -> Dict:
        """Récupère les détails d'un projet spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}")

            project_data = self._make_request('GET', f'projects/{project_id}')

            self._log_action(
                'get_project',
                'project',
                str(project_id),
                {
                    'odk_account': self.current_account['id']
                },
                success=True
            )

            return project_data

        except Exception as e:
            self._log_action(
                'get_project',
                'project',
                str(project_id),
                {
                    'error': str(e),
                    'odk_account': self.current_account['id'] if self.current_account else None
                },
                success=False
            )
            raise
    def create_project(self, project_data: Dict) -> Dict:
        """Crée un nouveau projet ODK"""
        try:
            if not self.django_user.profile.odk_role == self.django_user.profile.ODKRole.ADMINISTRATOR:
                raise PermissionError(f"L'utilisateur {self.django_user.get_full_name()} n'a pas les droits pour créer un projet")

            response = self._make_request('POST', 'projects', json=project_data)

            self._log_action(
                'create_project',
                'project',
                str(response['id']),
                {
                    'odk_account': self.current_account['id']
                },
                success=True
            )

            return response

        except Exception as e:
            self._log_action(
                'create_project',
                'project',
                'new',
                {
                    'error': str(e),
                    'odk_account': self.current_account['id'] if self.current_account else None
                },
                success=False
            )
            raise

    def get_project_forms(self, project_id: int) -> List[Dict]:
        """Récupère les formulaires d'un projet spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}")

            forms_data = self._make_request('GET', f'projects/{project_id}/forms')

            self._log_action(
                'list_forms',
                'form',
                str(project_id),
                {
                    'count': len(forms_data),
                    'odk_account': self.current_account['id']
                },
                success=True
            )

            return forms_data

        except Exception as e:
            self._log_action(
                'list_forms',
                'form',
                str(project_id),
                {
                    'error': str(e),
                    'odk_account': self.current_account['id'] if self.current_account else None
                },
                success=False
            )
            raise

    def get_form_submissions(self, project_id: int, form_id: str) -> List[Dict]:
        """Récupère les soumissions d'un formulaire spécifique"""
        try:
            if not self._user_can_access_project_id(project_id):
                raise PermissionError(f"L'utilisateur {self.django_user.get_full_name()} n'a pas accès au projet {project_id}")

            submissions = self._make_request('GET', f'projects/{project_id}/forms/{form_id}/submissions')

            self._log_action(
                'list_submissions',
                'submission',
                f"{project_id}/{form_id}",
                {
                    'count': len(submissions),
                    'odk_account': self.current_account['id']
                },
                success=True
            )

            return submissions

        except Exception as e:
            self._log_action(
                'list_submissions',
                'submission',
                f"{project_id}/{form_id}",
                {
                    'error': str(e),
                    'odk_account': self.current_account['id'] if self.current_account else None
                },
                success=False
            )
            raise

    def _user_can_access_project_id(self, project_id: int) -> bool:
        """Vérifie si l'utilisateur Django peut accéder au projet ODK"""
        # Admin ODK peut tout voir
        if self.django_user.profile.odk_role == self.django_user.profile.ODKRole.ADMINISTRATOR:
            return True

        # Manager ODK peut voir tous les projets
        if self.django_user.profile.odk_role == self.django_user.profile.ODKRole.MANAGER:
            return True

        # Vérification des permissions spécifiques au projet
        try:
            project = ODKProjects.objects.get(odk_id=project_id)

            try:
                # Si une permission explicite existe
                ODKProjectPermission.objects.get(
                    user=self.django_user,
                    project=project
                )
                return True
            except ODKProjectPermission.DoesNotExist:
                # Si c'est un superviseur, accès par défaut aux projets
                if self.django_user.profile.odk_role == self.django_user.profile.ODKRole.SUPERVISOR:
                    return True
                # Sinon, pas d'accès
                return False
        except ODKProjects.DoesNotExist:
            # Si le projet n'est pas encore dans la DB, on autorise l'accès aux superviseurs et +
            return self.django_user.profile.odk_role in [
                self.django_user.profile.ODKRole.SUPERVISOR,
                self.django_user.profile.ODKRole.MANAGER,
                self.django_user.profile.ODKRole.ADMINISTRATOR
            ]

    def sync_project(self, project_id: int) -> ODKProjects:
        """Synchronise un projet ODK dans la base Django"""
        project_data = self.get_project(project_id)

        django_project, created = ODKProjects.objects.update_or_create(
            odk_id=project_data['id'],
            defaults={
                'name': project_data['name'],
                'description': project_data.get('description', ''),
                'archived': project_data.get('archived', False),
                'created_by': self.django_user if created else None
            }
        )

        self._log_action(
            'sync_project',
            'project',
            str(project_id),
            {
                'created': created,
                'django_id': django_project.id,
                'odk_account': self.current_account['id']
            },
            success=True
        )

        return django_project

    # def sync_project_forms(self, project_id: int) -> List[ODKForm]:
    #     """Synchronise les formulaires d'un projet ODK dans la base Django"""
    #     try:
    #         # Vérifie que le projet existe dans Django
    #         try:
    #             django_project = ODKProjects.objects.get(odk_id=project_id)
    #         except ODKProjects.DoesNotExist:
    #             django_project = self.sync_project(project_id)
    #
    #         # Récupère les formulaires
    #         forms_data = self.get_project_forms(project_id)
    #         synced_forms = []
    #
    #         for form_data in forms_data:
    #             django_form, created = ODKForm.objects.update_or_create(
    #                 project=django_project,
    #                 odk_id=form_data['xmlFormId'],
    #                 defaults={
    #                     'name': form_data.get('name', form_data['xmlFormId']),
    #                     'version': form_data.get('version', ''),
    #                     'state': form_data.get('state', 'open'),
    #                     'submissions_count': form_data.get('submissions', 0)
    #                 }
    #             )
    #             synced_forms.append(django_form)
    #
    #         self._log_action(
    #             'sync_forms',
    #             'form',
    #             str(project_id),
    #             {
    #                 'count': len(synced_forms),
    #                 'odk_account': self.current_account['id']
    #             },
    #             success=True
    #         )
    #
    #         return synced_forms
    #
    #     except Exception as e:
    #         self._log_action(
    #             'sync_forms',
    #             'form',
    #             str(project_id),
    #             {
    #                 'error': str(e),
    #                 'odk_account': self.current_account['id'] if self.current_account else None
    #             },
    #             success=False
    #         )
    #         raise

    def _log_action(self, action: str, resource_type: str, resource_id: str,
                   details: dict, success: bool = True) -> None:
        """Enregistre une action dans le journal d'audit"""
        try:
            ODKAuditLogs.objects.create(
                user=self.django_user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                success=success
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement dans le journal d'audit: {e}")
