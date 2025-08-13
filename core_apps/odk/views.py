import logging
import mimetypes
from concurrent.futures import TimeoutError as ConcurrentTimeoutError

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from celery.exceptions import TimeoutError as CeleryTimeoutError

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.odk.services.allServices import ODKCentralService
from core_apps.odk.models import ODKProjects
from .cache import ODKCacheManager
from .serializers import ODKCreateProjectSerializer
logger = logging.getLogger(__name__)
from .tasks import convert_excel_to_xform_task

class ODKProjectListView(APIView):
    renderer_classes = [GenericJSONRenderer]
    object_label = "odk_projects"

    def get(self, request):
        cached_projects = ODKCacheManager.get_cached_user_projects(request.user.id)
        if cached_projects:
            # Retourne les données en cache
            return Response(
                {
                    "count": len(cached_projects),
                    "results": cached_projects,
                    "cached": True,
                    "user_role": request.user.profile.get_odk_role_display(),
                },
                status=status.HTTP_200_OK,
            )

        # Sinon, récupère depuis ODK avec le pool de comptes
        try:
            with ODKCentralService(request.user) as odk_service:
                projects = odk_service.get_accessible_projects()

                # Met en cache le résultat
                ODKCacheManager.cache_user_projects(request.user.id, projects)

                return Response(
                    {
                        "count": len(projects),
                        "results": projects,
                        "cached": False,
                        "user_role": request.user.profile.get_odk_role_display(),
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des projets ODK: {e}")
            return Response(
                {"error": "Impossible de récupérer les projets", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class ODKProjectCreateView(APIView):
    # renderer_classes = [GenericJSONRenderer]
    # object_label = "odk_project"

    def post(self, request):
        """Create a new project in the app without creating it in ODK Central"""
        try:
            # Create project in Django database first
            serializer = ODKCreateProjectSerializer(
                data=request.data,
                context={'request': request}
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            project = serializer.save()

            # Project is created only in the Django database
            # The ODK project will be created when a form is associated with this project

            # Invalidate projects cache for this user
            ODKCacheManager.invalidate_user_cache(request.user.id)

            # Return the created project
            return Response(
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return Response(
                {'error': 'Unable to create project', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ODKFormCreateView(APIView):
    """
    Vue pour la création de formulaires ODK.
    Accepte des fichiers XML ou XLSX et les envoie directement à l'API ODK Central
    sans conversion préalable.
    """
    renderer_classes = [GenericJSONRenderer]
    object_label = "odk_form"

    def validate_file(self, file):
        valid_extensions = ['.xml', '.xlsx']
        file_extension = f".{file.name.split('.')[-1].lower()}"
        if file_extension not in valid_extensions:
            raise ValueError(f"Invalid file extension. Expected {', '.join(valid_extensions)}, got {file_extension}")

        mime_type, _ = mimetypes.guess_type(file.name)
        valid_mimes = [
            'text/xml',
            'application/xml',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]

        # Additional check for XML files that might not be detected properly
        if file_extension == '.xml':

            file.seek(0)
            try:
                first_bytes = file.read(100).decode('utf-8', errors='ignore').strip()
                file.seek(0)
                if first_bytes.startswith('<?xml') or first_bytes.startswith('<'):
                    return file_extension
                else:
                    raise ValueError("File does not appear to be valid XML")
            except Exception:
                file.seek(0)
                raise ValueError("Unable to read file content")

        # For Excel files, check mime type
        if file_extension == '.xlsx':
            if mime_type not in valid_mimes:
                # Additional check by reading file signature
                file.seek(0)
                file_signature = file.read(4)
                file.seek(0)
                # Excel files start with PK (ZIP signature)
                if file_signature[:2] == b'PK':
                    return file_extension
                else:
                    raise ValueError("File does not appear to be a valid Excel file")
            return file_extension

        if mime_type not in valid_mimes:
            raise ValueError(f"Invalid file type. Expected XML or Excel, got {mime_type}")

        return file_extension

    def post(self, request, project_id):
        try:
            # Vérifier le projet Django
            try:
                django_project = ODKProjects.objects.get(pk=project_id)
            except ODKProjects.DoesNotExist:
                return Response(
                    {'error': 'Project not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Vérifier le fichier
            form_file = request.FILES.get('form')
            if not form_file:
                return Response(
                    {'error': 'Form file is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Valider la taille du fichier
            if form_file.size > 100 * 1024 * 1024:
                return Response(
                    {'error': 'File too large', 'detail': 'Maximum file size is 100MB'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Valider le type de fichier
            try:
                file_extension = self.validate_file(form_file)
            except ValueError as e:
                return Response(
                    {'error': 'Invalid file', 'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Traiter le fichier directement sans conversion
            form_file.seek(0)  # Remettre le curseur au début du fichier
            is_xlsx = file_extension == '.xlsx'
            
            if is_xlsx:
                # Pour les fichiers XLSX, utiliser directement les données binaires
                form_data = form_file.read()
                # logger.info(form_data)
            else:
                # Pour les fichiers XML, lire le contenu
                form_data = form_file.read()
                if not is_xlsx:
                    # Décoder en texte uniquement pour les fichiers XML (pour la compatibilité avec le code existant)
                    try:
                        form_data = form_data.decode('utf-8')
                    except UnicodeDecodeError:
                        return Response(
                            {'error': 'Invalid XML file', 'detail': 'The file could not be decoded as UTF-8'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            # Créer le formulaire dans ODK Central
            created_new_odk_project = False
            with ODKCentralService(request.user) as odk_service:
                try:
                    had_odk_project = django_project.odk_id is not None
                    odk_project_id = odk_service.ensure_odk_project_exists(django_project)
                    if not had_odk_project:
                        created_new_odk_project = True

                    form = odk_service.create_form(odk_project_id, form_data, is_xlsx=is_xlsx)
                    ODKCacheManager.invalidate_project_cache(request.user.id, odk_project_id)

                    return Response(
                        {'form': form},
                        status=status.HTTP_201_CREATED
                    )

                except Exception as e:
                    if created_new_odk_project:
                        try:
                            logger.info(f"Rolling back ODK project creation for project {django_project.pkid}")
                            odk_service.delete_project(odk_project_id)
                            django_project.odk_id = None
                            django_project.save()
                            logger.info(f"Successfully rolled back ODK project creation for project {django_project.pkid}")
                        except Exception as rollback_error:
                            logger.error(f"Error rolling back ODK project creation: {rollback_error}")
                    raise e

        except Exception as e:
            logger.error(f"Error creating form: {e}")
            return Response(
                {
                    'error': 'Unable to create form',
                    'detail': str(e),
                    'message': 'Form creation failed and all changes have been rolled back'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )