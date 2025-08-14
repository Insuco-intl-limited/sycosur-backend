from django.urls import path

from core_apps.odk.views.formViews import ODKFormCreateView
from core_apps.odk.views.projectViews import ODKProjectListView, ODKProjectCreateView
# from core_apps.odk.views.views import FormUploadView

app_name = "odk"

urlpatterns = [
    # Projets
    path("projects", ODKProjectListView.as_view(), name="projects-list"),
    path("projects/", ODKProjectCreateView.as_view(), name="add-project"),
    # path("projects/<int:project_id>/", ODKProjectDetailView.as_view(), name="project-detail"),
    # path("projects/<int:project_id>/sync/", ODKSyncProjectView.as_view(), name="project-sync"),
    #
    # # Formulaires
    # path('upload-form/', FormUploadView.as_view(), name='form-upload'),
    path("projects/<int:project_id>/forms/", ODKFormCreateView.as_view(), name="add-form"),
    # path("projects/<int:project_id>/forms/<str:form_id>/", ODKFormDetailView.as_view(), name="form-detail"),
    #
    # # Permissions
    # path("permissions/", ODKProjectPermissionListView.as_view(), name="permissions-list"),
    # path("projects/<int:project_id>/permissions/", ODKProjectPermissionListView.as_view(), name="project-permissions"),
    # path("permissions/<int:pk>/", ODKProjectPermissionDetailView.as_view(), name="permission-detail"),
    #
    # # Système
    # path("status/", ODKSystemStatusView.as_view(), name="system-status"),
]
