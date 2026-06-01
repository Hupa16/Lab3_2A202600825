# Individual Report: Lab 3 - Chatbot vs ReAct Agent

* **Student Name**: Phan Tân Hưng
* **Student ID**: 2022604276
* **Date**: 2026-06-01

---

# I. Technical Contribution (15 Points)

During Lab 3, I was responsible for designing, implementing, testing, and evaluating the entire AI-powered tour planning system. My contributions covered the chatbot baseline, ReAct agents, tool implementation, evaluation framework, and documentation.

## Modules Implemented

* `src/chatbot/baseline.py`

  * Implemented the baseline chatbot using a single LLM call without tool usage.

* `src/agents/react_agent_v1.py`

  * Implemented the first ReAct agent using the Thought → Action → Observation loop.

* `src/agents/react_agent_v2.py`

  * Improved the ReAct framework with guardrails, parsing recovery, and duplicate-action protection.

* `src/tools/search_destinations.py`

  * Built a destination search tool based on traveler interests, region, and budget.

* `src/tools/estimate_tour_budget.py`

  * Implemented package cost estimation in both VND and USD.

* `src/tools/build_itinerary.py`

  * Generated personalized day-by-day itineraries.

* `src/telemetry/metrics.py`

  * Added telemetry logging for latency, token usage, and estimated API cost.

## Code Highlights

### ReAct Decision Loop

The agent follows the ReAct framework:

1. Generate a Thought.
2. Select an Action.
3. Execute the selected tool.
4. Observe tool output.
5. Continue reasoning until a Final Answer is produced.

### Agent v2 Improvements

I introduced several improvements:

* Markdown stripping before parsing
* Observation-based retry mechanism
* Duplicate action detection
* Maximum step limits
* Final-answer prompting near loop limits

These improvements significantly reduced parsing failures and infinite loops.

## Documentation

The three tools are integrated directly into the ReAct loop. The agent uses observations returned by tools to determine the next reasoning step.

For example:

User Request
→ search_destinations
→ estimate_tour_budget
→ build_itinerary
→ Final Answer

This allows the system to generate grounded and verifiable tour plans instead of relying solely on LLM-generated estimates.

---

# II. Debugging Case Study (10 Points)

## Problem Description

One of the most common failures occurred when the agent generated an incorrect tool name.

Example:

Action: search_destination(...)

instead of

Action: search_destinations(...)

As a result, the agent could not execute the tool and failed to continue the reasoning process.

## Log Source

Observed in:

* `report/traces/TRACE_FAILURE.md`

Example trace:

Thought: I should search for beach destinations.
Action: search_destination(region="Central Vietnam")

Observation:
ERROR: Unknown tool name.

## Diagnosis

The root cause was prompt ambiguity.

Although tool descriptions were provided, the system prompt did not strongly emphasize exact tool names. Consequently, the LLM occasionally generated semantically similar but invalid tool names.

This issue was more common in Agent v1.

## Solution

To address the problem, I implemented:

### Tool Alias Mapping

Examples:

* search_destination → search_destinations
* budget_estimator → estimate_tour_budget

### Few-shot Examples

Added examples showing the exact expected action format.

### Parsing Recovery

Agent v2 attempts to recover from malformed actions before terminating.

After applying these fixes, tool invocation success improved significantly and multi-step task completion became much more reliable.

---

# III. Personal Insights: Chatbot vs ReAct (10 Points)

## 1. Reasoning

The Thought block provides an explicit reasoning stage before acting.

In the chatbot baseline, the model directly generates an answer, often guessing costs or itinerary details.

In contrast, the ReAct agent:

* Breaks problems into sub-tasks
* Chooses appropriate tools
* Verifies intermediate information
* Produces more grounded responses

For tour planning tasks, this structured reasoning greatly improved answer quality.

## 2. Reliability

Although ReAct generally performed better, it was not always superior.

Cases where the chatbot performed better:

* Simple factual questions
* Greetings
* Short conversational requests

In these situations, the agent sometimes incurred unnecessary reasoning steps and additional latency.

Therefore, ReAct is most beneficial for multi-step planning and decision-making tasks rather than simple Q&A.

## 3. Observation

Observations are the most important component of the ReAct framework.

Without observations, the agent would have no mechanism to validate or update its reasoning.

For example:

Observation:
Estimated package cost = 7,500,000 VND

The agent can then decide:

* Whether the budget is acceptable
* Whether a cheaper destination should be suggested
* Whether itinerary adjustments are needed

This feedback loop makes the system more adaptive and reliable than a standard chatbot.

---

# IV. Future Improvements (5 Points)

## Scalability

To support real-world deployment, I would:

* Integrate hotel booking APIs
* Integrate flight search APIs
* Connect to tourism databases
* Use asynchronous tool execution

This would allow the system to generate real-time travel plans.

## Safety

Additional safeguards could include:

* Destination allowlists
* Budget validation
* Human approval before bookings
* Tool permission management

A supervisor agent could audit actions before execution.

## Performance

To improve efficiency and accuracy:

* Introduce a Vector Database for retrieval
* Use RAG for destination knowledge
* Cache frequently requested itineraries
* Optimize prompt length to reduce token usage

These enhancements would enable the system to scale into a production-ready AI travel assistant.

---

## Conclusion

This lab demonstrated the practical advantages of the ReAct framework over a traditional chatbot. Through tool usage, iterative reasoning, and environmental feedback, the agent produced more accurate and grounded travel recommendations. The experience provided valuable insights into agent design, debugging, telemetry monitoring, and the challenges of building reliable AI systems.
