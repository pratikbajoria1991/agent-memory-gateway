from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent_memory_gateway.models import MemoryType, RecallRequest, StoreRequest
from agent_memory_gateway.service import MemoryGateway
from agent_memory_gateway.store import SQLiteMemoryStore


@dataclass
class EvalScenario:
    name: str
    tenant_id: str
    agent_id: str
    session_id: str | None
    stores: list[tuple[str, MemoryType]]
    query: str
    expected_keywords: list[str]


DEFAULT_SCENARIOS: list[EvalScenario] = [
    EvalScenario(
        name="preference_recall",
        tenant_id="eval",
        agent_id="assistant",
        session_id="s1",
        stores=[
            ("Customer prefers email over phone for support", MemoryType.SEMANTIC),
            ("User timezone is US Pacific", MemoryType.SEMANTIC),
        ],
        query="contact preference email",
        expected_keywords=["email"],
    ),
    EvalScenario(
        name="multi_turn_episodic",
        tenant_id="eval",
        agent_id="assistant",
        session_id="s2",
        stores=[
            ("User asked about refund policy for annual plan", MemoryType.EPISODIC),
            ("User mentioned order number 48291", MemoryType.EPISODIC),
        ],
        query="refund annual plan",
        expected_keywords=["refund"],
    ),
    EvalScenario(
        name="procedural_skill",
        tenant_id="eval",
        agent_id="coder",
        session_id=None,
        stores=[
            ("Always run pytest before committing Python changes", MemoryType.PROCEDURAL),
            ("Use feature branches named feature/<ticket>", MemoryType.PROCEDURAL),
        ],
        query="python test workflow",
        expected_keywords=["pytest"],
    ),
    EvalScenario(
        name="session_scoped_recall",
        tenant_id="eval",
        agent_id="assistant",
        session_id="s3",
        stores=[
            ("Session-specific: meeting at 3pm Tuesday", MemoryType.EPISODIC),
        ],
        query="meeting Tuesday",
        expected_keywords=["tuesday", "3pm"],
    ),
]


def _keyword_hit(results: list[Any], keywords: list[str]) -> bool:
    combined = " ".join(r.content.lower() for r in results)
    return any(kw.lower() in combined for kw in keywords)


def run_eval_suite(
    scenarios: list[EvalScenario] | None = None,
    k: int = 3,
    gateway: MemoryGateway | None = None,
) -> dict[str, Any]:
    gw = gateway or MemoryGateway(SQLiteMemoryStore())
    cases = scenarios or DEFAULT_SCENARIOS
    failures: list[dict[str, str]] = []
    hits = 0

    for scenario in cases:
        for content, memory_type in scenario.stores:
            gw.store(
                StoreRequest(
                    tenant_id=scenario.tenant_id,
                    agent_id=scenario.agent_id,
                    session_id=scenario.session_id,
                    memory_type=memory_type,
                    content=content,
                )
            )

        results = gw.recall(
            RecallRequest(
                tenant_id=scenario.tenant_id,
                agent_id=scenario.agent_id,
                query=scenario.query,
                session_id=scenario.session_id,
                limit=k,
            )
        )

        if _keyword_hit(results, scenario.expected_keywords):
            hits += 1
        else:
            failures.append(
                {
                    "scenario": scenario.name,
                    "reason": f"expected {scenario.expected_keywords} in top-{k}, got {len(results)} results",
                }
            )

    total = len(cases)
    return {
        "k": k,
        "total": total,
        "passed": hits,
        "hit_rate": hits / total if total else 0.0,
        "recall_at_k": hits / total if total else 0.0,
        "failures": failures,
    }