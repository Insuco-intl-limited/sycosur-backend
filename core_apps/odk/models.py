from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core_apps.common.models import TimeStampedModel

User = get_user_model()

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


class AuditLogs(TimeStampedModel):
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
        db_table = "audit_logs"
        verbose_name = "Sycosur Audit Log"
        verbose_name_plural = "Sycosur Audit Logs"

    def __str__(self) -> str:
        status = "succeeded" if self.success else "failed"
        return f"{self.action} ({self.resource_type}) par {self.user.get_full_name()} - {status}"
