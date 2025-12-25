try:
    from prometheus_client import Counter, Gauge, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Dummy classes
    class MetricMock:
        def labels(self, *args, **kwargs): return self
        def inc(self, amount=1): pass
        def observe(self, amount): pass
        def set(self, value): pass

    Counter = Histogram = Gauge = lambda *args, **kwargs: MetricMock()

class MetricsRegistry:
    # HTTP
    http_requests_total = Counter(
        "http_requests_total", "Total HTTP Requests", ["method", "route", "status", "tenant"]
    )
    http_request_duration_seconds = Histogram(
        "http_request_duration_seconds", "HTTP Request Duration", ["method", "route"]
    )

    # Engine
    executions_started_total = Counter(
        "executions_started_total", "Executions Started", ["tenant"]
    )
    executions_completed_total = Counter(
        "executions_completed_total", "Executions Completed", ["tenant", "status"]
    )

    # Provider
    provider_requests_total = Counter(
        "provider_requests_total", "Provider Calls", ["provider", "capability", "status"]
    )
    provider_latency_seconds = Histogram(
        "provider_latency_seconds", "Provider Latency", ["provider", "capability"]
    )

    # LLM Cost
    llm_tokens_total = Counter(
        "llm_tokens_total", "LLM Tokens", ["provider", "model", "tenant", "type"] # type=prompt/completion
    )
    llm_cost_usd_total = Counter(
        "llm_cost_usd_total", "LLM Cost USD", ["provider", "model", "tenant"]
    )

metrics = MetricsRegistry()
