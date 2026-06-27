from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from agent_memory_gateway.eval.recall_eval import run_eval_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Memory Gateway CLI")
    parser.add_argument("--host", default="127.0.0.1", help="API host (serve mode)")
    parser.add_argument("--port", type=int, default=8741, help="API port (serve mode)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Run API server")

    eval_cmd = sub.add_parser("eval", help="Run recall evaluation harness")
    eval_cmd.add_argument("--k", type=int, default=3, help="Recall@k limit")
    eval_cmd.add_argument("--json", action="store_true", help="Output JSON report")

    args = parser.parse_args()
    command = args.command or "serve"

    if command == "eval":
        report = run_eval_suite(k=args.k)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Recall@{report['k']}: {report['recall_at_k']:.1%}")
            print(f"Hit rate: {report['hit_rate']:.1%}")
            print(f"Scenarios: {report['passed']}/{report['total']} passed")
            if report["failures"]:
                print("Failures:")
                for failure in report["failures"]:
                    print(f"  - {failure['scenario']}: {failure['reason']}")
        sys.exit(0 if report["passed"] == report["total"] else 1)

    uvicorn.run("agent_memory_gateway.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()