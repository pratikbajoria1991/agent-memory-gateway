from __future__ import annotations

from typing import Any

from agent_memory_gateway.models import MemoryType, RecallRequest, StoreRequest
from agent_memory_gateway.service import MemoryGateway


class LlamaIndexMemoryAdapter:
    """Memory store adapter for LlamaIndex-style chat/session workflows."""

    def __init__(
        self,
        gateway: MemoryGateway,
        tenant_id: str,
        agent_id: str,
        session_id: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
    ) -> None:
        self.gateway = gateway
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.memory_type = memory_type

    def put(self, message: dict[str, str]) -> None:
        role = message.get("role", "user")
        content = message.get("content", "")
        self.gateway.store(
            StoreRequest(
                tenant_id=self.tenant_id,
                agent_id=self.agent_id,
                session_id=self.session_id,
                memory_type=self.memory_type,
                content=f"{role}: {content}",
                metadata={"framework": "llamaindex", "role": role},
            )
        )

    def get(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        hits = self.gateway.recall(
            RecallRequest(
                tenant_id=self.tenant_id,
                agent_id=self.agent_id,
                query=query,
                session_id=self.session_id,
                limit=limit,
            )
        )
        return [
            {
                "id": hit.id,
                "content": hit.content,
                "score": hit.score,
                "memory_type": hit.memory_type.value,
            }
            for hit in hits
        ]

    def get_all(self) -> list[dict[str, Any]]:
        records = self.gateway.memory_store.list_session(
            self.tenant_id, self.agent_id, self.session_id
        )
        return [{"id": r.id, "content": r.content} for r in records]

    def reset(self) -> None:
        from agent_memory_gateway.models import ForgetRequest

        self.gateway.forget(
            ForgetRequest(
                tenant_id=self.tenant_id,
                agent_id=self.agent_id,
                session_id=self.session_id,
            )
        )


def as_llamaindex_memory(
    gateway: MemoryGateway,
    tenant_id: str,
    agent_id: str,
    session_id: str,
) -> LlamaIndexMemoryAdapter:
    return LlamaIndexMemoryAdapter(gateway, tenant_id, agent_id, session_id)