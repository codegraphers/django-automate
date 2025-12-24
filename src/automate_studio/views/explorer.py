from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse

@method_decorator(staff_member_required, name='dispatch')
class ExecutionExplorerView(View):
    def get(self, request, run_id):
        # todo: Fetch ExecutionRun + AuditLogEntries for this run
        return JsonResponse({
            "run_id": run_id,
            "timeline": [
                {"ts": "2023-01-01T12:00:00Z", "stage": "Trigger", "status": "OK"},
                {"ts": "2023-01-01T12:00:01Z", "stage": "Rules", "status": "OK"},
            ]
        })
