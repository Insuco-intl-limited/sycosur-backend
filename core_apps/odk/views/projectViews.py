import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.odk.services.allServices import ODKCentralService
from ..cache import ODKCacheManager
from ..serializers import ODKCreateProjectSerializer


logger = logging.getLogger(__name__)


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
            with ODKCentralService(request.user,request=request) as odk_service:
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
