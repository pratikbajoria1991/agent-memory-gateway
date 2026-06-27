from agent_memory_gateway.models import (
    BudgetRequest,
    ForgetRequest,
    MemoryType,
    RecallRequest,
    StoreRequest,
)
from agent_memory_gateway.service import MemoryGateway
from agent_memory_gateway.store import SQLiteMemoryStore


def test_store_and_recall():
    gw = MemoryGateway(SQLiteMemoryStore())
    gw.store(
        StoreRequest(
            tenant_id="acme",
            agent_id="support-bot",
            session_id="s1",
            memory_type=MemoryType.SEMANTIC,
            content="Customer prefers email over phone",
            metadata={"user_id": "u42"},
        )
    )
    results = gw.recall(
        RecallRequest(
            tenant_id="acme",
            agent_id="support-bot",
            query="email preference",
            limit=5,
        )
    )
    assert len(results) == 1
    assert "email" in results[0].content.lower()


def test_forget_by_user_gdpr():
    gw = MemoryGateway(SQLiteMemoryStore())
    gw.store(
        StoreRequest(
            tenant_id="acme",
            agent_id="bot",
            content="User likes hiking",
            metadata={"user_id": "u99"},
        )
    )
    deleted = gw.forget(ForgetRequest(tenant_id="acme", user_id="u99"))
    assert deleted["deleted"] == 1
    assert gw.recall(RecallRequest(tenant_id="acme", agent_id="bot", query="hiking")) == []


def test_context_budget_offloads():
    gw = MemoryGateway(SQLiteMemoryStore())
    messages = [{"role": "user", "content": f"message {i} " * 50} for i in range(20)]
    resp = gw.budget(
        BudgetRequest(
            tenant_id="acme",
            agent_id="bot",
            session_id="s-budget",
            context_messages=messages,
            max_tokens=500,
        )
    )
    assert resp.offloaded_count > 0
    assert len(resp.kept_messages) < len(messages)
    recalled = gw.recall(
        RecallRequest(
            tenant_id="acme",
            agent_id="bot",
            query="message",
            session_id="s-budget",
        )
    )
    assert len(recalled) >= 1