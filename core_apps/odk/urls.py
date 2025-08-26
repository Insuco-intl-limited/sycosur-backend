from django.urls import path

from core_apps.odk.views import ODKFormCreateView
from core_apps.odk.views import ODKProjectListView

app_name = "odk"

urlpatterns = [
    # # Projects
    path("projects", ODKProjectListView.as_view(), name="projects-list"),
    # path("projects/<int:project_id>/", ODKProjectDetailView.as_view(), name="project-detail"),
    # path("projects/<int:project_id>/sync/", ODKSyncProjectView.as_view(), name="project-sync"),

    # # Forms
    path("projects/<int:project_id>/forms/", ODKFormCreateView.as_view(), name="add-form"),
    # path("projects/<int:project_id>/forms/<str:form_id>/", ODKFormDetailView.as_view(), name="form-detail"),
]
