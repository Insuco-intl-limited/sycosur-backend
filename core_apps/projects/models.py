from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel

User = get_user_model()


class Projects(TimeStampedModel):
    odk_id = models.BigIntegerField(
        unique=True, verbose_name="ODK Project ID", null=True
    )
    name = models.CharField(
        max_length=150, verbose_name="Project name", unique=True, null=False
    )
    description = models.TextField(null=True, verbose_name="Description")
    deleted = models.BooleanField(default=False, verbose_name="Deleted", null=True)
    deleted_at = models.DateTimeField(null=True, verbose_name="Deleted at")
    archived = models.BooleanField(default=False, verbose_name="Archived", null=True)
    archived_at = models.DateTimeField(null=True, verbose_name="Archived at")
    last_sync = models.DateTimeField(
        auto_now=True, verbose_name="Last synchronization", null=True
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Created by",
        related_name="owner",
    )

    class Meta:
        db_table = "projects"
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self) -> str:
        return self.name

    def get_user_permissions(self):
        """Get user's permissions for this project"""
        try:
            return ProjectPermissions.objects.get(user=User, project=self)
        except ProjectPermissions.DoesNotExist:
            return None


class ProjectPermissions(TimeStampedModel):
    class Levels(models.TextChoices):
        READER = (
            "read",
            _("View Project"),
        )
        CONTRIBUTOR = (
            "contribute",
            _("Project Contributor"),
        )
        MANAGER = (
            "manage",
            _("Project Manager"),
        )
        ADMINISTRATOR = (
            "administrator",
            _("Project Administrator"),
        )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="odk_permissions",
        verbose_name="User",
    )
    permission_level = models.CharField(
        max_length=100,
        choices=Levels.choices,
        default=Levels.READER,
    )
    project = models.ForeignKey(
        Projects, on_delete=models.CASCADE, verbose_name="Project"
    )
    granted_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Granted by"
    )

    class Meta:
        db_table = "project_permissions"
        verbose_name = "Project Permission"
        verbose_name_plural = "Project Permissions"

    def __str__(self) -> str:
        return f"{self.user.email} - {self.project.name} - {self.get_permission_level_display()}"
