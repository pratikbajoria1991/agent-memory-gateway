# Agent Memory Gateway

Unified memory layer for AI agents. One API for **episodic**, **semantic**, and **procedural** memory — with multi-tenancy, TTL, GDPR erase, context budgeting, and observability hooks.

Built to fill the gap between agent frameworks (LangChain, etc.), vector databases, and observability tools — none of which own memory end-to-end.

## Features

| Feature | Status |
|---------|--------|
| Episodic / semantic / procedural memory types | ✅ |
| Multi-tenant isolation (`tenant_id`) | ✅ |
| TTL expiration | ✅ |
| Recall with relevance scoring | ✅ |
| GDPR erase (`forget` by `user_id`) | ✅ |
| Context budget manager (offload to memory) | ✅ |
| Session consolidation | ✅ |
| Memory operation tracing (logs) | ✅ |
| OpenTelemetry export | 🔜 optional extra |
| Redis / Qdrant backends | 🔜 planned |

## Quick start

```bash
pip install -e .
amg --port 8741
```

API docs: http://127.0.0.1:8741/docs

## API

### Store memory

```bash
curl -X POST http://127.0.0.1:8741/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme",
    "agent_id": "support-bot",
    "session_id": "sess-001",
    "memory_type": "semantic",
    "content": "Customer prefers email support",
    "ttl_seconds": 86400
  }'
```

### Recall memory

```bash
curl -X POST http://127.0.0.1:8741/v1/memory/recall \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme",
    "agent_id": "support-bot",
    "query": "contact preference",
    "limit": 5
  }'
```

### GDPR erase

```bash
curl -X POST http://127.0.0.1:8741/v1/memory/forget \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "acme", "user_id": "user-42"}'
```

### Context budget (offload overflow to episodic memory)

```bash
curl -X POST http://127.0.0.1:8741/v1/memory/budget \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "acme",
    "agent_id": "support-bot",
    "session_id": "sess-001",
    "max_tokens": 4000,
    "context_messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }'
```

## Python SDK

```python
from agent_memory_gateway.models import StoreRequest, RecallRequest, MemoryType
from agent_memory_gateway.service import MemoryGateway
from agent_memory_gateway.store import SQLiteMemoryStore

gw = MemoryGateway(SQLiteMemoryStore("memory.db"))

gw.store(StoreRequest(
    tenant_id="acme",
    agent_id="bot",
    memory_type=MemoryType.EPISODIC,
    content="User asked about refund policy",
))

hits = gw.recall(RecallRequest(
    tenant_id="acme",
    agent_id="bot",
    query="refund",
))
```

## Architecture

```
Agent / Framework
       │
       ▼
┌──────────────────────┐
│  Memory Gateway API  │  store · recall · forget · consolidate · budget
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
 SQLite      (Redis / Qdrant — planned)
```

## Deploy to GitHub

```bash
git init
git add .
git commit -m "Initial commit: agent memory gateway"
gh auth login
gh repo create agent-memory-gateway --public --source=. --push
```

## Related

Companion analysis tool: [opensource-demand-analyzer](../opensource-demand-analyzer) — scans GitHub for demand and feature gaps across AI infra categories including `memory-infra`.

## License

MIT