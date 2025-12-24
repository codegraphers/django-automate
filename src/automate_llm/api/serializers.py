from rest_framework import serializers

class JsonObjectField(serializers.JSONField):
    pass

class LlmRunCreateSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["sync", "async"], default="async")
    provider_profile = serializers.CharField(required=False, default="llm:default")
    prompt_key = serializers.CharField(required=False)
    prompt_version = serializers.CharField(required=False)
    inputs = JsonObjectField(required=False)
    raw_messages = JsonObjectField(required=False)
    policy_overrides = JsonObjectField(required=False, default=dict)
    trace_id = serializers.CharField(required=False, allow_null=True)

    def validate(self, attrs):
        has_prompt = attrs.get("prompt_key") and attrs.get("prompt_version")
        has_raw = attrs.get("raw_messages") is not None
        if not (has_prompt or has_raw):
            raise serializers.ValidationError("Provide prompt_key+prompt_version or raw_messages")
        return attrs
