# Django Automate

<div align="center">

[![CI](https://github.com/codegraphers/django-automate/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/codegraphers/django-automate/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/codegraphers/django-automate.svg)](https://github.com/codegraphers/django-automate/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://pypi.org/project/django-automate/)
[![Ruff](https://img.shields.io/badge/lint-ruff-2b9348.svg)](https://github.com/astral-sh/ruff)
<!-- [![PyPI](https://img.shields.io/pypi/v/django-automate.svg)](https://pypi.org/project/django-automate/) -->
<!-- [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-automate.svg)](https://pypi.org/project/django-automate/) -->

**A secure, extensible automation + multimodal model gateway for Django.**

[Documentation](docs/) • [Quickstart](#quickstart) • [Examples](examples/) • [Contributing](CONTRIBUTING.md) • [Releasing](docs/deployment/pypi_setup.md)

</div>

---

**Django Automate** turns your Django project into a production-grade AI platform. It provides a unified gateway for LLMs, Audio, and Video models, backed by a robust automation engine.

## 🚀 Features

*   **Multi-Modal Gateway**: Unified API for Text (GPT-4), Audio (TTS/Whisper), and Image/Video.
*   **Automation Engine**: Workflow orchestration with Celery/Redis backing.
*   **Enterprise Security**: SecretRef-only credentials, SSRF protection, RBAC, and Audit Logs.
*   **Admin-First**: Manage providers, test capabilities, and view job logs directly in Django Admin.

## ⚡ Quickstart

1.  **Install**:
    ```bash
    pip install django-automate[celery]
    ```

2.  **Try the Standalone Script**:
    ```bash
    python examples/scripts/quickstart.py
    ```

3.  **Run the Full Demo (Docker)**:
    ```bash
    cd examples/docker
    docker-compose up --build
    ```

## 📦 What's Included

| Package | Description |
| ------- | ----------- |
| `automate_modal` | **Core Gateway**. Providers, Jobs, Artifacts. |
| `automate_llm` | **Legacy Support**. Bridge to existing text-only pipelines. |
| `rag` | **RAG Subsystem**. Documents, Embeddings, Vector Store management. |
| `automate_governance` | **Policy Engine**. RBAC, Secrets, Redaction. |

## 📦 Project Structure

```
├── src/                    # Source code (all packages)
│   ├── automate/           # Core app & signals
│   ├── automate_modal/     # Multi-Modal Gateway
│   ├── automate_llm/       # Legacy LLM support
│   └── ...
├── examples/
│   ├── demo_app/           # Full Django reference project
│   ├── scripts/            # Standalone runnable scripts
│   └── docker/             # Production Docker stack
├── tests/                  # Pytest suite
├── docs/                   # Documentation (MkDocs)
└── .github/workflows/      # CI/CD Pipelines
```

## 🔧 Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Description |
| -------- | ----------- |
| `OPENAI_API_KEY` | Needed for OpenAI providers. |
| `CELERY_BROKER_URL` | Redis URL for async tasks. |
| `POSTGRES_*` | Database credentials (if using docker). |

## 📚 Documentation

Full documentation is available in the `docs/` directory.
You can browse it locally:

```bash
pip install mkdocs-material
mkdocs serve
```

It is also hosted on [GitHub Pages](https://example.com).

## 🤝 Contributing

We welcome contributions! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
