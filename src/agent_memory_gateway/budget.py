from __future__ import annotations

from agent_memory_gateway.models import BudgetRequest, BudgetResponse
from agent_memory_gateway.store import MemoryStore, new_record
from agent_memory_gateway.models import MemoryType


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def apply_context_budget(req: BudgetRequest, store: MemoryStore) -> BudgetResponse:
    """Offload oldest messages into episodic memory when over token budget."""
    kept: list[dict[str, str]] = []
    offloaded: list[dict[str, str]] = []
    running = 0

    for msg in reversed(req.context_messages):
        tokens = estimate_tokens(msg.get("content", ""))
        if running + tokens <= req.max_tokens:
            kept.insert(0, msg)
            running += tokens
        else:
            offloaded.insert(0, msg)

    for msg in offloaded:
        store.store(
            new_record(
                tenant_id=req.tenant_id,
                agent_id=req.agent_id,
                session_id=req.session_id,
                memory_type=MemoryType.EPISODIC,
                content=msg.get("content", ""),
                metadata={"role": msg.get("role", "unknown"), "offloaded": True},
            )
        )

    return BudgetResponse(
        kept_messages=kept,
        offloaded_count=len(offloaded),
        estimated_tokens=running,
        strategy="fifo_offload_to_episodic",
    )