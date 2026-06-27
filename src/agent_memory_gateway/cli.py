from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Agent Memory Gateway API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8741)
    args = parser.parse_args()
    uvicorn.run("agent_memory_gateway.api:app", host=args.host, port=args.port, reload=False)