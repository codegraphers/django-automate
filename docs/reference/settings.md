# Settings Reference

All configuration is contained in the `DJANGO_AUTOMATE` dictionary in `settings.py`.

## Core Settings

| Path | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ENABLED` | `bool` | `True` | Global master switch. If False, triggers are ignored. |
| `WORKER_MODE` | `str` | `"thread"` | `"thread"`, `"process"`, or `"custom"`. Controls built-in worker behavior. |

## Outbox & Execution

| Path | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `EXECUTION.timeout_seconds` | `int` | `60` | Hard timeout for a single step execution span. |
| `EXECUTION.max_retries` | `int` | `3` | Default retries for transient exceptions. |
| `EXECUTION.batch_size` | `int` | `10` | SQL limit for `claim_batch`. |
| `OUTBOX.lease_seconds` | `int` | `60` | How long a worker owns a job before it expires (for crash recovery). |

> [!NOTE]
> **DB Capability**: On Postgres, `batch_size` uses `SKIP LOCKED` for high concurrency. On SQLite, it locks the table, reducing throughput.

## Governance & Policy

| Path | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `POLICY.allow_ssrf` | `bool` | `False` | Safety gate for HTTP connectors. Blocks private IPs. |
| `POLICY.connector_allowlist` | `list[str]` | `["*"]` | Allowed connector codes. e.g. `["http.post", "slack.*"]`. |
| `POLICY.llm_budget_daily` | `float` | `10.0` | Daily USD cap for LLM usage. |

## Secrets

| Path | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SECRETS.backend` | `str` | `"env"` | Module path to `SecretsBackend`. |
| `SECRETS.prefix` | `str` | `"AUTOMATE_"` | Env var prefix for discovery. |

## Observability

| Path | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `OBSERVABILITY.log_schema` | `str` | `"ecs"` | `"ecs"` (Elastic) or `"simple"`. |
| `OBSERVABILITY.metrics_export` | `bool` | `False` | Expose `/metrics` endpoint (Prometheus). |
