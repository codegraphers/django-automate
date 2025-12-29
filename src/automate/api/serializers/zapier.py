"""
Zapier Integration API Serializers.
"""

from rest_framework import serializers


class TriggerSerializer(serializers.Serializer):
    """Serializer for Zapier trigger definitions."""

    key = serializers.CharField()
    label = serializers.CharField()


class SubscribeRequestSerializer(serializers.Serializer):
    """Serializer for Zapier subscribe requests."""

    target_url = serializers.URLField(
        required=True,
        help_text="Callback URL for webhook events"
    )
    event = serializers.CharField(
        required=False,
        help_text="Event type to subscribe to"
    )


class SubscribeResponseSerializer(serializers.Serializer):
    """Serializer for subscribe response."""

    id = serializers.UUIDField()
    status = serializers.CharField()


class UnsubscribeResponseSerializer(serializers.Serializer):
    """Serializer for unsubscribe response."""

    status = serializers.CharField()
