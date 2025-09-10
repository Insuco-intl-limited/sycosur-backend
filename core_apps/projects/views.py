import logging
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from core_apps.common.renderers import GenericJSONRenderer
from .models import Projects
from .serializers import ProjectSerializer

logger = logging.getLogger(__name__)


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating projects.
    
    GET: List all projects
    POST: Create a new project
    """
    queryset = Projects.objects.filter(deleted=False, archived=False)
    serializer_class = ProjectSerializer
    renderer_classes = [GenericJSONRenderer]
    @property
    def object_label(self):
        """
        Return different object labels based on the HTTP method:
        - 'projects' for GET (list) operations
        - 'project' for POST (create) operations
        """
        if self.request.method == 'POST':
            return "project"
        return "projects"

    def perform_create(self, serializer):
        """Save the project """
        project = serializer.save()



class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating and deleting a project.
    
    GET: Retrieve a project
    PUT/PATCH: Update a project
    DELETE: Delete a project
    """
    queryset = Projects.objects.filter(deleted=False)
    serializer_class = ProjectSerializer
    renderer_classes = [GenericJSONRenderer]
    lookup_field = "pkid"
    object_label = "project"

    def perform_update(self, serializer):
        """Update the project """
        project = serializer.save()

    
    def perform_destroy(self, instance):
        """Soft delete the project by setting deleted=True"""
        instance.deleted = True
        instance.deleted_at = timezone.now()
        instance.save()



class ProjectArchiveView(APIView):
    renderer_classes = [GenericJSONRenderer,]
    object_label = "project"

    def patch(self, request, pk, *args, **kwargs):
        try:
            project = Projects.objects.get(pkid=pk, deleted=False)
        except Projects.DoesNotExist:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)

        project.archived = True
        project.archived_at = timezone.now()
        project.save()

        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)