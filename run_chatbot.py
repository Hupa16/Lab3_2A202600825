"""Run chatbot baseline (no tools)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.chatbot.baseline import TourChatbot
from src.core.factory import create_provider


def main():
    query = (
        " ".join(sys.argv[1:]).strip()
        or "I would like a 5-day tour for 3 people. We enjoy beaches and local cuisine in Central Vietnam. "
    "Our budget is a maximum of 2000 dollar per day, with a standard package. "
    "Please suggest destinations, provide estimated costs, and create an exploration itinerary."
    )
    print("=== Tour Chatbot Baseline (no tools) ===\n")
    print(f"Request: {query}\n")

    bot = TourChatbot(create_provider())
    print(bot.run(query))


if __name__ == "__main__":
    main()
