"""
Prompt Evaluation ViewSets.

Class-based ViewSets for prompt testing and metrics.
"""

from django.db import models
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


class PromptTestRequestSerializer(serializers.Serializer):
    """Serializer for prompt test requests."""

    prompt_slug = serializers.SlugField(required=True)
    version = serializers.IntegerField(default=1)
    variables = serializers.DictField(default=dict)


class PromptTestResponseSerializer(serializers.Serializer):
    """Serializer for prompt test response."""

    system_prompt = serializers.CharField()
    user_prompt = serializers.CharField()
    version = serializers.IntegerField()
    status = serializers.CharField()


class PromptMetricsSerializer(serializers.Serializer):
    """Serializer for prompt metrics."""

    daily_stats = serializers.ListField()
    recent_failures = serializers.ListField()


class PromptEvalViewSet(viewsets.ViewSet):
    """
    Prompt Evaluation ViewSet.

    Provides endpoints for testing prompts and viewing metrics.

    Class Attributes:
        template_engine: Jinja2 template engine for rendering
        metrics_days: Number of days for daily stats (default: 30)
        failure_limit: Number of recent failures to show (default: 10)

    Endpoints:
        POST /api/prompts/test/ - Test a prompt with variables
        GET /api/prompts/{slug}/metrics/ - Get prompt metrics

    Example - Custom template rendering:
        class MyPromptEvalViewSet(PromptEvalViewSet):
            def render_template(self, template_str, variables):
                return my_custom_render(template_str, variables)
    """

    authentication_classes = []  # Staff-only via permission check
    permission_classes = []

    metrics_days = 30
    failure_limit = 10

    def check_staff(self, request):
        """Check that user is staff."""
        if not request.user or not request.user.is_staff:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Staff access required')

    def render_template(self, template_str: str, variables: dict) -> str:
        """
        Render a Jinja2 template with variables.

        Override to customize template rendering.
        """
        from jinja2 import Template
        return Template(template_str).render(**variables)

    @extend_schema(
        request=PromptTestRequestSerializer,
        responses=PromptTestResponseSerializer,
        description="Test a prompt by rendering with sample variables."
    )
    @action(detail=False, methods=['post'], url_path='test')
    def test(self, request):
        """
        Test a prompt with sample variables.

        Renders both system and user templates with provided variables.
        """
        self.check_staff(request)

        serializer = PromptTestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        prompt_slug = serializer.validated_data['prompt_slug']
        version_num = serializer.validated_data['version']
        variables = serializer.validated_data['variables']

        from automate.models import Prompt

        try:
            prompt = Prompt.objects.get(slug=prompt_slug)
        except Prompt.DoesNotExist:
            return Response(
                {'error': 'Prompt not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        version = prompt.versions.filter(version=version_num).first()
        if not version:
            return Response(
                {'error': f'Version {version_num} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            system_rendered = self.render_template(version.system_template, variables)
            user_rendered = self.render_template(version.user_template, variables)

            return Response({
                'system_prompt': system_rendered,
                'user_prompt': user_rendered,
                'version': version_num,
                'status': version.status,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        responses=PromptMetricsSerializer,
        description="Get metrics for a specific prompt."
    )
    @action(detail=True, methods=['get'], url_path='metrics')
    def metrics(self, request, pk=None):
        """
        Get detailed metrics for a prompt.

        Returns daily stats and recent failures.
        """
        self.check_staff(request)

        from automate_llm.governance.models import LLMRequest

        prompt_slug = pk

        # Daily breakdown
        daily_stats = list(
            LLMRequest.objects.filter(prompt_slug=prompt_slug)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(
                calls=Count('id'),
                avg_latency=Avg('latency_ms'),
                success_rate=Count('id', filter=models.Q(status='SUCCESS')) * 100.0 / Count('id'),
            )
            .order_by('-date')[:self.metrics_days]
        )

        # Recent failures
        failures = list(
            LLMRequest.objects.filter(prompt_slug=prompt_slug, status='FAILED')
            .order_by('-created_at')[:self.failure_limit]
            .values('id', 'error_message', 'created_at')
        )

        return Response({
            'daily_stats': daily_stats,
            'recent_failures': failures,
        })
