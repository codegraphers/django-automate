# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2025-12-25

### Added
- **DataChat MCP Integration**: Chat now supports calling external MCP tools alongside SQL queries
- **Comprehensive Table Registration**: All 44+ project models registered in DataChatRegistry
- **Customization Guide**: New docs covering admin, developer, and API integration patterns
- **automate_api**: Full REST API v1 with authentication, pagination, and throttling
- **automate_observability**: Structured logging, metrics, and OpenTelemetry tracing
- **automate_rag**: V2 RAG subsystem with Corpus, Document, and Chunk models
- **Provider Architecture**: New provider registry with entrypoint discovery
- **OpenAI Provider**: Production-ready OpenAI chat provider implementation

### Fixed
- MCP tool sync admin action now correctly unpacks 3-tuple return value
- DataChat prompt template includes MCP tool instructions
- Studio template paths corrected to `admin/automate/studio/`
- Admin index.html uses `{% url %}` tags instead of hardcoded paths
- `tests/settings.py` now loads `.env` via `python-dotenv`
- Database changed from `:memory:` to file-based for persistence

### Changed
- `automate_studio` moved to top of INSTALLED_APPS for template precedence
- All Studio views now require `staff_member_required`
- `automate_datachat` re-enabled in INSTALLED_APPS

### Documentation
- Added `guides/customization.md` - comprehensive customization guide
- Updated `features/datachat.md` with registration examples
- Restored full README with architecture diagram and use cases
- Added DataChat table registration docs in apps.py docstring

---

## [1.0.0] - 2025-12-23

### Features
- **Studio**: Visual Automation Wizard, Rule Tester, Execution Explorer
- **Core**: Reliable Outbox worker, Signal/Webhook triggers
- **Governance**: SecretRef system, Audit Logging, Policy Engine
- **LLM**: Gateway with OpenAI/Anthropic support and Jinja2 sandboxing
- **Observability**: Structured logging and Trace ID propagation

### Compatibility
- Django 4.2 / 5.0 / 6.0
- Python 3.10+
