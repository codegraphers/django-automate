# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Multi-Modal Gateway (`automate_modal`) with legacy LLM Bridge.
- Audio Providers: OpenAI (TTS/STT).
- Video Pipeline: Secure downloader + STT.
- Admin: Import/Export, JSON Widgets, Autocomplete.
- Workflow: `modal.execute` action.

### Changed
- Refactored project structure to `src` layout.
- **License**: Updated to strict Apache 2.0 compliance (verbatim `LICENSE` text, `NOTICE` file attribution, `pyproject.toml` classifiers).
- **CI**: Configured `ruff` to ignore lazy imports (`PLC0415`) in `admin.py`, `apps.py`, and sub-apps where necessary.

### Fixed
- Critical `ImportError` in `automate.models` by restoring compatibility shims for core models (`Automation`, `Workflow`, etc.), fixing legacy import paths.
- `SyntaxError` in `automate.ingestion.py` caused by malformed docstring.
- Resolved over 300 linting errors including whitespace, unused imports (`F401`), and logic issues (`B904` exception chaining, `F821` undefined names).
- Configured targeted `ruff` ignores for legacy modules (`automate_core`, `step_executors`) to pass CI without risky refactors.
- Fixed `ImportError` in `automate.models` by properly shimming and exporting core models (`Automation`, `Event`, etc.) in `__all__`.
- Removed `.DS_Store` file which caused CI failures.
