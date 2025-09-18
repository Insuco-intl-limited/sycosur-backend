import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.odk.services import ODKCentralService
from core_apps.projects.models import Projects

from ..cache import ODKCacheManager

logger = logging.getLogger(__name__)


class ODKFormCreateView(APIView):
    renderer_classes = [
        GenericJSONRenderer,
    ]
    object_label = "project_form"
    # permission_classes = [IsAuthenticated]

    def post(self, request, project_id):
        """
        Handles the creation and uploading of an ODK form associated with a specific project. This includes checking the
        existence of the project in the database, validating the uploaded form file, and interacting with the ODK Central
        service to create the form and associate it with a corresponding ODK project. If necessary, the operation rolls back
        changes in case of failures.
        """
        created_new_odk_project = False
        odk_project_id = None

        try:
            # Check if the project exists in django db
            try:
                django_project = Projects.objects.get(pkid=project_id)
            except Projects.DoesNotExist:
                return Response(
                    {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Check et validate the file in the request
            form_file = request.FILES.get("form")
            if not form_file:
                return Response(
                    {"error": "Form file is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get the file name and check extension
            filename = form_file.name
            file_extension = filename.split(".")[-1].lower()
            if file_extension not in ["xml", "xlsx", "xls"]:
                return Response(
                    {"error": "Invalid file extension"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            form_data = form_file.read()
            form_id = request.query_params.get("form_id")
            ignore_warnings = (
                request.query_params.get("ignore_warnings", "false") == "true"
            )
            publish = request.query_params.get("publish", "false") == "true"

            # Appel du service ODK
            with ODKCentralService(request.user, request=request) as odk_service:
                try:
                    # Check if django_project is a string before accessing odk_id attribute
                    if isinstance(django_project, str):
                        return Response(
                            {"error": "Invalid project format"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    had_odk_project = django_project.odk_id is not None

                    odk_project_id = odk_service.ensure_odk_project_exists(
                        django_project
                    )
                    logger.info("odk_project_id: %s", odk_project_id)
                    if not had_odk_project:
                        created_new_odk_project = True
                    form = odk_service.create_form(
                        odk_project_id,
                        form_data,
                        filename,
                        form_id=form_id,
                        ignore_warnings=ignore_warnings,
                        publish=publish,
                    )
                    ODKCacheManager.invalidate_project_cache(
                        request.user.id, odk_project_id
                    )
                    return Response({"form": form}, status=status.HTTP_201_CREATED)
                except Exception as e:
                    if created_new_odk_project:
                        self.rollback_project_creation(
                            odk_service, odk_project_id, django_project
                        )
                    raise e
        except Exception as e:
            logger.error(f"Error creating form: {e}")
            return Response(
                {
                    "error": "Unable to create form",
                    "detail": str(e),
                    "message": "Form creation failed and all changes have been rolled back",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def rollback_project_creation(
        self, odk_service, odk_project_id, django_project
    ) -> None:
        try:
            logger.info(
                f"Rolling back ODK project creation for project {django_project.pkid}"
            )
            odk_service.delete_project(odk_project_id)
            django_project.odk_id = None
            django_project.save()
            logger.info(
                f"Successfully rolled back ODK project creation for project {django_project.pkid}"
            )
        except Exception as rollback_error:
            logger.error(f"Error rolling back ODK project creation: {rollback_error}")


class ODKProjectFormsListView(APIView):
    renderer_classes = [
        GenericJSONRenderer,
    ]
    object_label = "project_forms"
    # permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """
        Handles the retrieval of all ODK forms associated with a specific project. This includes checking the existence
        of the project in the database and interacting with the ODK Central service to fetch the list of forms.
        """
        try:
            try:
                django_project = Projects.objects.get(pkid=project_id)
            except Projects.DoesNotExist:
                return Response(
                    {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Appel du service ODK
            with ODKCentralService(request.user, request=request) as odk_service:
                try:
                    forms = odk_service.get_project_forms(django_project.odk_id)
                    return Response({"forms": forms}, status=status.HTTP_200_OK)
                except Exception as e:
                    raise e
        except Exception as e:
            logger.error(f"Error listing forms: {e}")
            return Response(
                {
                    "error": "Unable to list forms",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )