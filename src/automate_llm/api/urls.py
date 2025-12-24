from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EvalDatasetViewSet, EvalRunViewSet, PromptViewSet, RunViewSet

router = DefaultRouter()
router.register(r"llm/prompts", PromptViewSet, basename="llm-prompts")
router.register(r"llm/runs", RunViewSet, basename="llm-runs")
router.register(r"llm/evals/datasets", EvalDatasetViewSet, basename="llm-eval-datasets")
router.register(r"llm/evals/runs", EvalRunViewSet, basename="llm-eval-runs")

urlpatterns = [
    path("", include(router.urls)),
]
