from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Generator

from agent_memory_gateway.config import get_settings

logger = logging.getLogger("agent_memory_gateway")

_tracer = None
_otel_initialized = False


def _init_otel() -> None:
    global _tracer, _otel_initialized
    if _otel_initialized:
        return
    _otel_initialized = True

    settings = get_settings()
    if not settings.otel_enabled:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except ImportError:
        logger.warning("OpenTelemetry requested but opentelemetry packages are not installed")
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("agent_memory_gateway")


@contextmanager
def trace_operation(operation: str, **attrs: str) -> Generator[None, None, None]:
    _init_otel()
    start = perf_counter()
    span = None

    if _tracer is not None:
        span = _tracer.start_as_current_span(f"memory.{operation}")
        span.__enter__()
        for key, value in attrs.items():
            span.set_attribute(key, value)

    try:
        yield
    finally:
        elapsed_ms = (perf_counter() - start) * 1000
        if span is not None:
            span.set_attribute("duration_ms", elapsed_ms)
            span.__exit__(None, None, None)
        logger.info(
            "memory.%s duration_ms=%.2f %s",
            operation,
            elapsed_ms,
            " ".join(f"{k}={v}" for k, v in attrs.items()),
        )