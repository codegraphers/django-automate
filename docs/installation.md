# Installation

## Prerequisites
- Python 3.10+
- Django 4.2+ (Testing against 5.0 and 6.0)
- Redis (Optional, for production backoff/throttling)

## Steps

1. **Install Package**:
    ```bash
    pip install django-automate
    ```

## Optional Extras

Install only what you need:

| Extra | Description | Command |
|-------|-------------|---------|
| `llm-openai` | OpenAI provider | `pip install django-automate[llm-openai]` |
| `llm-anthropic` | Anthropic provider | `pip install django-automate[llm-anthropic]` |
| `rag-milvus` | Milvus vector store | `pip install django-automate[rag-milvus]` |
| `rag-pgvector` | PostgreSQL pgvector | `pip install django-automate[rag-pgvector]` |
| `rag-qdrant` | Qdrant vector store | `pip install django-automate[rag-qdrant]` |
| `observability` | OpenTelemetry | `pip install django-automate[observability]` |
| `full` | All providers | `pip install django-automate[full]` |

Combine extras: `pip install django-automate[llm-openai,rag-pgvector]`

2. **Update Settings**:
    Add to `INSTALLED_APPS` in `settings.py`:
    ```python
    INSTALLED_APPS = [
        # ...
        "automate",
        "django_json_widget", # Required for JSON editing in Admin
        "rest_framework",     # Required for API
        "drf_spectacular",    # Required for Swagger
    ]
    ```

3. **URL Configuration**:
    Include URLs in `urls.py`:
    ```python
    from django.urls import path, include
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns = [
        path("admin/", admin.site.urls),
        path("automate/", include("automate.urls")),
        
        # API Documentation
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]
    ```

4. **Migrate**:
    ```bash
    python manage.py migrate
    ```

## Verify
Run the dispatcher loop:
```bash
python manage.py automate_dispatch
```
