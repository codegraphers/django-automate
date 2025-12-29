"""
DataChat API Serializers.

Provides validation and serialization for DataChat API endpoints.

All serializers are designed to be:
- Overridable via inheritance
- Configurable via class attributes
- Well-documented for customization
"""

from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """
    Serializer for chat API requests.
    
    Attributes:
        question: The natural language question to process
        context: Optional additional context for the query
        
    Example:
        serializer = ChatRequestSerializer(data={'question': 'How many users?'})
        serializer.is_valid(raise_exception=True)
    """
    
    question = serializers.CharField(
        required=True,
        min_length=1,
        max_length=2000,
        help_text="Natural language question to ask about your data"
    )
    context = serializers.DictField(
        required=False,
        default=dict,
        help_text="Optional context to include with the query"
    )


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer for chat API responses.
    
    Attributes:
        answer: The natural language response
        sql: The generated SQL query (if applicable)
        data: Query result data
        chart: Chart configuration (if applicable)
        error: Error message (if any)
    """
    
    answer = serializers.CharField(allow_blank=True)
    sql = serializers.CharField(allow_blank=True, required=False)
    data = serializers.ListField(child=serializers.DictField(), required=False)
    chart = serializers.DictField(required=False)
    error = serializers.CharField(allow_blank=True, required=False)


class HistoryMessageSerializer(serializers.Serializer):
    """
    Serializer for chat history messages.
    
    Used for paginated history responses.
    """
    
    id = serializers.IntegerField()
    role = serializers.ChoiceField(choices=['user', 'assistant'])
    content = serializers.CharField()
    sql = serializers.CharField(allow_null=True, required=False)
    data = serializers.JSONField(allow_null=True, required=False)
    chart = serializers.JSONField(allow_null=True, required=False)
    error = serializers.CharField(allow_null=True, required=False)
    created_at = serializers.DateTimeField()


class HistoryResponseSerializer(serializers.Serializer):
    """
    Serializer for paginated chat history response.
    """
    
    messages = HistoryMessageSerializer(many=True)
    has_more = serializers.BooleanField()
    total = serializers.IntegerField()
    page = serializers.IntegerField()


class EmbedChatRequestSerializer(serializers.Serializer):
    """
    Serializer for embedded widget chat requests.
    
    Similar to ChatRequestSerializer but may have different constraints
    for embedded contexts.
    """
    
    question = serializers.CharField(
        required=True,
        min_length=1,
        max_length=1000,  # Shorter limit for embeds
        help_text="Question from embedded widget"
    )


class EmbedChatResponseSerializer(serializers.Serializer):
    """
    Serializer for embedded widget chat responses.
    
    Simplified response format for embedded contexts.
    """
    
    answer = serializers.CharField()
    sql = serializers.CharField(allow_blank=True, required=False)
    error = serializers.CharField(allow_blank=True, required=False)


class EmbedConfigSerializer(serializers.Serializer):
    """
    Serializer for embed configuration responses.
    """
    
    theme = serializers.DictField(required=False)
    welcome_message = serializers.CharField()
    require_auth = serializers.BooleanField()
