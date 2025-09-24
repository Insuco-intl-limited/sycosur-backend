from django.urls import path

from core_apps.odk.views import (
    AppUserCreateView,
    AppUserListView,
    ODKFormCreateView,
    ODKFormDeleteView,
    ODKFormDetailView,
    ODKFormDraftPublishView,
    ODKFormDraftSubmissionsView,
    ODKFormDraftTestView,
    ODKFormDraftView,
    ODKFormVersionsView,
    ODKFormVersionXMLView,
    ODKProjectFormsListView,
    ODKProjectListView,
)

app_name = "odk"

urlpatterns = [
    path("projects", ODKProjectListView.as_view(), name="projects-list"),
    # # Forms
    path(
        "projects/<int:project_id>/forms/", ODKFormCreateView.as_view(), name="add-form"
    ),
    path(
        "projects/<int:project_id>/forms",
        ODKProjectFormsListView.as_view(),
        name="project-forms-list",
    ),
    path(
        "projects/<int:project_id>/forms/<str:form_id>/",
        ODKFormDetailView.as_view(),
        name="form-detail",
    ),
    path(
        "projects/<int:project_id>/forms/<str:form_id>/delete/",
        ODKFormDeleteView.as_view(),
        name="form-delete",
    ),
    # App Users
    path(
        "projects/<int:project_id>/app-users/",
        AppUserCreateView.as_view(),
        name="create-app-user",
    ),
    path(
        "projects/<int:project_id>/app-users",
        AppUserListView.as_view(),
        name="list-app-users",
    ),
    # ================================
    # MVP ROUTES FOR DRAFT MANAGEMENT
    # ================================
    # Draft management
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/",
        ODKFormDraftView.as_view(),
        name="form-draft",
    ),
    # Draft publishing
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/publish/",
        ODKFormDraftPublishView.as_view(),
        name="form-draft-publish",
    ),
    # Draft test submissions
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/submissions/",
        ODKFormDraftSubmissionsView.as_view(),
        name="form-draft-submissions",
    ),
    # Enketo test URL for draft
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/test/",
        ODKFormDraftTestView.as_view(),
        name="form-draft-test",
    ),
    # Published version management
    path(
        "projects/<int:project_id>/forms/<str:form_id>/versions/",
        ODKFormVersionsView.as_view(),
        name="form-versions",
    ),
    # XML for specific version
    path(
        "projects/<int:project_id>/forms/<str:form_id>/versions/<str:version>.xml",
        ODKFormVersionXMLView.as_view(),
        name="form-version-xml",
    ),
]
