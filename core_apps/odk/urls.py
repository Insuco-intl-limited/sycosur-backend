from django.urls import path

from core_apps.odk.views import (
    AppUserCreateView,
    AppUserListView,
    FormCreateView,
    FormDeleteView,
    FormDetailView,
    FormDraftPublishView,
    FormDraftSubmissionsView,
    FormDraftView,
    FormVersionsView,
    FormVersionXMLView,
    ProjectFormsListView,
    ODKProjectListView,
    FormSubmissionsListView,
    FormSubmissionsCSVExportView,
    FormSubmissionDetailView,
    CreateListAccessView,
)

app_name = "odk"

urlpatterns = [
    path("projects", ODKProjectListView.as_view(), name="projects-list"),
    # # Forms
    path(
        "projects/<int:project_id>/forms/", FormCreateView.as_view(), name="add-form"
    ),
    # List forms in a project
    path(
        "projects/<int:project_id>/forms",
        ProjectFormsListView.as_view(),
        name="project-forms-list",
    ),
    # Form details
    path(
        "projects/<int:project_id>/forms/<str:form_id>/",
        FormDetailView.as_view(),
        name="form-detail",
    ),
    # Form deletion
    path(
        "projects/<int:project_id>/forms/<str:form_id>/delete/",
        FormDeleteView.as_view(),
        name="form-delete",
    ),
    # Submissions (published form)
    path(
        "projects/<int:project_id>/forms/<str:form_id>/submissions/",
        FormSubmissionsListView.as_view(),
        name="form-submissions",
    ),
    # Submissions CSV export
    path(
        "projects/<int:project_id>/forms/<str:form_id>/submissions.csv",
        FormSubmissionsCSVExportView.as_view(),
        name="form-submissions-csv",
    ),
    # Submission details
    path(
        "projects/<int:project_id>/forms/<str:form_id>/submissions/<str:instance_id>/",
        FormSubmissionDetailView.as_view(),
        name="form-submission-detail",
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
        FormDraftView.as_view(),
        name="form-draft",
    ),
    # Draft publishing
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/publish/",
        FormDraftPublishView.as_view(),
        name="form-draft-publish",
    ),
    # Draft test submissions
    path(
        "projects/<int:project_id>/forms/<str:form_id>/draft/submissions/",
        FormDraftSubmissionsView.as_view(),
        name="form-draft-submissions",
    ),
    # Published version management
    path(
        "projects/<int:project_id>/forms/<str:form_id>/versions/",
        FormVersionsView.as_view(),
        name="form-versions",
    ),
    # XML for specific version
    path(
        "projects/<int:project_id>/forms/<str:form_id>/versions/<str:version>.xml",
        FormVersionXMLView.as_view(),
        name="form-version-xml",
    ),
    # Public access to form definition
    path(
        "projects/<int:project_id>/forms/<str:form_id>/public-links/",
        CreateListAccessView.as_view(),
        name="form-public-links",
    ),

]
