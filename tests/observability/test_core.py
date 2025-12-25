import json
import logging
from io import StringIO

import pytest

from automate_core.providers.base import ProviderContext
from automate_observability.logging import JSONFormatter, configure_logging, get_logger
from automate_observability.metrics import metrics
from automate_observability.tracing import trace_span


def test_json_logging():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())

    ctx = ProviderContext(
        tenant_id="t1", correlation_id="c1", actor_id="u1", purpose="test",
        secrets=None, policy=None, logger=None, now=lambda: None
    )

    logger = get_logger("test_logger", ctx=ctx)
    logger.logger.addHandler(handler)
    logger.logger.setLevel(logging.INFO)

    logger.info("Hello World", extra={"data": {"k": "v"}})

    log_out = stream.getvalue().strip()
    entry = json.loads(log_out)

    assert entry["message"] == "Hello World"
    assert entry["tenant_id"] == "t1"
    assert entry["correlation_id"] == "c1"
    assert entry["data"]["k"] == "v"
    assert entry["service"] == "django-automate"

def test_metrics_usage():
    # Just ensure no exception works
    metrics.http_requests_total.labels(method="GET", route="/", status="200", tenant="t1").inc()
    metrics.llm_tokens_total.labels(provider="openai", model="gpt", tenant="t1", type="prompt").inc(10)

def test_tracing_usage():
    with trace_span("test_span", attributes={"foo": "bar"}):
        pass
