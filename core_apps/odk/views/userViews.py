import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.odk.services.appUserServices import ODKAppUserService
from core_apps.projects.models import Projects

logger = logging.getLogger(__name__)


class AppUserListView(APIView):
    renderer_classes = [
        GenericJSONRenderer,
    ]
    object_label = "app_users"

    def get(self, request, project_id):
        """
        Handles the retrieval of ODK app users associated with a specific project.
        This includes checking the existence of the project in the database and 
        interacting with the ODK Central service to fetch the app users.
        """
        try:
            # Check if the project exists in django db
            try:
                django_project = Projects.objects.get(pkid=project_id)
            except Projects.DoesNotExist:
                return Response(
                    {"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Check if odk_id exists for the project
            if not django_project.odk_id:
                return Response(
                    {"detail": "Project is not associated with ODK"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get app users using the service
            with ODKAppUserService(request.user, request=request) as app_user_service:
                try:
                    app_users = app_user_service.get_project_app_users(
                        django_project.odk_id
                    )
                    return Response({"count":len(app_users), "results": app_users}, status=status.HTTP_200_OK)
                except Exception as e:
                    raise e
        except Exception as e:
            logger.error(f"Error retrieving app users: {e}")
            return Response(
                {
                    "error": "Unable to retrieve app users",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AppUserCreateView(APIView):
    renderer_classes = [
        GenericJSONRenderer,
    ]
    object_label = "app_user"

    def post(self, request, project_id):
        """
        Handles the creation of an ODK app user associated with a specific project.
        This includes checking the existence of the project in the database and 
        interacting with the ODK Central service to create the app user.
        """
        try:
            # Check if the project exists in django db
            try:
                django_project = Projects.objects.get(pkid=project_id)
            except Projects.DoesNotExist:
                return Response(
                    {"detail": "Project not found"}, status=status.HTTP_404_NOT_FOUND
                )

            # Check if odk_id exists for the project
            if not django_project.odk_id:
                return Response(
                    {"detail": "Project is not associated with ODK"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get display_name from request data
            display_name = request.data.get("display_name")
            if not display_name:
                return Response(
                    {"detail": "Display name is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Create app user using the service
            with ODKAppUserService(request.user, request=request) as app_user_service:
                try:
                    app_user = app_user_service.create_app_user(
                        django_project.odk_id, display_name
                    )
                    return Response( app_user, status=status.HTTP_201_CREATED)
                except Exception as e:
                    raise e
        except Exception as e:
            logger.error(f"Error creating app user: {e}")
            return Response(
                {
                    "error": "Unable to create app user",
                    "detail": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )