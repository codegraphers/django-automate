from contextlib import contextmanager
from functools import wraps

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None

@contextmanager
def trace_span(name: str, attributes: dict = None):
    if not OTEL_AVAILABLE:
        yield None
        return

    tracer = trace.get_tracer("django-automate")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            span.set_attributes(attributes)
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

def traced(name: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with trace_span(span_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
