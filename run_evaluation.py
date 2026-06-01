"""
Run Chatbot vs Agent evaluation and save results (group score: Evaluation & Analysis).

  python run_evaluation.py
  python run_evaluation.py --agent v1
  python run_evaluation.py --output report/evaluation_results.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.factory import create_provider
from src.evaluation.runner import run_evaluation


def main():
    parser = argparse.ArgumentParser(description="Tour planning lab evaluation")
    parser.add_argument("--agent", choices=["v1", "v2"], default="v2")
    parser.add_argument(
        "--cases",
        default=os.path.join("data", "evaluation_cases.json"),
    )
    parser.add_argument(
        "--output",
        default=os.path.join("report", "evaluation_results.json"),
    )
    args = parser.parse_args()

    print(f"=== Evaluation: Chatbot vs Agent {args.agent.upper()} ===\n")

    llm = create_provider()
    summary = run_evaluation(llm, args.cases, agent_version=args.agent)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    for mode, data in summary["modes"].items():
        print(f"{mode}: {data['passed']}/{data['total']} passed ({data['success_rate']*100:.0f}%)")

    print("\nHead-to-head:")
    for row in summary.get("comparison", []):
        print(f"  [{row['case_id']}] ({row['type']}) → winner: {row['winner']}")

    m = summary.get("metrics", {})
    if m.get("request_count"):
        print(
            f"\nTelemetry: {m['request_count']} LLM calls, "
            f"{m['total_tokens']} tokens, ~${m['total_cost_usd']} USD, "
            f"p50 latency {m['p50_latency_ms']}ms"
        )

    print(f"\nSaved: {args.output}")


if __name__ == "__main__":
    main()
