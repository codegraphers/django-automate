from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DataChatSession(models.Model):
    """
    A chat session for a user. One session per user, or one per browser session.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-updated_at"]
    
    def __str__(self):
        return f"Session {self.id} - {self.user or self.session_key}"


class DataChatMessage(models.Model):
    """
    Individual messages in a chat session.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]
    
    session = models.ForeignKey(DataChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # For assistant messages
    sql = models.TextField(blank=True)
    data_json = models.JSONField(null=True, blank=True)
    chart_json = models.JSONField(null=True, blank=True)
    error = models.TextField(blank=True)
    
    # Link to LLM audit log
    llm_request = models.ForeignKey(
        "automate_llm.LLMRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="datachat_messages"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["created_at"]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ============================================================================
# Embeddable Chat Widget
# ============================================================================

import uuid
import secrets


class ChatEmbed(models.Model):
    """
    Configuration for an embeddable chat widget.
    
    Each embed has its own API key, allowed domains, and customization settings.
    Embed code can be generated and placed on external websites.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Display name for this embed config")
    
    # Security
    api_key = models.CharField(
        max_length=64, 
        unique=True, 
        editable=False,
        help_text="API key for authenticating embed requests"
    )
    allowed_domains = models.JSONField(
        default=list,
        help_text='List of allowed domains ["example.com", "*.myapp.io"]'
    )
    
    # Access Control
    require_auth = models.BooleanField(
        default=False,
        help_text="Require user login (redirects to your auth)"
    )
    allowed_tables = models.JSONField(
        default=list,
        blank=True,
        help_text="Restrict to specific tables (empty = all)"
    )
    
    # Rate Limiting
    rate_limit_per_minute = models.IntegerField(
        default=10,
        help_text="Max requests per minute per session"
    )
    max_queries_per_session = models.IntegerField(
        default=100,
        help_text="Max total queries per session"
    )
    
    # Customization
    theme = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"primaryColor": "#2563eb", "title": "Data Assistant"}'
    )
    welcome_message = models.TextField(
        default="Hello! Ask me anything about your data.",
        help_text="Initial message shown in the widget"
    )
    
    # Status
    enabled = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Embed"
        verbose_name_plural = "Chat Embeds"
        ordering = ["-created_at"]
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = f"dce_{secrets.token_urlsafe(32)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        status = "✓" if self.enabled else "✗"
        return f"{status} {self.name}"
    
    def get_embed_code(self, base_url: str = "") -> str:
        """Generate the embed code snippet."""
        return f'''<script src="{base_url}/datachat/embed/v1/{self.id}/widget.js" data-key="{self.api_key}"></script>'''

