import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(staff_member_required, name="dispatch")
class PromptEvalView(TemplateView):
    """
    Prompt Evaluation View - Test prompts, compare versions, view performance metrics.
    """

    template_name = "admin/automate/prompt_eval.html"

    def get_context_data(self, **kwargs):
        from automate.models import Prompt
        from automate_llm.governance.models import LLMRequest

        context = super().get_context_data(**kwargs)

        # Get all prompts with their versions
        prompts = list(Prompt.objects.prefetch_related("versions").all())

        # Get performance metrics by prompt_slug
        metrics = (
            LLMRequest.objects.filter(status="SUCCESS")
            .values("prompt_slug")
            .annotate(
                total_calls=Count("id"),
                avg_latency=Avg("latency_ms"),
                total_input_tokens=Sum("input_tokens"),
                total_output_tokens=Sum("output_tokens"),
                avg_input_tokens=Avg("input_tokens"),
                avg_output_tokens=Avg("output_tokens"),
            )
        )

        # Convert to dict for easy lookup
        metrics_by_slug = {m["prompt_slug"]: m for m in metrics}

        # Attach metrics directly to each prompt object
        for prompt in prompts:
            prompt.metrics = metrics_by_slug.get(prompt.slug, {})

        # Recent requests for debugging
        recent_requests = LLMRequest.objects.order_by("-created_at")[:20]

        context.update(
            {
                "prompts": prompts,
                "recent_requests": recent_requests,
            }
        )

        return context


@staff_member_required
def prompt_test_api(request):
    """
    POST /admin/prompt-eval/test/
    Test a prompt with sample input variables.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        from jinja2 import Template

        from automate.models import Prompt

        data = json.loads(request.body)
        prompt_slug = data.get("prompt_slug")
        version_num = data.get("version", 1)
        variables = data.get("variables", {})

        prompt = Prompt.objects.get(slug=prompt_slug)
        version = prompt.versions.filter(version=version_num).first()

        if not version:
            return JsonResponse({"error": f"Version {version_num} not found"}, status=404)

        # Render the templates
        system_rendered = Template(version.system_template).render(**variables)
        user_rendered = Template(version.user_template).render(**variables)

        return JsonResponse(
            {
                "system_prompt": system_rendered,
                "user_prompt": user_rendered,
                "version": version_num,
                "status": version.status,
            }
        )

    except Prompt.DoesNotExist:
        return JsonResponse({"error": "Prompt not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def prompt_metrics_api(request, prompt_slug):
    """
    GET /admin/prompt-eval/metrics/<prompt_slug>/
    Get detailed metrics for a specific prompt.
    """
    from django.db.models import Avg, Count

    from automate_llm.governance.models import LLMRequest

    # Daily breakdown
    daily_stats = (
        LLMRequest.objects.filter(prompt_slug=prompt_slug)
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(
            calls=Count("id"),
            avg_latency=Avg("latency_ms"),
            success_rate=Count("id", filter=models.Q(status="SUCCESS")) * 100.0 / Count("id"),
        )
        .order_by("-date")[:30]
    )

    # Recent failures for debugging
    failures = (
        LLMRequest.objects.filter(prompt_slug=prompt_slug, status="FAILED")
        .order_by("-created_at")[:10]
        .values("id", "error_message", "created_at")
    )

    return JsonResponse(
        {
            "daily_stats": list(daily_stats),
            "recent_failures": list(failures),
        }
    )
