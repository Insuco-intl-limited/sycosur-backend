from django.urls import path

from core_apps.projects.views import ProjectListCreateView, ProjectDetailView, ProjectArchiveView

app_name = "projects"

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list-create"),
    path("<int:pkid>/", ProjectDetailView.as_view(), name="project-detail"),
    path("<int:pk>/archive/", ProjectArchiveView.as_view(), name="project-archive")
]
