from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "test-key"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "automate_studio",
    "automate_datachat",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "automate",
    "automate_core",

    "automate_governance",
    "automate_llm",
    "automate_modal",
    "rag",
    "automate_rag",
    "automate_connectors",
    "automate_observability",
    "django_json_widget",
    "import_export",
    "rest_framework",
    "drf_spectacular",
    "automate_api",
]

MIDDLEWARE = [
    "automate_api.v1.middleware.CorrelationIdMiddleware",
    "automate_api.v1.middleware_audit.AuditMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
ROOT_URLCONF = "automate.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CELERY_BROKER_URL = "memory://"
CELERY_TASK_ALWAYS_EAGER = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "automate_api.v1.auth.BearerTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "automate_api.v1.permissions.IsAuthenticatedAndTenantScoped",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "automate_api.v1.pagination.CursorPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_CLASSES": [
        "automate_api.v1.throttling.TenantRateThrottle",
        "automate_api.v1.throttling.TokenRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "tenant": "120/min",
        "token": "60/min",
    },
    "EXCEPTION_HANDLER": "automate_api.v1.errors.api_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Django Automate API",
    "DESCRIPTION": "Automation execution, endpoints, jobs, artifacts, and providers.",
    "VERSION": "v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
