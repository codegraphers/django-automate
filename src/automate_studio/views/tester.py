import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View


@method_decorator(staff_member_required, name="dispatch")
class RuleTesterView(View):
    def get(self, request):
        # Default/Example Data
        example_event = {"type": "order.created", "source": "shopify", "payload": {"amount": 150.00, "currency": "USD"}}

        example_rule = {
            "conditions": {"and": [{"==": [{"var": "type"}, "order.created"]}, {">": [{"var": "payload.amount"}, 100]}]}
        }

        return render(
            request,
            "admin/automate/studio/tester.html",
            {
                "title": "Rule Tester",
                "event_json": json.dumps(example_event, indent=2),
                "rule_json": json.dumps(example_rule, indent=2),
            },
        )

    def post(self, request):
        # Input: { "event": {...}, "rule_spec": {...} }
        # Output: { "match": bool, "explain": [tree] }
        try:
            data = json.loads(request.body)
            data.get("event", {})
            data.get("rule_spec", {})

            # Simple simulation for MVP
            # Real impl would import RuleEngine from automate_core.rules.engine

            match = True  # Mock result

            return JsonResponse(
                {
                    "match": match,
                    "explain": [
                        {"node": "type == 'order.created'", "result": True, "details": "Matches 'order.created'"},
                        {"node": "payload.amount > 100", "result": True, "details": "Value 299.00 > 100"},
                        {
                            "node": "payload.customer.tier in ['vip', 'gold']",
                            "result": True,
                            "details": "Found 'vip' in list",
                        },
                    ],
                }
            )
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
