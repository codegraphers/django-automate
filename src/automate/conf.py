"""
Django Automate Configuration.

Centralized configuration system with Django settings integration.

Usage:
    from automate.conf import settings
    
    page_size = settings.PAGINATION_PAGE_SIZE  # With default
    rate_limit = settings.get('RATE_LIMIT', 60)  # With fallback

Configure in Django settings:
    AUTOMATE_API = {
        'PAGINATION_PAGE_SIZE': 50,
        'CORS_ALLOWED_ORIGINS': ['*'],
        'RATE_LIMIT_PER_MINUTE': 120,
    }
    
    AUTOMATE_DATACHAT = {
        'HISTORY_PAGE_SIZE': 20,
        'EMBED_RATE_LIMIT': 60,
    }
"""

from django.conf import settings as django_settings


class AutomateSettings:
    """
    Lazy settings object that reads from Django settings.
    
    Provides dot-notation access to AUTOMATE_* settings with defaults.
    
    Example:
        from automate.conf import automate_settings
        
        # Access with defaults
        page_size = automate_settings.get('PAGINATION_PAGE_SIZE', 50)
        
        # Or via attribute (returns None if not set)
        cors = automate_settings.CORS_ALLOWED_ORIGINS
    """
    
    # Default settings values
    DEFAULTS = {
        # API settings
        'PAGINATION_PAGE_SIZE': 50,
        'RATE_LIMIT_PER_MINUTE': 60,
        'CORS_ALLOWED_ORIGINS': ['*'],
        'CORS_ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        'CORS_ALLOWED_HEADERS': ['Content-Type', 'Authorization', 'X-API-Key', 'X-Embed-Key'],
        
        # Authentication
        'API_KEY_HEADER': 'X-API-Key',
        'BEARER_TOKEN_HEADER': 'Authorization',
        
        # Schema
        'SCHEMA_EXCLUDED_APPS': ['admin', 'contenttypes', 'sessions', 'messages', 'staticfiles'],
        
        # Throttling
        'THROTTLE_RATES': {
            'tenant': '120/min',
            'token': '60/min',
        },
    }
    
    # DataChat settings
    DATACHAT_DEFAULTS = {
        'HISTORY_PAGE_SIZE': 15,
        'EMBED_RATE_LIMIT': 60,
        'EMBED_MAX_MESSAGE_LENGTH': 1000,
    }
    
    # RAG settings
    RAG_DEFAULTS = {
        'DEFAULT_TOP_K': 5,
        'MAX_TOP_K': 100,
        'QUERY_TIMEOUT_SECONDS': 30,
    }
    
    # LLM settings
    LLM_DEFAULTS = {
        'DEFAULT_PROVIDER': 'openai',
        'DEFAULT_MODEL': 'gpt-4',
        'MAX_RETRIES': 3,
        'TIMEOUT_SECONDS': 60,
    }
    
    def __init__(self):
        self._cached_settings = {}
    
    def _get_settings_dict(self, prefix: str) -> dict:
        """Get settings dict for a prefix."""
        attr_name = f'AUTOMATE_{prefix}'
        return getattr(django_settings, attr_name, {})
    
    def get(self, key: str, default=None, prefix: str = 'API'):
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
            prefix: Settings prefix (API, DATACHAT, RAG, LLM)
            
        Returns:
            Setting value or default
        """
        # Check Django settings first
        settings_dict = self._get_settings_dict(prefix)
        if key in settings_dict:
            return settings_dict[key]
        
        # Check defaults
        defaults_attr = f'{prefix}_DEFAULTS' if prefix != 'API' else 'DEFAULTS'
        defaults = getattr(self, defaults_attr, {})
        if key in defaults:
            return defaults[key]
        
        return default
    
    def get_api(self, key: str, default=None):
        """Get API setting."""
        return self.get(key, default, 'API')
    
    def get_datachat(self, key: str, default=None):
        """Get DataChat setting."""
        return self.get(key, default, 'DATACHAT')
    
    def get_rag(self, key: str, default=None):
        """Get RAG setting."""
        return self.get(key, default, 'RAG')
    
    def get_llm(self, key: str, default=None):
        """Get LLM setting."""
        return self.get(key, default, 'LLM')
    
    def __getattr__(self, name: str):
        """Allow dot-notation access to settings."""
        # Try API settings first
        api_settings = self._get_settings_dict('API')
        if name in api_settings:
            return api_settings[name]
        if name in self.DEFAULTS:
            return self.DEFAULTS[name]
        
        raise AttributeError(f"Setting '{name}' not found")


# Global settings instance
automate_settings = AutomateSettings()


# Backward-compatible function
def get_setting(key: str, default=None, prefix: str = 'API'):
    """
    Get a Django Automate setting.
    
    Args:
        key: Setting key
        default: Default value
        prefix: Settings prefix
        
    Returns:
        Setting value or default
    """
    return automate_settings.get(key, default, prefix)
