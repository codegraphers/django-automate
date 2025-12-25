from rest_framework import serializers

from automate.models import LLMProvider


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMProvider
        fields = ["slug", "name", "base_url", "api_key_env_var"]
        # Hide sensitive vars if needed, though env var name is usually safe-ish
        # We can treat api_key_env_var as config for now
