# Agent Memory Gateway

[![CI](https://github.com/pratikbajoria1991/agent-memory-gateway/actions/workflows/ci.yml/badge.svg)](https://github.com/pratikbajoria1991/agent-memory-gateway/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
| OpenTelemetry export | ✅ optional extra |
| Redis backend | ✅ optional extra |
| Recall eval harness (`amg eval`) | ✅ |
| LangChain / LlamaIndex adapters | ✅ |

## Quick start

```bash
pip install -e .
amg serve --port 8741
# or: amg --port 8741 serve
```

API docs: http://127.0.0.1:8741/docs

### Optional extras

```bash
pip install -e ".[redis,otel,dev]"
```

### Configuration (environment)

| Variable | Default | Description |
|----------|---------|-------------|
| `AMG_BACKEND` | `sqlite` | `sqlite` or `redis` |
| `AMG_SQLITE_PATH` | `:memory:` | SQLite database path |
| `AMG_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `AMG_OTEL_ENABLED` | `false` | Enable OpenTelemetry spans |

### Recall evaluation

```bash
amg eval
amg eval --k 5 --json
```

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
from agent_memory_gateway.store_factory import create_memory_store

gw = MemoryGateway(create_memory_store())

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
 SQLite        Redis
```

## Framework adapters

```python
from agent_memory_gateway.adapters.langchain import as_langchain_memory
from agent_memory_gateway.adapters.llamaindex import as_llamaindex_memory

lc_mem = as_langchain_memory(gw, tenant_id="acme", agent_id="bot", session_id="s1")
lc_mem.save_context({"input": "question"}, {"output": "answer"})

li_mem = as_llamaindex_memory(gw, "acme", "bot", session_id="s1")
li_mem.put({"role": "user", "content": "remember this preference"})
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