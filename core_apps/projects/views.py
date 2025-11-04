import logging

from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.common.utils import log_audit_action

from .models import Projects
from .serializers import ProjectSerializer

logger = logging.getLogger(__name__)


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    View for listing and creating projects.
    GET: List all projects
    POST: Create a new project
    Query parameters for GET:
    - include_deleted: if true, include deleted projects in the results (default: false)
    - include_archived: if true, include archived projects in the results (default: false)
    """

    queryset = Projects.objects.filter(deleted=False, archived=False)
    serializer_class = ProjectSerializer
    renderer_classes = [GenericJSONRenderer]

    def get_queryset(self):
        """Return projects with default exclusions, optionally including deleted/archived."""

        def _truthy(val: str) -> bool:
            if val is None:
                return False
            return val.strip().lower() in {"1", "true", "yes", "y", "on"}

        include_deleted = _truthy(self.request.query_params.get("add_deleted"))
        include_archived = _truthy(self.request.query_params.get("add_archived"))

        qs = Projects.objects.all()
        if not include_deleted:
            qs = qs.filter(deleted=False)
        if not include_archived:
            qs = qs.filter(archived=False)
        return qs

    @property
    def object_label(self):
        """
        Return different object labels based on the HTTP method:
        - 'projects' for GET (list) operations
        - 'project' for POST (create) operations
        """
        return "project" if self.request.method == "POST" else "projects"

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     return Response({"detail":"Project created"}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        """Save the project"""
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
    lookup_field = "pkid"

    def get_renderers(self):
        if self.request.method in ["PUT", "PATCH", "GET"]:
            return [GenericJSONRenderer()]
        return super().get_renderers()

    @property
    def object_label(self):
        if self.request.method in ["PUT", "PATCH", "GET"]:
            return "project"
        raise AttributeError("object_label is not defined for this HTTP method")

    def perform_update(self, serializer):
        """Update the project"""
        project = serializer.save()
        return Response(project, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Soft delete the project by setting deleted=True"""
        instance.deleted = True
        instance.deleted_at = timezone.now()
        instance.save()


class ProjectArchiveView(APIView):

    def patch(self, request, pk, *args, **kwargs):
        try:
            project = Projects.objects.get(pkid=pk, deleted=False)
        except Projects.DoesNotExist:
            return Response(
                {"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND
            )

        project.archived = True
        project.archived_at = timezone.now()
        project.save()

        return Response({"detail": "Project Archived"}, status=status.HTTP_200_OK)


class ProjectUnarchiveView(APIView):
    def patch(self, request, pk, *args, **kwargs):
        try:
            project = Projects.objects.get(pkid=pk, deleted=False, archived=True)
        except Projects.DoesNotExist:
            return Response(
                {"detail": "Project not found in archived projects."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project.archived = False
        project.archived_at = None
        project.save()
        # Log unarchive action
        log_audit_action(
            user=request.user,
            action="unarchive",
            resource_type="project",
            resource_id=str(project.id),
            details={"message": "Project unarchived"},
            success=True,
            request=request,
        )

        return Response({"detail": "Project Unarchived"}, status=status.HTTP_200_OK)


class ProjectRestoreView(APIView):
    def patch(self, request, pk, *args, **kwargs):
        try:
            project = Projects.objects.get(pkid=pk, deleted=True)
        except Projects.DoesNotExist:
            return Response(
                {"detail": "Project not found in deleted projects."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project.deleted = False
        project.deleted_at = None
        project.save()
        # Log restore action
        log_audit_action(
            user=request.user,
            action="restore",
            resource_type="project",
            resource_id=str(project.id),
            details={"message": "Project restored"},
            success=True,
            request=request,
        )
        return Response({"detail": "Project Restored"}, status=status.HTTP_200_OK)
