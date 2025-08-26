import logging

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer

from ..odk.cache import ODKCacheManager
from .serializers import CreateProjectSerializer

logger = logging.getLogger(__name__)


class CreateProjectView(APIView):
    # renderer_classes = [GenericJSONRenderer]
    # object_label = "odk_project"

    def post(self, request):
        """Create a new project in the app without creating it in ODK Central"""
        try:
            serializer = CreateProjectSerializer(
                data=request.data, context={"request": request}
            )

            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            project = serializer.save()

            # Project is created only in the Django database
            # The ODK project will be created when a form is associated with this project

            # Invalidate projects cache for this user
            ODKCacheManager.invalidate_user_cache(request.user.id)

            # Return the created project
            return Response(status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return Response(
                {"error": "Unable to create project", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
