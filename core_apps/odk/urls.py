from django.urls import path

from core_apps.odk.views import (
    ODKFormCreateView, 
    ODKProjectListView, 
    ODKProjectFormsListView, 
    AppUserCreateView, 
    AppUserListView,
    ODKFormDetailView,
    ODKFormDeleteView
)

app_name = "odk"

urlpatterns = [
    path("projects", ODKProjectListView.as_view(), name="projects-list"),
    # path("projects/<int:project_id>/", ODKProjectDetailView.as_view(), name="project-detail"),
    # path("projects/<int:project_id>/sync/", ODKSyncProjectView.as_view(), name="project-sync"),
    # # Forms
    path("projects/<int:project_id>/forms/", ODKFormCreateView.as_view(), name="add-form"),
    path("projects/<int:project_id>/forms", ODKProjectFormsListView.as_view(), name="project-forms-list"),
    path("projects/<int:project_id>/forms/<str:form_id>/", ODKFormDetailView.as_view(), name="form-detail"),
    path("projects/<int:project_id>/forms/<str:form_id>/delete/", ODKFormDeleteView.as_view(), name="form-delete"),
    
    # App Users
    path("projects/<int:project_id>/app-users/", AppUserCreateView.as_view(), name="create-app-user"),
    path("projects/<int:project_id>/app-users", AppUserListView.as_view(), name="list-app-users"),
]
