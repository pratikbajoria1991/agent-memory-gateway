from __future__ import annotations

import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from agent_memory_gateway.models import MemoryRecord, MemoryType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _simple_score(query: str, content: str) -> float:
    q = set(query.lower().split())
    c = set(content.lower().split())
    if not q:
        return 0.0
    return len(q & c) / len(q)


class MemoryStore(ABC):
    @abstractmethod
    def store(self, record: MemoryRecord) -> MemoryRecord:
        ...

    @abstractmethod
    def recall(
        self,
        tenant_id: str,
        agent_id: str,
        query: str,
        memory_types: list[MemoryType] | None = None,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        ...

    @abstractmethod
    def forget(
        self,
        tenant_id: str,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        memory_id: str | None = None,
    ) -> int:
        ...

    @abstractmethod
    def list_session(
        self, tenant_id: str, agent_id: str, session_id: str
    ) -> list[MemoryRecord]:
        ...


class SQLiteMemoryStore(MemoryStore):
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                user_id TEXT
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_tenant_agent ON memories(tenant_id, agent_id)"
        )
        self.conn.commit()

    def _row_to_record(self, row: sqlite3.Row, score: float | None = None) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            memory_type=MemoryType(row["memory_type"]),
            content=row["content"],
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=(
                datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
            ),
            score=score,
        )

    def store(self, record: MemoryRecord) -> MemoryRecord:
        user_id = record.metadata.get("user_id")
        self.conn.execute(
            """
            INSERT INTO memories
            (id, tenant_id, agent_id, session_id, memory_type, content, metadata,
             created_at, expires_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.tenant_id,
                record.agent_id,
                record.session_id,
                record.memory_type.value,
                record.content,
                json.dumps(record.metadata),
                record.created_at.isoformat(),
                record.expires_at.isoformat() if record.expires_at else None,
                user_id,
            ),
        )
        self.conn.commit()
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
        now = _utcnow().isoformat()
        clauses = ["tenant_id = ?", "agent_id = ?", "(expires_at IS NULL OR expires_at > ?)"]
        params: list[Any] = [tenant_id, agent_id, now]

        if memory_types:
            placeholders = ",".join("?" * len(memory_types))
            clauses.append(f"memory_type IN ({placeholders})")
            params.extend(m.value for m in memory_types)

        if session_id:
            clauses.append("(session_id = ? OR session_id IS NULL)")
            params.append(session_id)

        sql = f"SELECT * FROM memories WHERE {' AND '.join(clauses)}"
        rows = self.conn.execute(sql, params).fetchall()

        scored = [
            (self._row_to_record(row, _simple_score(query, row["content"])), row)
            for row in rows
        ]
        scored.sort(key=lambda x: x[0].score or 0, reverse=True)
        return [r for r, _ in scored[:limit]]

    def forget(
        self,
        tenant_id: str,
        agent_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        memory_id: str | None = None,
    ) -> int:
        clauses = ["tenant_id = ?"]
        params: list[Any] = [tenant_id]

        if memory_id:
            clauses.append("id = ?")
            params.append(memory_id)
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if user_id:
            clauses.append("user_id = ?")
            params.append(user_id)

        sql = f"DELETE FROM memories WHERE {' AND '.join(clauses)}"
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.rowcount

    def list_session(
        self, tenant_id: str, agent_id: str, session_id: str
    ) -> list[MemoryRecord]:
        rows = self.conn.execute(
            """
            SELECT * FROM memories
            WHERE tenant_id = ? AND agent_id = ? AND session_id = ?
            ORDER BY created_at ASC
            """,
            (tenant_id, agent_id, session_id),
        ).fetchall()
        return [self._row_to_record(row) for row in rows]


def new_record(
    tenant_id: str,
    agent_id: str,
    content: str,
    memory_type: MemoryType,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ttl_seconds: int | None = None,
) -> MemoryRecord:
    now = _utcnow()
    return MemoryRecord(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        agent_id=agent_id,
        session_id=session_id,
        memory_type=memory_type,
        content=content,
        metadata=metadata or {},
        created_at=now,
        expires_at=now + timedelta(seconds=ttl_seconds) if ttl_seconds else None,
    )