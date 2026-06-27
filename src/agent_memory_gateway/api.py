from __future__ import annotations

from fastapi import FastAPI

from agent_memory_gateway.models import (
    BudgetRequest,
    BudgetResponse,
    ConsolidateRequest,
    ForgetRequest,
    MemoryRecord,
    RecallRequest,
    StoreRequest,
)
from agent_memory_gateway import __version__
from agent_memory_gateway.config import get_settings
from agent_memory_gateway.service import MemoryGateway
from agent_memory_gateway.store_factory import create_memory_store

app = FastAPI(
    title="Agent Memory Gateway",
    description="Unified memory API for AI agents",
    version=__version__,
)

_settings = get_settings()
_store = create_memory_store(_settings)
_gateway = MemoryGateway(_store)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "backend": _settings.backend,
        "otel_enabled": str(_settings.otel_enabled).lower(),
    }


@app.post("/v1/memory/store", response_model=MemoryRecord)
def store_memory(req: StoreRequest) -> MemoryRecord:
    return _gateway.store(req)


@app.post("/v1/memory/recall", response_model=list[MemoryRecord])
def recall_memory(req: RecallRequest) -> list[MemoryRecord]:
    return _gateway.recall(req)


@app.post("/v1/memory/forget")
def forget_memory(req: ForgetRequest) -> dict[str, int]:
    return _gateway.forget(req)


@app.post("/v1/memory/consolidate", response_model=MemoryRecord)
def consolidate_memory(req: ConsolidateRequest) -> MemoryRecord:
    return _gateway.consolidate(req)


@app.post("/v1/memory/budget", response_model=BudgetResponse)
def context_budget(req: BudgetRequest) -> BudgetResponse:
    return _gateway.budget(req)