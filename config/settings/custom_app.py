from django.contrib.auth.apps import AuthConfig
from django.utils.translation import gettext_lazy as _

from admin_interface.apps import AdminInterfaceConfig


class CustomAdminInterfaceConfig(AdminInterfaceConfig):
    verbose_name = _("Theme Settings")


class CustomAuthConfig(AuthConfig):
    verbose_name = _("permissions & groups")
