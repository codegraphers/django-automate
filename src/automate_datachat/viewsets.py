"""
DataChat API Views.

Class-based ViewSets for DataChat functionality.

All ViewSets are designed to be:
- Configurable via class attributes
- Overridable via inheritance
- Extensible with custom mixins

Example - Custom Chat ViewSet:
    from automate_datachat.viewsets import ChatViewSet

    class MyChatViewSet(ChatViewSet):
        # Override orchestrator class
        orchestrator_class = MyCustomOrchestrator

        # Override pagination
        history_page_size = 25
"""

from django.core.paginator import Paginator
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from automate_api.v1.base import CORSMixin, StaffOnlyMixin

from .models import ChatEmbed, DataChatMessage, DataChatSession
from .permissions import (
    EmbedAPIKeyPermission,
    EmbedOriginPermission,
    EmbedRateLimitPermission,
    IsStaffMember,
)
from .runtime import ChatOrchestrator
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    EmbedChatRequestSerializer,
    EmbedChatResponseSerializer,
    EmbedConfigSerializer,
    HistoryResponseSerializer,
)


class ChatViewSet(StaffOnlyMixin, viewsets.ViewSet):
    """
    Admin DataChat API ViewSet.

    Provides natural language query interface for admin users.

    Class Attributes:
        orchestrator_class: Chat orchestrator to use (default: ChatOrchestrator)
        history_page_size: Messages per history page (default: 15)

    Endpoints:
        POST /datachat/chat/ - Send a chat message
        GET /datachat/history/ - Get chat history

    Configuration via settings:
        AUTOMATE_DATACHAT = {
            'HISTORY_PAGE_SIZE': 20,
        }

    Example - Override orchestrator:
        class MyChatViewSet(ChatViewSet):
            orchestrator_class = MyOrchestrator
    """

    permission_classes = [IsStaffMember]
    orchestrator_class = ChatOrchestrator
    history_page_size = 15

    def get_orchestrator_class(self):
        """Get orchestrator class. Override to customize."""
        return self.orchestrator_class

    def get_history_page_size(self):
        """Get history page size. Override to customize."""
        from django.conf import settings
        datachat_settings = getattr(settings, 'AUTOMATE_DATACHAT', {})
        return datachat_settings.get('HISTORY_PAGE_SIZE', self.history_page_size)

    @extend_schema(
        request=ChatRequestSerializer,
        responses=ChatResponseSerializer,
        description="Send a natural language question about your data."
    )
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """
        Process a chat message.

        Returns natural language response with optional SQL and data.
        """
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator_class = self.get_orchestrator_class()
        orchestrator = orchestrator_class(request)
        result = orchestrator.chat(serializer.validated_data['question'])

        return Response(result)

    @extend_schema(
        responses=HistoryResponseSerializer,
        description="Get paginated chat history for current user."
    )
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        Get chat history for current user.

        Query params:
            page: Page number (default: 1)
            limit: Messages per page (default: 15)
        """
        # Get or create session
        if request.user.is_authenticated:
            session = DataChatSession.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key or ""
            session = DataChatSession.objects.filter(session_key=session_key).first()

        if not session:
            return Response({
                'messages': [],
                'has_more': False,
                'total': 0,
                'page': 1
            })

        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', self.get_history_page_size()))

        all_messages = DataChatMessage.objects.filter(session=session).order_by('-created_at')
        paginator = Paginator(all_messages, limit)
        page_obj = paginator.get_page(page)

        messages = []
        for msg in reversed(page_obj.object_list):
            messages.append({
                'id': msg.id,
                'role': msg.role,
                'content': msg.content,
                'sql': msg.sql if msg.role == 'assistant' else None,
                'data': msg.data_json if msg.role == 'assistant' else None,
                'chart': msg.chart_json if msg.role == 'assistant' else None,
                'error': msg.error if msg.role == 'assistant' else None,
                'created_at': msg.created_at.isoformat(),
            })

        return Response({
            'messages': messages,
            'has_more': page_obj.has_next(),
            'total': paginator.count,
            'page': page,
        })


class EmbedViewSet(CORSMixin, viewsets.ViewSet):
    """
    Embeddable Widget API ViewSet.

    Provides endpoints for embedding DataChat in external websites.

    Class Attributes:
        embed_model: Model class for embed configuration
        widget_template: Template for widget JS (override for customization)

    Endpoints:
        GET /datachat/embed/{id}/widget.js - Get widget JavaScript
        POST /datachat/embed/{id}/chat/ - Process chat message
        GET /datachat/embed/{id}/config/ - Get embed configuration

    Security:
        - API key validation via EmbedAPIKeyPermission
        - Origin validation via EmbedOriginPermission
        - Rate limiting via EmbedRateLimitPermission

    Example - Custom widget template:
        class MyEmbedViewSet(EmbedViewSet):
            def get_widget_template(self, embed):
                return 'datachat/custom_widget.js'
    """

    authentication_classes = []  # Public endpoints
    permission_classes = []  # Permissions handled per-action
    embed_model = ChatEmbed
    embed = None  # Set by dispatch

    def get_embed(self, embed_id):
        """Get embed instance. Override to customize lookup."""
        try:
            return self.embed_model.objects.get(id=embed_id, enabled=True)
        except self.embed_model.DoesNotExist:
            return None

    def dispatch(self, request, *args, **kwargs):
        """Load embed before dispatching."""
        embed_id = kwargs.get('pk') or kwargs.get('embed_id')
        if embed_id:
            self.embed = self.get_embed(embed_id)
        return super().dispatch(request, *args, **kwargs)

    @action(detail=True, methods=['get'], url_path='widget.js')
    def widget_js(self, request, pk=None):
        """
        Get widget JavaScript code.

        Returns JavaScript that creates the chat widget on the page.
        """
        if not self.embed:
            response = HttpResponse(
                "// Embed not found",
                content_type="application/javascript",
                status=404
            )
            return self.add_cors_headers(response)

        base_url = request.build_absolute_uri('/').rstrip('/')
        theme = self.embed.theme or {}
        primary_color = theme.get('primaryColor', '#2563eb')
        title = theme.get('title', 'Data Assistant')

        js_code = self._get_widget_js(self.embed, base_url, primary_color, title)

        response = HttpResponse(js_code, content_type="application/javascript")
        return self.add_cors_headers(response)

    def _get_widget_js(self, embed, base_url, primary_color, title):
        """Generate widget JavaScript. Override to customize."""
        return f'''
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
            const resp = await fetch(`${{BASE_URL}}/datachat/embed/${{EMBED_ID}}/chat/`, {{
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

    @extend_schema(
        request=EmbedChatRequestSerializer,
        responses=EmbedChatResponseSerializer,
        description="Process chat message from embedded widget."
    )
    @action(
        detail=True,
        methods=['post', 'options'],
        permission_classes=[EmbedAPIKeyPermission, EmbedOriginPermission, EmbedRateLimitPermission]
    )
    def chat(self, request, pk=None):
        """
        Process chat message from embedded widget.

        Validates API key, origin, and rate limit before processing.
        """
        if request.method == 'OPTIONS':
            return self.options(request)

        if not self.embed:
            return Response({'error': 'Embed not found'}, status=404)

        serializer = EmbedChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        orchestrator = ChatOrchestrator()
        result = orchestrator.chat(serializer.validated_data['question'])

        response_data = {
            'answer': result.get('answer', ''),
            'sql': result.get('sql', '') if not self.embed.allowed_tables else '',
            'error': result.get('error'),
        }

        return Response(response_data)

    @extend_schema(
        responses=EmbedConfigSerializer,
        description="Get embed configuration."
    )
    @action(detail=True, methods=['get'])
    def config(self, request, pk=None):
        """Get embed configuration."""
        if not self.embed:
            return Response({'error': 'Not found'}, status=404)

        return Response({
            'theme': self.embed.theme,
            'welcome_message': self.embed.welcome_message,
            'require_auth': self.embed.require_auth,
        })
