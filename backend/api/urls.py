from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.register),
    path("auth/login/", views.login),
    # Projects (owner-scoped)
    path("projects/", views.projects),
    path("projects/<int:pk>/", views.project_detail),
    path("projects/<int:pk>/events/", views.project_events),
    path("projects/<int:pk>/start-session/", views.start_session),
    path("projects/<int:pk>/end-session/", views.end_session),
    path("projects/<int:pk>/submit/", views.submit_project),
    # Reviewer (staff only)
    path("reviewer/projects/", views.reviewer_projects),
    path("reviewer/projects/<int:pk>/", views.reviewer_project_detail),
    path("reviewer/projects/<int:pk>/decision/", views.reviewer_decision),
    path(
        "reviewer/projects/<int:pk>/issue-certificate/",
        views.reviewer_issue_certificate,
    ),
    # Public
    path("certificates/<str:certificate_id>/", views.public_certificate),
]
