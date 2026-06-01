"""
Run ReAct tour planning agent.

  python run_agent.py
  python run_agent.py --version v1
  python run_agent.py "Family of 4, 5 days South Vietnam, luxury, beaches."
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.agent.agent import ReActAgentV1, ReActAgentV2
from src.core.factory import create_provider
from src.tools.tour_tools import get_tour_tools


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", choices=["v1", "v2"], default="v2")
    parser.add_argument("query", nargs="*", help="User request in English")
    args = parser.parse_args()

    default_query = (
        "I would like a 5-day tour for 3 people. We enjoy beaches and local cuisine in Central Vietnam. "
    "Our budget is a maximum of 2000 dollar per day, with a standard package. "
    "Please suggest destinations, provide estimated costs, and create an exploration itinerary."
    )
    user_input = " ".join(args.query).strip() or default_query

    AgentCls = ReActAgentV2 if args.version == "v2" else ReActAgentV1
    print(f"=== Vietnam Tour Assistant (ReAct {args.version.upper()}) ===\n")
    print(f"Request: {user_input}\n")
    print("Reasoning… (see logs/ for traces)\n")

    agent = AgentCls(create_provider(), get_tour_tools())
    answer = agent.run(user_input)

    run = agent.last_run
    if run:
        print(f"[steps={run.steps}, tools={run.tools_called}, completed={run.completed}]\n")

    print("--- Result ---\n")
    print(answer)


if __name__ == "__main__":
    main()
