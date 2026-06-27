from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryRecord(BaseModel):
    id: str
    tenant_id: str
    agent_id: str
    session_id: str | None = None
    memory_type: MemoryType
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    expires_at: datetime | None = None
    score: float | None = None


class StoreRequest(BaseModel):
    tenant_id: str
    agent_id: str
    session_id: str | None = None
    memory_type: MemoryType = MemoryType.EPISODIC
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    ttl_seconds: int | None = None


class RecallRequest(BaseModel):
    tenant_id: str
    agent_id: str
    query: str
    memory_types: list[MemoryType] | None = None
    session_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class ForgetRequest(BaseModel):
    tenant_id: str
    agent_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    memory_id: str | None = None


class ConsolidateRequest(BaseModel):
    tenant_id: str
    agent_id: str
    session_id: str
    max_tokens: int = Field(default=2000, ge=100, le=32000)


class BudgetRequest(BaseModel):
    tenant_id: str
    agent_id: str
    session_id: str
    context_messages: list[dict[str, str]]
    max_tokens: int = Field(default=8000, ge=500, le=128000)


class BudgetResponse(BaseModel):
    kept_messages: list[dict[str, str]]
    offloaded_count: int
    estimated_tokens: int
    strategy: str