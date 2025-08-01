from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import ODKProjects, ODKProjectPermissions
from .cache import ODKCacheManager

User = get_user_model()


@receiver(post_save, sender=ODKProjects)
def invalidate_project_cache(sender, instance, created, **kwargs):
    """Invalide le cache lorsqu'un projet est modifié"""
    # Invalide le cache pour tous les utilisateurs ayant une permission sur ce projet
    users_with_permission = User.objects.filter(
        odk_permissions__project=instance
    ).distinct()

    for user in users_with_permission:
        ODKCacheManager.invalidate_project_cache(user.id, instance.odk_id)


# @receiver(post_save, sender=ODKForms)
# def invalidate_form_cache(sender, instance, created, **kwargs):
#     """Invalide le cache lorsqu'un formulaire est modifié"""
#     # Invalide le cache pour tous les utilisateurs ayant une permission sur le projet
#     users_with_permission = User.objects.filter(
#         odk_permissions__project=instance.project
#     ).distinct()
#
#     for user in users_with_permission:
#         ODKCacheManager.invalidate_project_cache(user.id, instance.project.odk_id)


@receiver(post_save, sender=ODKProjectPermissions)
def invalidate_permission_cache(sender, instance, created, **kwargs):
    """Invalide le cache lorsqu'une permission est modifiée"""
    # Invalide le cache pour l'utilisateur concerné
    ODKCacheManager.invalidate_project_cache(instance.user.id, instance.project.odk_id)
    ODKCacheManager.invalidate_user_cache(instance.user.id)


# @receiver(post_delete, sender=ODKProjectPermissions)
# def invalidate_permission_cache_on_delete(sender, instance, **kwargs):
#     """Invalide le cache lorsqu'une permission est supprimée"""
#     # Invalide le cache pour l'utilisateur concerné
#     ODKCacheManager.invalidate_project_cache(instance.user.id, instance.project.odk_id)
#     ODKCacheManager.invalidate_user_cache(instance.user.id)
