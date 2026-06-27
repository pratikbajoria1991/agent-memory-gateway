from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Generator

logger = logging.getLogger("agent_memory_gateway")


@contextmanager
def trace_operation(operation: str, **attrs: str) -> Generator[None, None, None]:
    start = perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info(
            "memory.%s duration_ms=%.2f %s",
            operation,
            elapsed_ms,
            " ".join(f"{k}={v}" for k, v in attrs.items()),
        )