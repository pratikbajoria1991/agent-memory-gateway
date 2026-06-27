from __future__ import annotations

from agent_memory_gateway.config import Settings, get_settings
from agent_memory_gateway.store import MemoryStore, SQLiteMemoryStore


def create_memory_store(settings: Settings | None = None) -> MemoryStore:
    cfg = settings or get_settings()
    if cfg.backend == "redis":
        from agent_memory_gateway.redis_store import RedisMemoryStore

        return RedisMemoryStore(url=cfg.redis_url, key_prefix=cfg.redis_key_prefix)
    return SQLiteMemoryStore(cfg.sqlite_path)