import json
from uuid import uuid4

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .auth import require_api_key


@require_GET
@require_api_key
def list_triggers(request):
    """
    Zapier polls this to see available trigger types.
    """
    triggers = [
        {"key": "new_event", "label": "New Event"},
        {"key": "model_created", "label": "Model Created"},
    ]
    return JsonResponse(triggers, safe=False)


@csrf_exempt
@require_POST
@require_api_key
def subscribe(request):
    """
    Zapier subscribes to a trigger via Webhook.
    REQ: Valid callback URL + API Key.
    P0.5: Validation and Security.
    """
    try:
        data = json.loads(request.body)
        target_url = data.get("target_url")
        # event = data.get("event")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not target_url:
        return JsonResponse({"error": "target_url required"}, status=400)

    # P0.5: Validate Callback URL (SSRF)
    # We use the hardened HttpFetchTool from automate_llm to validate the URL
    from automate_llm.tools.http import HttpFetchTool  # noqa: PLC0415

    validator = HttpFetchTool()
    if not validator._is_safe_url(target_url):
        return JsonResponse({"error": "Invalid Target URL: Blocked by SSRF Policy"}, status=400)

    # P0.5: Unsubscribe Token / ID
    sub_id = str(uuid4())

    # Store subscription (Mock for beta MVP, should use TriggerSpec/Model)

    return JsonResponse({"id": sub_id, "status": "subscribed"})


@csrf_exempt
@require_POST
@require_api_key
def unsubscribe(request):
    # P0.5: Unsubscribe requires integrity (API Key enforced by decorator)
    return JsonResponse({"status": "unsubscribed"})
