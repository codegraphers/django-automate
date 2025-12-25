"""DataChat App Configuration."""

from django.apps import AppConfig


class AutomateDataChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automate_datachat'
    verbose_name = 'Data Chat'

    def ready(self):
        """
        Register all models for DataChat NL2SQL queries.

        To register your own models, add them here or use the decorator::

            from automate_datachat.registry import register_model

            @register_model(tags=["my_app"])
            class MyModel(models.Model):
                ...

        Or register manually::

            from automate_datachat.registry import DataChatRegistry
            DataChatRegistry.register(MyModel, tags=["my_app"])
        """
        self._register_models()

    def _register_models(self):
        """Register all project models in DataChatRegistry."""
        from django.contrib.auth import get_user_model

        from .registry import DataChatRegistry

        # Django Core
        user_model = get_user_model()
        DataChatRegistry.register(user_model, tags=["users", "auth"])

        # automate (Main App)
        from automate.models import (
            BudgetPolicy,
            ConnectionProfile,
            LLMModelConfig,
            LLMProvider,
            MCPServer,
            MCPTool,
            Prompt,
            PromptRelease,
            PromptVersion,
            Template,
        )

        DataChatRegistry.register(LLMProvider, tags=["llm", "providers"])
        DataChatRegistry.register(LLMModelConfig, tags=["llm", "models", "config"])
        DataChatRegistry.register(Prompt, tags=["prompts"])
        DataChatRegistry.register(PromptVersion, tags=["prompts", "versions"])
        DataChatRegistry.register(PromptRelease, tags=["prompts", "releases"])
        DataChatRegistry.register(ConnectionProfile, tags=["connectors", "profiles"])
        DataChatRegistry.register(BudgetPolicy, tags=["governance", "budget"])
        DataChatRegistry.register(Template, tags=["templates"])
        DataChatRegistry.register(MCPServer, tags=["mcp", "integrations"])
        DataChatRegistry.register(MCPTool, tags=["mcp", "tools"])

        # automate_core (Execution Engine)
        from automate_core.models import (
            Artifact,
            Automation,
            Event,
            Execution,
            Job,
            JobEvent,
            OutboxItem,
            Policy,
            RuleSpec,
            SideEffectLog,
            StepRun,
            Trigger,
            Workflow,
        )

        DataChatRegistry.register(Event, tags=["events", "triggers"])
        DataChatRegistry.register(Automation, tags=["automation", "workflows"])
        DataChatRegistry.register(Workflow, tags=["workflows"])
        DataChatRegistry.register(Trigger, tags=["triggers"])
        DataChatRegistry.register(Execution, tags=["execution", "runs"])
        DataChatRegistry.register(StepRun, tags=["execution", "steps"])
        DataChatRegistry.register(SideEffectLog, tags=["execution", "side_effects"])
        DataChatRegistry.register(Artifact, tags=["artifacts", "files"])
        DataChatRegistry.register(Job, tags=["jobs", "queue"])
        DataChatRegistry.register(JobEvent, tags=["jobs", "events"])
        DataChatRegistry.register(OutboxItem, tags=["outbox", "queue"])
        DataChatRegistry.register(Policy, tags=["policies", "governance"])
        DataChatRegistry.register(RuleSpec, tags=["rules", "logic"])

        # automate_governance (Audit & Security)
        from automate_governance.models import AuditLog

        DataChatRegistry.register(AuditLog, tags=["audit", "security", "logs"])

        # automate_llm (LLM Subsystem)
        from automate_llm.governance.models import LLMRequest
        from automate_llm.models import LLMUsage

        DataChatRegistry.register(LLMUsage, tags=["llm", "usage", "costs"])
        DataChatRegistry.register(LLMRequest, tags=["llm", "requests", "messages"])

        # automate_modal (Multi-Modal Gateway)
        from automate_modal.models import (
            ModalArtifact,
            ModalAuditEvent,
            ModalEndpoint,
            ModalJob,
            ModalProviderConfig,
        )

        DataChatRegistry.register(ModalProviderConfig, tags=["modal", "providers"])
        DataChatRegistry.register(ModalEndpoint, tags=["modal", "endpoints"])
        DataChatRegistry.register(ModalJob, tags=["modal", "jobs"])
        DataChatRegistry.register(ModalArtifact, tags=["modal", "artifacts"])
        DataChatRegistry.register(ModalAuditEvent, tags=["modal", "audit"])

        # rag (RAG Knowledge Base)
        from rag.models import EmbeddingModel, KnowledgeSource, RAGEndpoint, RAGQueryLog

        DataChatRegistry.register(KnowledgeSource, tags=["rag", "knowledge"])
        DataChatRegistry.register(RAGEndpoint, tags=["rag", "endpoints"])
        DataChatRegistry.register(EmbeddingModel, tags=["rag", "embeddings"])
        DataChatRegistry.register(RAGQueryLog, tags=["rag", "queries", "logs"])

        # automate_rag (V2 RAG)
        from automate_rag.models import Chunk, Corpus, Document
        from automate_rag.models import KnowledgeSource as RAGKnowledgeSource

        DataChatRegistry.register(Corpus, tags=["rag", "corpus"])
        DataChatRegistry.register(RAGKnowledgeSource, tags=["rag", "sources"])
        DataChatRegistry.register(Document, tags=["rag", "documents"])
        DataChatRegistry.register(Chunk, tags=["rag", "chunks"])

        # automate_connectors
        from automate_connectors.models import ConnectorInstance

        DataChatRegistry.register(ConnectorInstance, tags=["connectors", "instances"])

        # automate_observability
        from automate_observability.models import AuditLogEntry

        DataChatRegistry.register(AuditLogEntry, tags=["observability", "audit"])

        # automate_datachat (Self)
        from .models import ChatEmbed, DataChatMessage, DataChatSession

        DataChatRegistry.register(DataChatSession, tags=["chat", "sessions"])
        DataChatRegistry.register(DataChatMessage, tags=["chat", "messages"])
        DataChatRegistry.register(ChatEmbed, tags=["chat", "embeds"])
