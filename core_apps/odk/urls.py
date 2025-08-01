from django.urls import path

from .views import (  # ODKProjectDetailView,; ODKFormDetailView,; ODKSyncProjectView,; ODKProjectPermissionListView,; ODKProjectPermissionDetailView,; ODKSystemStatusView
    ODKProjectListView,
)

app_name = "odk"

urlpatterns = [
    # Projets
    path("projects/", ODKProjectListView.as_view(), name="projects-list"),
    # path("projects/<int:project_id>/", ODKProjectDetailView.as_view(), name="project-detail"),
    # path("projects/<int:project_id>/sync/", ODKSyncProjectView.as_view(), name="project-sync"),
    #
    # # Formulaires
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
