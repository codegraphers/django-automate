from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("studio/", include("automate_studio.urls")),
    path("datachat/", include("automate_datachat.urls")),  # New module
    path("api/", include("automate.urls")),
    path("api/rag/", include("rag.urls")),  # RAG Retrieval API
    path("api/modal/", include("automate_modal.api.urls")),  # Multi-Modal Gateway API
    # Root API Docs (for convenience)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
