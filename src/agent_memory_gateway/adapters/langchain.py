from __future__ import annotations

from typing import Any

from agent_memory_gateway.models import MemoryType, RecallRequest, StoreRequest
from agent_memory_gateway.service import MemoryGateway


class LangChainMemoryAdapter:
    """Thin adapter exposing MemoryGateway as LangChain-compatible memory hooks."""

    def __init__(
        self,
        gateway: MemoryGateway,
        tenant_id: str,
        agent_id: str,
        session_id: str | None = None,
        memory_type: MemoryType = MemoryType.EPISODIC,
    ) -> None:
        self.gateway = gateway
        self.tenant_id = tenant_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.memory_type = memory_type

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, Any]) -> None:
        user_text = " ".join(str(v) for v in inputs.values())
        assistant_text = " ".join(str(v) for v in outputs.values())
        self.gateway.store(
            StoreRequest(
                tenant_id=self.tenant_id,
                agent_id=self.agent_id,
                session_id=self.session_id,
                memory_type=self.memory_type,
                content=f"User: {user_text}\nAssistant: {assistant_text}",
                metadata={"framework": "langchain"},
            )
        )

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        query = " ".join(str(v) for v in inputs.values())
        hits = self.gateway.recall(
            RecallRequest(
                tenant_id=self.tenant_id,
                agent_id=self.agent_id,
                query=query,
                session_id=self.session_id,
                limit=5,
            )
        )
        history = "\n".join(h.content for h in hits)
        return {"history": history}

    def clear(self) -> None:
        if self.session_id:
            from agent_memory_gateway.models import ForgetRequest

            self.gateway.forget(
                ForgetRequest(
                    tenant_id=self.tenant_id,
                    agent_id=self.agent_id,
                    session_id=self.session_id,
                )
            )


def as_langchain_memory(
    gateway: MemoryGateway,
    tenant_id: str,
    agent_id: str,
    session_id: str | None = None,
) -> LangChainMemoryAdapter:
    """Factory for LangChain-style memory without requiring langchain-core."""
    return LangChainMemoryAdapter(gateway, tenant_id, agent_id, session_id=session_id)