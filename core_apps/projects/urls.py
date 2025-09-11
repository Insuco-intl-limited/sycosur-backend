from django.urls import path

from core_apps.projects.views import (
    ProjectArchiveView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectRestoreView,
    ProjectUnarchiveView,
)

app_name = "projects"

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pkid>/", ProjectDetailView.as_view(), name="project-detail"),
    path("<int:pk>/archive/", ProjectArchiveView.as_view(), name="project-archive"),
    path(
        "<int:pk>/unarchive/", ProjectUnarchiveView.as_view(), name="project-unarchive"
    ),
    path("<int:pk>/restore/", ProjectRestoreView.as_view(), name="project-restore"),
]
