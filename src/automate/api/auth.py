import secrets
from functools import wraps

from django.conf import settings
from django.http import JsonResponse


def require_api_key(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Get Key from Header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JsonResponse({"error": "Missing API Key"}, status=401)

        # 2. Validate
        # Ideally stored in DB or settings. For MVP, settings.
        configured_key = getattr(settings, "AUTOMATE_ZAPIER_API_KEY", None)

        if not configured_key or not secrets.compare_digest(api_key, configured_key):
            return JsonResponse({"error": "Invalid API Key"}, status=403)

        return view_func(request, *args, **kwargs)

    return _wrapped_view
