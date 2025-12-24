# Contributing to Django Automate

We love your input! We want to make contributing to this project as easy and transparent as possible.

## Pull Requests

1.  contracts/interfaces must be kept stable.
2.  Tests must pass (`pytest`).
3.  Code must be formatted (`ruff format`).

## Development Setup

```bash
# Clone
git clone ...
cd django_automate

# Install local dev
pip install -e ".[dev]"

# Run tests
pytest
```

## Adding a New Provider

1.  Create `src/automate_modal/providers/your_provider.py`.
2.  Inherit from `ProviderBase`.
3.  Register in `apps.py`.
