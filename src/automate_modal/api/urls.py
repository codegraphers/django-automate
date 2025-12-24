from django.urls import path

from .views import (
    ArtifactDownloadView,
    EndpointJobView,
    EndpointRunView,
    EndpointStreamView,
    JobEventsView,
    JobStatusView,
)

urlpatterns = [
    # Endpoint execution
    path("endpoints/<slug:slug>/run", EndpointRunView.as_view(), name="modal-run"),
    path("endpoints/<slug:slug>/stream", EndpointStreamView.as_view(), name="modal-stream"),
    path("endpoints/<slug:slug>/jobs", EndpointJobView.as_view(), name="modal-job-submit"),
    # Job management
    path("jobs/<str:job_id>", JobStatusView.as_view(), name="modal-job-status"),
    path("jobs/<str:job_id>/events", JobEventsView.as_view(), name="modal-job-events"),
    # Artifacts
    path("artifacts/<str:artifact_id>/download", ArtifactDownloadView.as_view(), name="modal-artifact-download"),
]
