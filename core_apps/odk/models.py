from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel

User = get_user_model()


class ODKProjects(TimeStampedModel):
    odk_id = models.BigIntegerField(unique=True, verbose_name="ODK Project ID", null=True)
    name = models.CharField(max_length=150, verbose_name="Project name", unique=True)
    description = models.TextField(null=True, verbose_name="Description")
    archived = models.BooleanField(default=False, verbose_name="Archived")
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
            return ODKProjectPermissions.objects.get(user=User, project=self)
        except ODKProjectPermissions.DoesNotExist:
            return None


class ODKProjectPermissions(TimeStampedModel):
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
        ODKProjects, on_delete=models.CASCADE, verbose_name="Project"
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


class ODKUserSessions(TimeStampedModel):
    odk_token = models.CharField(verbose_name="Odk Token")
    token_expired_at = models.DateTimeField(verbose_name="Odk Token Expired", null=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, verbose_name="Sycosur User"
    )
    actor_id = models.BigIntegerField(verbose_name="Odk Actor ID", null=True)

    class Meta:
        db_table = "odk_user_sessions"
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"

    def __str__(self) -> str:
        return f"{self.user.email} Session"

    def is_valid(self) -> bool:
        if self.token_expired_at is None:
            return False
        return self.token_expired_at > timezone.now()


class ODKAuditLogs(TimeStampedModel):
    class Resources(models.TextChoices):
        PROJECT = (
            "project",
            _("Project"),
        )
        FORM = (
            "form",
            _("Form"),
        )
        SUBMISSION = (
            "submission",
            _("Submission"),
        )
        USER = (
            "user",
            _("User"),
        )

    resource_type = models.CharField(
        verbose_name="Resource Type",
        max_length=30,
        choices=Resources.choices,
        default=None,
    )
    # Identifies the specific resource instance affected (e.g., the ID of a project or user)
    resource_id = models.CharField(verbose_name="Resource ID")
    details = models.JSONField(verbose_name="Details")
    success = models.BooleanField(default=True, verbose_name="Success")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="User", related_name="odk_logs"
    )
    action = models.CharField(verbose_name="Action", max_length=100)
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address", null=True, blank=True
    )

    class Meta:
        db_table = "odk_audit_logs"
        verbose_name = "ODK Audit Log"
        verbose_name_plural = "ODK Audit Logs"

    def __str__(self) -> str:
        status = "succeeded" if self.success else "failed"
        return f"{self.action} ({self.resource_type}) par {self.user.get_full_name()} - {status}"
