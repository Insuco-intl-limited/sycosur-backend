from rest_framework.permissions import BasePermission

from .models import ODKProjectPermissions, ODKProjects


class HasODKAccess(BasePermission):
    """Permission de base pour accéder à ODK"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            profile = request.user.profile
            # Tout rôle différent de None donne accès à l'API ODK
            return profile.odk_role is not None
        except:
            return False


class CanManageODKProjects(BasePermission):
    """Permission pour gérer les projets ODK"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            profile = request.user.profile
            # Seuls les managers et administrateurs peuvent gérer les projets
            return profile.odk_role in [
                profile.ODKRole.MANAGER,
                profile.ODKRole.ADMINISTRATOR,
            ]
        except:
            return False


class IsODKAdministrator(BasePermission):
    """Permission pour les administrateurs ODK"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            profile = request.user.profile
            return profile.odk_role == profile.ODKRole.ADMINISTRATOR
        except:
            return False


class HasODKProjectPermission(BasePermission):
    """Permission spécifique à un projet ODK"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        project_id = view.kwargs.get("project_id")
        if not project_id:
            return (
                True  # Si pas de projet spécifié, on vérifie juste l'accès ODK général
            )

        try:
            profile = request.user.profile

            # Admin et Manager peuvent tout faire
            if profile.odk_role in [
                profile.ODKRole.ADMINISTRATOR,
                profile.ODKRole.MANAGER,
            ]:
                return True

            # Pour les autres rôles, on vérifie les permissions spécifiques
            try:
                project = ODKProject.objects.get(odk_id=project_id)

                # Superviseur a accès par défaut
                if profile.odk_role == profile.ODKRole.SUPERVISOR:
                    return True

                # Vérifie les permissions explicites
                try:
                    permission = ODKProjectPermission.objects.get(
                        user=request.user, project=project
                    )

                    # Pour les requêtes en lecture seule
                    if request.method in ["GET", "HEAD", "OPTIONS"]:
                        return True

                    # Pour les modifications
                    return permission.permission_level in [
                        "contribute",
                        "manage",
                        "admin",
                    ]

                except ODKProjectPermission.DoesNotExist:
                    # Pas de permission explicite pour ce projet
                    return False

            except ODKProject.DoesNotExist:
                # Si le projet n'existe pas encore dans Django, seuls les superviseurs et +
                return profile.odk_role == profile.ODKRole.SUPERVISOR

        except:
            return False


class CanSubmitToODKProject(BasePermission):
    """Permission pour soumettre des données à un projet ODK"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        project_id = view.kwargs.get("project_id")
        if not project_id:
            return False

        try:
            profile = request.user.profile

            # Admin, Manager et Supervisor peuvent soumettre partout
            if profile.odk_role in [
                profile.ODKRole.ADMINISTRATOR,
                profile.ODKRole.MANAGER,
                profile.ODKRole.SUPERVISOR,
            ]:
                return True

            # Pour les collecteurs, on vérifie les permissions spécifiques
            try:
                project = ODKProjects.objects.get(odk_id=project_id)
                permission = ODKProjectPermissions.objects.get(
                    user=request.user, project=project
                )

                return permission.permission_level in ["contribute", "manage", "admin"]

            except (ODKProjects.DoesNotExist, ODKProjectPermissions.DoesNotExist):
                return False

        except:
            return False
