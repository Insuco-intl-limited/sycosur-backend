import logging

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_apps.common.renderers import GenericJSONRenderer
from core_apps.odk.services.allServices import ODKCentralService

from .cache import ODKCacheManager

logger = logging.getLogger(__name__)


class ODKProjectListView(APIView):
    permission_classes = [IsAuthenticated]
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
            with ODKCentralService(request.user) as odk_service:
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


# class ODKProjectDetailView(APIView):
#     permission_classes = [IsAuthenticated, HasODKAccess, HasODKProjectPermission]
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "odk_project"
#
#     def get(self, request, project_id):
#         """Détail d'un projet ODK avec ses formulaires"""
#         # Vérifie le cache pour les formulaires
#         cached_forms = ODKCacheManager.get_cached_project_forms(
#             request.user.id,
#             project_id
#         )
#
#         try:
#             with ODKCentralService(request.user) as odk_service:
#                 # Récupère les détails du projet
#                 project_data = odk_service.get_project(project_id)
#
#                 # Pour les formulaires, utilise le cache ou récupère depuis ODK
#                 if cached_forms:
#                     forms = cached_forms
#                     forms_cached = True
#                 else:
#                     forms = odk_service.get_project_forms(project_id)
#                     ODKCacheManager.cache_project_forms(request.user.id, project_id, forms)
#                     forms_cached = False
#
#                 # Synchronise le projet dans la base Django si nécessaire
#                 try:
#                     django_project = ODKProject.objects.get(odk_id=project_id)
#                 except ODKProject.DoesNotExist:
#                     django_project = odk_service.sync_project(project_id)
#
#                 # Récupère la permission de l'utilisateur pour ce projet
#                 user_permission = django_project.get_user_permission(request.user)
#
#                 return Response({
#                     'project': project_data,
#                     'forms': forms,
#                     'forms_cached': forms_cached,
#                     'django_id': django_project.id,
#                     'user_permission': user_permission.permission_level if user_permission else None
#                 }, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             logger.error(f"Erreur lors de la récupération des détails du projet ODK {project_id}: {e}")
#             return Response({
#                 'error': 'Impossible de récupérer les détails du projet',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# class ODKFormDetailView(APIView):
#     permission_classes = [IsAuthenticated, HasODKAccess, HasODKProjectPermission]
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "odk_form"
#
#     def get(self, request, project_id, form_id):
#         """Détail d'un formulaire ODK avec ses soumissions"""
#         # Vérifie le cache pour les soumissions
#         cached_submissions = ODKCacheManager.get_cached_form_submissions(
#             request.user.id,
#             project_id,
#             form_id
#         )
#
#         try:
#             with ODKCentralService(request.user) as odk_service:
#                 # Pour les soumissions, utilise le cache ou récupère depuis ODK
#                 if cached_submissions:
#                     submissions = cached_submissions
#                     submissions_cached = True
#                 else:
#                     submissions = odk_service.get_form_submissions(project_id, form_id)
#                     ODKCacheManager.cache_form_submissions(
#                         request.user.id,
#                         project_id,
#                         form_id,
#                         submissions
#                     )
#                     submissions_cached = False
#
#                 # Récupère la liste des formulaires pour identifier celui-ci
#                 forms = odk_service.get_project_forms(project_id)
#                 current_form = next((f for f in forms if f['xmlFormId'] == form_id), None)
#
#                 if not current_form:
#                     return Response({
#                         'error': 'Formulaire non trouvé'
#                     }, status=status.HTTP_404_NOT_FOUND)
#
#                 # Synchronise le formulaire dans la base Django si nécessaire
#                 try:
#                     django_project = ODKProject.objects.get(odk_id=project_id)
#                     try:
#                         django_form = ODKForm.objects.get(project=django_project, odk_id=form_id)
#                     except ODKForm.DoesNotExist:
#                         odk_service.sync_project_forms(project_id)
#                         django_form = ODKForm.objects.get(project=django_project, odk_id=form_id)
#                 except (ODKProject.DoesNotExist, ODKForm.DoesNotExist):
#                     django_form = None
#
#                 return Response({
#                     'form': current_form,
#                     'submissions': submissions,
#                     'submissions_cached': submissions_cached,
#                     'submissions_count': len(submissions),
#                     'django_id': django_form.id if django_form else None
#                 }, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             logger.error(f"Erreur lors de la récupération des détails du formulaire ODK {form_id}: {e}")
#             return Response({
#                 'error': 'Impossible de récupérer les détails du formulaire',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# class ODKSyncProjectView(APIView):
#     permission_classes = [IsAuthenticated, HasODKAccess, CanManageODKProjects]
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "sync_result"
#
#     def post(self, request, project_id):
#         """Synchronise un projet ODK avec la base Django"""
#         try:
#             with ODKCentralService(request.user) as odk_service:
#                 # Synchronise le projet
#                 project = odk_service.sync_project(project_id)
#
#                 # Synchronise ses formulaires
#                 forms = odk_service.sync_project_forms(project_id)
#
#                 # Invalide le cache
#                 ODKCacheManager.invalidate_project_cache(request.user.id, project_id)
#
#                 return Response({
#                     'success': True,
#                     'project': ODKProjectSerializer(project, context={'request': request}).data,
#                     'forms_count': len(forms),
#                     'message': f'Projet {project.name} synchronisé avec succès'
#                 }, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             logger.error(f"Erreur lors de la synchronisation du projet ODK {project_id}: {e}")
#             return Response({
#                 'success': False,
#                 'error': 'Impossible de synchroniser le projet',
#                 'detail': str(e)
#             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#
# class ODKProjectPermissionListView(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated, HasODKAccess, CanManageODKProjects]
#     serializer_class = ODKProjectPermissionSerializer
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "odk_permissions"
#
#     def get_queryset(self):
#         project_id = self.kwargs.get('project_id')
#
#         if project_id:
#             # Récupère les permissions pour un projet spécifique
#             project = get_object_or_404(ODKProject, odk_id=project_id)
#             return ODKProjectPermission.objects.filter(project=project)
#
#         # Sinon, toutes les permissions que l'utilisateur peut voir
#         if self.request.user.profile.odk_role == self.request.user.profile.ODKRole.ADMINISTRATOR:
#             return ODKProjectPermission.objects.all()
#
#         # Pour les managers, seulement leurs projets
#         return ODKProjectPermission.objects.filter(
#             project__in=ODKProject.objects.filter(created_by=self.request.user)
#         )
#
#     def perform_create(self, serializer):
#         serializer.save(granted_by=self.request.user)
#
#
# class ODKProjectPermissionDetailView(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated, HasODKAccess, CanManageODKProjects]
#     serializer_class = ODKProjectPermissionSerializer
#     queryset = ODKProjectPermission.objects.all()
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "odk_permission"
#
#     def perform_update(self, serializer):
#         serializer.save(granted_by=self.request.user)
#
#
# class ODKSystemStatusView(APIView):
#     permission_classes = [IsAuthenticated, HasODKAccess]
#     renderer_classes = [GenericJSONRenderer]
#     object_label = "odk_status"
#
#     def get(self, request):
#         """Vérifie l'état du système ODK Central"""
#         try:
#             with ODKCentralService(request.user) as odk_service:
#                 # Tente de récupérer les projets pour vérifier la connexion
#                 projects = odk_service.get_projects()
#
#                 # Vérifie le pool de comptes
#                 account_pool_size = len(odk_account_pool.accounts)
#                 account_pool_available = odk_account_pool.account_queue.qsize()
#
#                 return Response({
#                     'status': 'online',
#                     'api_url': odk_service.base_url,
#                     'user_role': request.user.profile.get_odk_role_display(),
#                     'account_pool': {
#                         'total': account_pool_size,
#                         'available': account_pool_available,
#                         'busy': account_pool_size - account_pool_available
#                     },
#                     'projects_count': len(projects),
#                     'timestamp': timezone.now().isoformat()
#                 }, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             logger.error(f"Erreur lors de la vérification de l'état du système ODK: {e}")
#             return Response({
#                 'status': 'offline',
#                 'error': str(e),
#                 'timestamp': timezone.now().isoformat()
#             }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
# # Create your views here.
#
