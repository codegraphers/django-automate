from django.apps import AppConfig

class ExampleProjectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'example_project'

    def ready(self):
        # Register models for Data Chat
        try:
            from django.contrib.auth.models import User, Group
            from automate_datachat.registry import DataChatRegistry
            
            # Auth models
            DataChatRegistry.register(
                User, 
                include_fields=["id", "username", "email", "date_joined", "is_staff", "is_active", "last_login"],
                tags=["auth"]
            )
            DataChatRegistry.register(
                Group,
                include_fields=["id", "name"],
                tags=["auth"]
            )
            
            # Automate models
            from automate.models import (
                Automation, LLMProvider, LLMModelConfig, Prompt, PromptVersion,
                Execution, ExecutionStep, Event, ConnectionProfile, BudgetPolicy
            )
            
            DataChatRegistry.register(
                LLMProvider,
                include_fields=["slug", "name", "base_url", "api_key_env_var"],
                tags=["llm", "config"]
            )
            DataChatRegistry.register(
                LLMModelConfig,
                include_fields=["id", "name", "provider_id", "is_default", "max_tokens", "temperature"],
                tags=["llm", "config"]
            )
            DataChatRegistry.register(
                Prompt,
                include_fields=["id", "slug", "name", "description"],
                tags=["llm", "prompts"]
            )
            DataChatRegistry.register(
                PromptVersion,
                include_fields=["id", "prompt_id", "version", "status", "created_at"],
                tags=["llm", "prompts"]
            )
            DataChatRegistry.register(
                Automation,
                include_fields=["id", "name", "slug", "enabled", "environment", "created_at"],
                tags=["automation"]
            )
            DataChatRegistry.register(
                Execution,
                include_fields=["id", "automation_id", "status", "started_at", "finished_at", "duration_ms", "attempts"],
                tags=["automation", "execution"]
            )
            DataChatRegistry.register(
                Event,
                include_fields=["id", "event_type", "source", "status", "created_at"],
                tags=["automation", "events"]
            )
            DataChatRegistry.register(
                BudgetPolicy,
                include_fields=["id", "name", "max_monthly_usd", "enabled"],
                tags=["governance"]
            )
            
            # LLM Request logs
            from automate_llm.governance.models import LLMRequest
            DataChatRegistry.register(
                LLMRequest,
                include_fields=["id", "provider", "model", "prompt_slug", "purpose", "status", "input_tokens", "output_tokens", "latency_ms", "cost_usd", "created_at"],
                tags=["llm", "logs"]
            )
            
            # DataChat models
            from automate_datachat.models import DataChatSession, DataChatMessage
            DataChatRegistry.register(
                DataChatSession,
                include_fields=["id", "user_id", "session_key", "created_at", "updated_at"],
                tags=["datachat"]
            )
            DataChatRegistry.register(
                DataChatMessage,
                include_fields=["id", "session_id", "role", "content", "sql", "created_at", "llm_request_id"],
                tags=["datachat"]
            )
            
        except ImportError as e:
            print(f"DataChat registry error: {e}")
        
        # Seed Data Chat prompts with improved templates
        try:
            from automate.models import Prompt, PromptVersion
            
            # SQL Generator Prompt - IMPROVED
            sql_prompt, created = Prompt.objects.get_or_create(
                slug="datachat_sql_generator",
                defaults={"name": "Data Chat SQL Generator", "description": "Generates SQL from natural language questions"}
            )
            
            # Always update to version 4 with session context support
            version, v_created = PromptVersion.objects.update_or_create(
                prompt=sql_prompt,
                version=4,
                defaults={
                    "status": "approved",
                    "system_template": """You are a helpful data assistant with access to a database and external tools.

=== SESSION CONTEXT ===
{% if context %}
Current User: {{ context.username | default('Anonymous') }}
User ID: {{ context.user_id | default('N/A') }}
Date/Time: {{ context.current_datetime | default('Unknown') }}
Timezone: {{ context.timezone | default('UTC') }}
IP Address: {{ context.ip_address | default('Unknown') }}
{% endif %}

=== YOUR ROLE ===
- Answer general questions conversationally when appropriate
- For data questions, generate SQL to query the database
- For external data (sales, products, orders, etc.), use the available tools
- Be helpful, friendly, and concise

=== DATABASE SCHEMA ===
{{ schema }}

=== EXTERNAL TOOLS ===
{% if tools %}
You have access to these external tools:
{% for tool in tools %}
- {{ tool.name }}: {{ tool.description }}
{% endfor %}

To use a tool, respond with ONLY:
TOOL_CALL: {"tool": "tool_name", "args": {"arg1": "value1"}}
{% else %}
No external tools available.
{% endif %}

=== SQL GENERATION RULES ===
When the user asks about data you can access:
1. Generate ONLY a valid SQLite/PostgreSQL SELECT query
2. Use JOINs when querying related tables (use _id foreign keys)
3. Support GROUP BY, COUNT, SUM, AVG, MIN, MAX for analytics
4. Always include a reasonable LIMIT (max 1000)
5. Output ONLY the SQL - no markdown, no explanation

=== HANDLING REQUESTS ===
- Questions about "me", "who am I", "my info": Use the session context above
- If you can answer from the database: Generate SQL only
- If you should use an external tool: Use TOOL_CALL format
- If you can't access the requested data: Say "I don't have access to that data. I can help you with user information, system settings, and logs."
- For general questions: Answer conversationally
- NEVER list table names or expose internal schema details to users

=== EXAMPLES ===
Q: "Who am I?" → You are {{ context.username }}, logged in from {{ context.ip_address }}
Q: "What time is it?" → It's currently {{ context.current_datetime }} ({{ context.timezone }})
Q: "How many users are there?" → SELECT COUNT(*) FROM auth_user LIMIT 1000
Q: "Show me all products" → TOOL_CALL: {"tool": "listProducts", "args": {}}
Q: "What tables do you have?" → I can help with user data, system settings, and logs. What would you like to know?""",
                    "user_template": """{{ history }}

User: {{ question }}"""
                }
            )
            
            # Summarizer Prompt
            sum_prompt, created = Prompt.objects.get_or_create(
                slug="datachat_summarizer",
                defaults={"name": "Data Chat Summarizer", "description": "Summarizes SQL results in natural language"}
            )
            if created or not sum_prompt.versions.filter(version=2).exists():
                PromptVersion.objects.update_or_create(
                    prompt=sum_prompt,
                    version=2,
                    defaults={
                        "status": "approved",
                        "system_template": "You are a helpful data analyst. Provide clear, concise summaries of query results. If there's an error, explain what went wrong in plain language.",
                        "user_template": """Question: {{ question }}
SQL: {{ sql }}
Results ({{ row_count }} rows): {{ results }}
{% if error %}Error: {{ error }}{% endif %}

Summarize these results conversationally. Be concise but informative."""
                    }
                )
        except Exception as e:
            print(f"Prompt seeding error: {e}")


