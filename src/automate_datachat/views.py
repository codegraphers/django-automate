import json

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .runtime import ChatOrchestrator


@csrf_exempt
@staff_member_required
def chat_api(request):
    """
    API endpoint for the Admin Chat Widget.
    POST: { "question": "..." }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        question = data.get("question")
        if not question:
             return JsonResponse({"error": "No question provided"}, status=400)

        orchestrator = ChatOrchestrator(request)
        result = orchestrator.chat(question)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@staff_member_required
def history_api(request):
    """
    GET /admin/datachat/history/?page=1&limit=15
    Returns paginated chat history for the current user.
    """
    from .models import DataChatMessage, DataChatSession

    # Get or create session for current user
    if request.user.is_authenticated:
        session = DataChatSession.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key or ""
        session = DataChatSession.objects.filter(session_key=session_key).first()

    if not session:
        return JsonResponse({"messages": [], "has_more": False, "total": 0})

    # Paginate messages (newest first for loading, will reverse on client)
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 15))

    all_messages = DataChatMessage.objects.filter(session=session).order_by("-created_at")
    paginator = Paginator(all_messages, limit)
    page_obj = paginator.get_page(page)

    messages = []
    for msg in reversed(page_obj.object_list):
        messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "sql": msg.sql if msg.role == "assistant" else None,
            "data": msg.data_json if msg.role == "assistant" else None,
            "chart": msg.chart_json if msg.role == "assistant" else None,
            "error": msg.error if msg.role == "assistant" else None,
            "created_at": msg.created_at.isoformat(),
        })

    return JsonResponse({
        "messages": messages,
        "has_more": page_obj.has_next(),
        "total": paginator.count,
        "page": page,
    })


# ============================================================================
# Embeddable Widget API
# ============================================================================

import fnmatch

from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt


def validate_embed_origin(request, embed):
    """Check if request Origin/Referer is in allowed_domains."""
    origin = request.headers.get("Origin") or request.headers.get("Referer", "")

    if not origin:
        return False

    # Handle "null" origin (file:// URLs) - check if "null" is in allowed domains
    if origin == "null":
        return "null" in embed.allowed_domains or "*" in embed.allowed_domains

    # Extract components from origin
    from urllib.parse import urlparse
    parsed = urlparse(origin)

    # Get full netloc (host:port) and just host
    netloc = parsed.netloc  # e.g., "localhost:8002"
    host = netloc.split(":")[0]  # e.g., "localhost"

    for pattern in embed.allowed_domains:
        # Support wildcard for all domains
        if pattern == "*":
            return True
        # Check full origin including protocol (http://localhost:8002)
        if fnmatch.fnmatch(origin, pattern):
            return True
        # Check netloc with port (localhost:8002)
        if fnmatch.fnmatch(netloc, pattern):
            return True
        # Check just hostname (localhost)
        if fnmatch.fnmatch(host, pattern):
            return True

    return False


def validate_embed_api_key(request, embed):
    """Check X-Embed-Key header matches."""
    key = request.headers.get("X-Embed-Key") or request.GET.get("key")
    return key == embed.api_key


def check_rate_limit(embed, session_key):
    """Rate limiting per embed per session."""
    cache_key = f"embed_rate:{embed.id}:{session_key}"
    count = cache.get(cache_key, 0)

    if count >= embed.rate_limit_per_minute:
        return False

    cache.set(cache_key, count + 1, 60)  # 60 second window
    return True


@xframe_options_exempt
def embed_widget_js(request, embed_id):
    """
    GET /embed/v1/<embed_id>/widget.js
    Returns the widget JavaScript code.
    """
    from .models import ChatEmbed

    try:
        embed = ChatEmbed.objects.get(id=embed_id, enabled=True)
    except ChatEmbed.DoesNotExist:
        response = HttpResponse("// Embed not found", content_type="application/javascript", status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Get base URL for API calls
    base_url = request.build_absolute_uri("/").rstrip("/")

    theme = embed.theme or {}
    primary_color = theme.get("primaryColor", "#2563eb")
    title = theme.get("title", "Data Assistant")

    js_code = f'''
(function() {{
    const EMBED_ID = "{embed.id}";
    const API_KEY = document.currentScript.getAttribute("data-key");
    const BASE_URL = "{base_url}";
    const THEME = {{
        primary: "{primary_color}",
        title: "{title}"
    }};
    
    // Create styles
    const style = document.createElement("style");
    style.textContent = `
        #datachat-embed-fab {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 56px;
            height: 56px;
            background: ${{THEME.primary}};
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 99999;
        }}
        #datachat-embed-window {{
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 380px;
            height: 500px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            z-index: 99998;
            overflow: hidden;
        }}
        #datachat-embed-header {{
            background: ${{THEME.primary}};
            color: white;
            padding: 16px;
            font-weight: 600;
        }}
        #datachat-embed-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }}
        #datachat-embed-input-area {{
            display: flex;
            gap: 8px;
            padding: 12px;
            border-top: 1px solid #e5e7eb;
        }}
        #datachat-embed-input {{
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 20px;
            outline: none;
        }}
        #datachat-embed-send {{
            background: ${{THEME.primary}};
            color: white;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
        }}
        .embed-msg {{
            margin-bottom: 12px;
            padding: 10px 14px;
            border-radius: 12px;
            max-width: 85%;
        }}
        .embed-msg-user {{ background: #e0e7ff; margin-left: auto; }}
        .embed-msg-bot {{ background: #f3f4f6; }}
    `;
    document.head.appendChild(style);
    
    // Create widget
    const fab = document.createElement("div");
    fab.id = "datachat-embed-fab";
    fab.innerHTML = "💬";
    document.body.appendChild(fab);
    
    const win = document.createElement("div");
    win.id = "datachat-embed-window";
    win.innerHTML = `
        <div id="datachat-embed-header">${{THEME.title}}</div>
        <div id="datachat-embed-messages">
            <div class="embed-msg embed-msg-bot">{embed.welcome_message}</div>
        </div>
        <div id="datachat-embed-input-area">
            <input type="text" id="datachat-embed-input" placeholder="Ask a question...">
            <button id="datachat-embed-send">Send</button>
        </div>
    `;
    document.body.appendChild(win);
    
    // Toggle
    fab.addEventListener("click", () => {{
        win.style.display = win.style.display === "none" ? "flex" : "none";
    }});
    
    // Send message
    async function sendMessage() {{
        const input = document.getElementById("datachat-embed-input");
        const msgs = document.getElementById("datachat-embed-messages");
        const q = input.value.trim();
        if (!q) return;
        
        input.value = "";
        msgs.innerHTML += `<div class="embed-msg embed-msg-user">${{q}}</div>`;
        msgs.innerHTML += `<div class="embed-msg embed-msg-bot" id="loading">...</div>`;
        msgs.scrollTop = msgs.scrollHeight;
        
        try {{
            const resp = await fetch(`${{BASE_URL}}/datachat/embed/v1/${{EMBED_ID}}/chat`, {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "X-Embed-Key": API_KEY
                }},
                body: JSON.stringify({{ question: q }})
            }});
            const data = await resp.json();
            document.getElementById("loading").remove();
            
            if (data.error) {{
                msgs.innerHTML += `<div class="embed-msg embed-msg-bot">Error: ${{data.error}}</div>`;
            }} else {{
                msgs.innerHTML += `<div class="embed-msg embed-msg-bot">${{data.answer}}</div>`;
            }}
            msgs.scrollTop = msgs.scrollHeight;
        }} catch (err) {{
            document.getElementById("loading").remove();
            msgs.innerHTML += `<div class="embed-msg embed-msg-bot">Connection error</div>`;
        }}
    }}
    
    document.getElementById("datachat-embed-send").addEventListener("click", sendMessage);
    document.getElementById("datachat-embed-input").addEventListener("keypress", (e) => {{
        if (e.key === "Enter") sendMessage();
    }});
}})();
'''

    response = HttpResponse(js_code, content_type="application/javascript")
    response["Access-Control-Allow-Origin"] = "*"
    return response


@csrf_exempt
def embed_chat_api(request, embed_id):
    """
    POST /embed/v1/<embed_id>/chat
    Chat API for embedded widgets.
    """
    from .models import ChatEmbed

    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-Embed-Key, X-Session-Id"
        return response

    if request.method != "POST":
        response = JsonResponse({"error": "POST required"}, status=405)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    try:
        embed = ChatEmbed.objects.get(id=embed_id, enabled=True)
    except ChatEmbed.DoesNotExist:
        response = JsonResponse({"error": "Embed not found"}, status=404)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Validate origin
    if embed.allowed_domains and not validate_embed_origin(request, embed):
        response = JsonResponse({"error": "Domain not allowed"}, status=403)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Validate API key
    if not validate_embed_api_key(request, embed):
        response = JsonResponse({"error": "Invalid API key"}, status=401)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Rate limiting
    session_key = request.headers.get("X-Session-Id") or request.META.get("REMOTE_ADDR", "unknown")
    if not check_rate_limit(embed, session_key):
        response = JsonResponse({"error": "Rate limit exceeded"}, status=429)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    # Process chat (reuse existing orchestrator)
    try:
        data = json.loads(request.body)
        question = data.get("question")
        if not question:
            response = JsonResponse({"error": "No question provided"}, status=400)
            response["Access-Control-Allow-Origin"] = "*"
            return response

        from .runtime import ChatOrchestrator
        orchestrator = ChatOrchestrator()  # No request = no auth required
        result = orchestrator.chat(question)

        response = JsonResponse({
            "answer": result.get("answer", ""),
            "sql": result.get("sql", "") if not embed.allowed_tables else "",  # Hide SQL if restricted
            "error": result.get("error")
        })
        response["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        response = JsonResponse({"error": str(e)}, status=500)
        response["Access-Control-Allow-Origin"] = "*"
        return response


def embed_config_api(request, embed_id):
    """
    GET /embed/v1/<embed_id>/config
    Returns embed configuration (theme, settings).
    """
    from .models import ChatEmbed

    try:
        embed = ChatEmbed.objects.get(id=embed_id, enabled=True)
    except ChatEmbed.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    return JsonResponse({
        "theme": embed.theme,
        "welcome_message": embed.welcome_message,
        "require_auth": embed.require_auth,
    })


