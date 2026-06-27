from __future__ import annotations

from agent_memory_gateway.budget import apply_context_budget
from agent_memory_gateway.models import (
    BudgetRequest,
    BudgetResponse,
    ConsolidateRequest,
    ForgetRequest,
    MemoryRecord,
    MemoryType,
    RecallRequest,
    StoreRequest,
)
from agent_memory_gateway.store import MemoryStore, new_record
from agent_memory_gateway.telemetry import trace_operation


class MemoryGateway:
    def __init__(self, memory_store: MemoryStore) -> None:
        self.memory_store = memory_store

    def store(self, req: StoreRequest) -> MemoryRecord:
        with trace_operation(
            "store",
            tenant=req.tenant_id,
            agent=req.agent_id,
            type=req.memory_type.value,
        ):
            record = new_record(
                tenant_id=req.tenant_id,
                agent_id=req.agent_id,
                session_id=req.session_id,
                memory_type=req.memory_type,
                content=req.content,
                metadata=req.metadata,
                ttl_seconds=req.ttl_seconds,
            )
            return self.memory_store.store(record)

    def recall(self, req: RecallRequest) -> list[MemoryRecord]:
        with trace_operation("recall", tenant=req.tenant_id, agent=req.agent_id):
            return self.memory_store.recall(
                tenant_id=req.tenant_id,
                agent_id=req.agent_id,
                query=req.query,
                memory_types=req.memory_types,
                session_id=req.session_id,
                limit=req.limit,
            )

    def forget(self, req: ForgetRequest) -> dict[str, int]:
        with trace_operation("forget", tenant=req.tenant_id):
            deleted = self.memory_store.forget(
                tenant_id=req.tenant_id,
                agent_id=req.agent_id,
                session_id=req.session_id,
                user_id=req.user_id,
                memory_id=req.memory_id,
            )
            return {"deleted": deleted}

    def consolidate(self, req: ConsolidateRequest) -> MemoryRecord:
        with trace_operation("consolidate", tenant=req.tenant_id, agent=req.agent_id):
            session_memories = self.memory_store.list_session(
                req.tenant_id, req.agent_id, req.session_id
            )
            combined = "\n".join(m.content for m in session_memories)
            if len(combined) > req.max_tokens * 4:
                combined = combined[: req.max_tokens * 4]

            summary = (
                f"Session summary ({len(session_memories)} memories): {combined[:500]}..."
                if len(combined) > 500
                else f"Session summary: {combined}"
            )

            mem_type = (
                session_memories[0].memory_type
                if session_memories
                else MemoryType.SEMANTIC
            )
            return self.memory_store.store(
                new_record(
                    tenant_id=req.tenant_id,
                    agent_id=req.agent_id,
                    session_id=req.session_id,
                    memory_type=mem_type,
                    content=summary,
                    metadata={"consolidated": True, "source_count": len(session_memories)},
                )
            )

    def budget(self, req: BudgetRequest) -> BudgetResponse:
        with trace_operation("budget", tenant=req.tenant_id, agent=req.agent_id):
            return apply_context_budget(req, self.memory_store)