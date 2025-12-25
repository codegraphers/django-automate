from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView

from automate.models import Execution, LLMProvider
from automate_core.jobs.models import Job
from automate_governance.models import AuditLog


# Helper to normalize timestamps for sorting
def get_timestamp(obj):
    if hasattr(obj, "occurred_at"): return obj.occurred_at
    if hasattr(obj, "created_at"): return obj.created_at
    if hasattr(obj, "started_at"): return obj.started_at
    return None

import json
import time


@method_decorator(staff_member_required, name='dispatch')
class TestProviderView(View):
    template_name = "studio/provider_test.html"

    def get(self, request, provider_id):
        provider = get_object_or_404(LLMProvider, pk=provider_id)
        return render(request, self.template_name, {"provider": provider})

    def post(self, request, provider_id):
        provider = get_object_or_404(LLMProvider, pk=provider_id)
        input_text = request.POST.get("input", "Hello world")

        # Simulate check (In real life, call provider backend)
        start = time.time()

        # Mock result for V1
        success = True
        latency_ms = 150
        response_data = {
            "model": "gpt-4",
            "choices": [{"message": {"content": f"Echo: {input_text}"}}]
        }

        context = {
            "success": success,
            "latency_ms": latency_ms,
            "request_preview": json.dumps({"messages": [{"role": "user", "content": input_text}]}, indent=2),
            "response_preview": json.dumps(response_data, indent=2),
            "provider": provider
        }


        # HTMX partial render
        return render(request, "studio/components/test_result.html", context)


@method_decorator(staff_member_required, name='dispatch')
class CorrelationExplorerView(View):
    template_name = "studio/correlation.html"

    def get(self, request):
        query = request.GET.get("q", "").strip()
        results = []

        if query:
            # 1. Search Audit Logs
            audits = list(AuditLog.objects.filter(correlation_id=query))
            for a in audits: a.object_type = "AuditLog"; a.timestamp = a.occurred_at

            # 2. Search Executions
            execs = list(Execution.objects.filter(correlation_id=query))
            for e in execs: e.object_type = "Execution"; e.timestamp = e.started_at

            # 3. Search Jobs
            jobs = list(Job.objects.filter(correlation_id=query))
            for j in jobs: j.object_type = "Job"; j.timestamp = j.created_at

            # 4. Search Events (if payload has correlation_id or trace_id?)
            # Usually events initiate the correlation, so they might not have it unless enriched.
            # We'll check rudimentary matches

            results = audits + execs + jobs
            results.sort(key=lambda x: x.timestamp if x.timestamp else timezone.now())

        return render(request, self.template_name, {"query": query, "results": results})

from django.db.models import Count


@method_decorator(staff_member_required, name='dispatch')
class DashboardView(View):
    template_name = "studio/dashboard.html"

    def get(self, request):
        # 1. Job Queue Stats
        job_stats = Job.objects.values('status').annotate(count=Count('id'))
        jobs_dict = {x['status']: x['count'] for x in job_stats}

        # 2. Execution Stats (Last 24h usually, but simplified for V1)
        exec_stats = Execution.objects.values('status').annotate(count=Count('id'))
        exec_dict = {x['status']: x['count'] for x in exec_stats}

        # 3. Queue Lag (Proxy: count of 'queued' jobs created long ago)
        # Simplified: just showing raw counts

        context = {
            "jobs_stats": jobs_dict,
            "exec_stats": exec_dict,
            "system_health": {"db": "Connected", "queue": "Active"}
        }
        return render(request, self.template_name, context)


@method_decorator(staff_member_required, name='dispatch')
class WizardView(TemplateView):
    template_name = "admin/automate/studio/wizard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Automation Wizard"
        return ctx


@method_decorator(staff_member_required, name='dispatch')
class RuleTesterView(TemplateView):
    template_name = "admin/automate/studio/tester.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Rule Tester"
        return ctx

