from django.urls import path
from core_apps.projects.views import CreateProjectView

app_name = "projects"

urlpatterns = [
    # Projets Sycosur
    path("", CreateProjectView.as_view(), name="add-project"),
    # path("projects/<int:project_id>/", ODKProjectDetailView.as_view(), name="project-detail"),
    # path("projects/<int:project_id>/sync/", ODKSyncProjectView.as_view(), name="project-sync"),
]
