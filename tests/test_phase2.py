import pytest

from agent_memory_gateway.adapters.langchain import LangChainMemoryAdapter
from agent_memory_gateway.adapters.llamaindex import LlamaIndexMemoryAdapter
from agent_memory_gateway.config import Settings
from agent_memory_gateway.eval.recall_eval import run_eval_suite
from agent_memory_gateway.models import MemoryType, RecallRequest, StoreRequest
from agent_memory_gateway.service import MemoryGateway
from agent_memory_gateway.store import SQLiteMemoryStore
from agent_memory_gateway.store_factory import create_memory_store
from agent_memory_gateway.telemetry import trace_operation


def test_create_memory_store_sqlite():
    store = create_memory_store(Settings(backend="sqlite", sqlite_path=":memory:"))
    assert isinstance(store, SQLiteMemoryStore)


def test_recall_eval_suite_passes():
    report = run_eval_suite(k=3)
    assert report["total"] >= 3
    assert report["passed"] == report["total"]
    assert report["recall_at_k"] == 1.0


def test_langchain_adapter_roundtrip():
    gw = MemoryGateway(SQLiteMemoryStore())
    mem = LangChainMemoryAdapter(gw, "t1", "agent", session_id="s1")
    mem.save_context({"input": "refund policy"}, {"output": "30 day window"})
    vars_ = mem.load_memory_variables({"input": "refund"})
    assert "refund" in vars_["history"].lower()


def test_llamaindex_adapter_roundtrip():
    gw = MemoryGateway(SQLiteMemoryStore())
    mem = LlamaIndexMemoryAdapter(gw, "t1", "agent", session_id="s1")
    mem.put({"role": "user", "content": "deploy to staging first"})
    hits = mem.get("deploy staging")
    assert len(hits) >= 1
    assert "staging" in hits[0]["content"].lower()


def test_trace_operation_without_otel():
    with trace_operation("test", tenant="t1"):
        pass


def test_redis_store_roundtrip():
    pytest.importorskip("fakeredis")
    import fakeredis

    from agent_memory_gateway.redis_store import RedisMemoryStore

    client = fakeredis.FakeRedis(decode_responses=True)
    store = RedisMemoryStore.__new__(RedisMemoryStore)
    store.client = client
    store.prefix = "amg"

    gw = MemoryGateway(store)
    gw.store(
        StoreRequest(
            tenant_id="acme",
            agent_id="bot",
            memory_type=MemoryType.SEMANTIC,
            content="User likes dark mode UI",
        )
    )
    results = gw.recall(
        RecallRequest(tenant_id="acme", agent_id="bot", query="dark mode", limit=5)
    )
    assert len(results) == 1
    assert "dark" in results[0].content.lower()