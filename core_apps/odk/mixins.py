from rest_framework import status
from rest_framework.response import Response

from core_apps.projects.models import Projects


class ProjectValidationMixin:
    """Mixin to handle common project validation across ODK views"""

    def get_project_or_404(self, project_id):
        """Retrieve a project or return None if not found"""
        try:
            return Projects.objects.get(pkid=project_id)
        except Projects.DoesNotExist:
            return None

    def validate_project(self, project_id):
        """Validate project and return project or error response"""
        project = self.get_project_or_404(project_id)
        if project is None:
            return None, Response(
                {"error": "Project not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return project, None
