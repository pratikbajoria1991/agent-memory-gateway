from __future__ import annotations

from datetime import timezone

from agent_memory_gateway.models import MemoryRecord, MemoryType
from agent_memory_gateway.store import MemoryStore, _simple_score, _utcnow


def _record_to_json(record: MemoryRecord) -> str:
    return record.model_dump_json()


def _record_from_json(data: str, score: float | None = None) -> MemoryRecord:
    record = MemoryRecord.model_validate_json(data)
    if score is not None:
        record.score = score
    return record


class RedisMemoryStore(MemoryStore):
    """Redis-backed memory store with tenant/agent indexing."""

    def __init__(self, url: str = "redis://localhost:6379/0", key_prefix: str = "amg") -> None:
        try:
            import redis
        except ImportError as exc:
            raise ImportError(
                "Redis backend requires the redis package. Install with: pip install agent-memory-gateway[redis]"
            ) from exc

        self.client = redis.from_url(url, decode_responses=True)
        self.prefix = key_prefix.rstrip(":")

    def _mem_key(self, memory_id: str) -> str:
        return f"{self.prefix}:mem:{memory_id}"

    def _index_key(self, tenant_id: str, agent_id: str) -> str:
        return f"{self.prefix}:idx:{tenant_id}:{agent_id}"

    def _load_record(self, memory_id: str) -> MemoryRecord | None:
        raw = self.client.get(self._mem_key(memory_id))
        if not raw:
            return None
        return _record_from_json(raw)

    def _is_expired(self, record: MemoryRecord) -> bool:
        if record.expires_at is None:
            return False
        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires <= _utcnow()

    def store(self, record: MemoryRecord) -> MemoryRecord:
        pipe = self.client.pipeline()
        mem_key = self._mem_key(record.id)
        pipe.set(mem_key, _record_to_json(record))
        if record.expires_at:
            ttl = int((record.expires_at - record.created_at).total_seconds())
            if ttl > 0:
                pipe.expire(mem_key, ttl)
        pipe.sadd(self._index_key(record.tenant_id, record.agent_id), record.id)
        pipe.execute()
        return record

    def recall(
        self,
        tenant_id: str,
        agent_id: str,
        query: str,
        memory_types: list[MemoryType] | None = None,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        ids = self.client.smembers(self._index_key(tenant_id, agent_id))
        records: list[MemoryRecord] = []

        for memory_id in ids:
            record = self._load_record(memory_id)
            if record is None or self._is_expired(record):
                self.client.srem(self._index_key(tenant_id, agent_id), memory_id)
                self.client.delete(self._mem_key(memory_id))
                continue
            if memory_types and record.memory_type not in memory_types:
                continue
            if session_id and record.session_id not in (session_id, None):
                continue
            record.score = _simple_score(query, record.content)
            records.append(record)

        records.sort(key=lambda r: r.score or 0, reverse=True)
        return records[:limit]

    def forget(
        self,
        tenant_id: str,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        memory_id: str | None = None,
    ) -> int:
        if memory_id:
            record = self._load_record(memory_id)
            if record is None or record.tenant_id != tenant_id:
                return 0
            self.client.delete(self._mem_key(memory_id))
            self.client.srem(self._index_key(record.tenant_id, record.agent_id), memory_id)
            return 1

        if agent_id is None:
            return 0

        ids = list(self.client.smembers(self._index_key(tenant_id, agent_id)))
        deleted = 0
        for mid in ids:
            record = self._load_record(mid)
            if record is None:
                self.client.srem(self._index_key(tenant_id, agent_id), mid)
                continue
            if session_id and record.session_id != session_id:
                continue
            if user_id and record.metadata.get("user_id") != user_id:
                continue
            self.client.delete(self._mem_key(mid))
            self.client.srem(self._index_key(tenant_id, agent_id), mid)
            deleted += 1
        return deleted

    def list_session(
        self, tenant_id: str, agent_id: str, session_id: str
    ) -> list[MemoryRecord]:
        ids = self.client.smembers(self._index_key(tenant_id, agent_id))
        records: list[MemoryRecord] = []
        for memory_id in ids:
            record = self._load_record(memory_id)
            if record is None or self._is_expired(record):
                continue
            if record.session_id == session_id:
                records.append(record)
        records.sort(key=lambda r: r.created_at)
        return records