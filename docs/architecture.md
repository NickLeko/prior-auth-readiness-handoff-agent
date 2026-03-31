# Architecture

## Workflow Overview

This project models a bounded prior authorization readiness workflow for mock administrative cases. The workflow is intentionally narrow: it checks whether a case packet is complete enough for handoff, identifies missing information, routes manual-handling scenarios, and captures a final handoff summary after human-in-the-loop review.

## State Model

The LangGraph state is defined in [src/state.py](/Users/nicholasleko/projects/Langraph-agent/src/state.py).

Core fields:

- `case_data`
- `rule_set`
- `validation_results`
- `missing_items`
- `automated_status`
- `readiness_status`
- `escalation_reason`
- `human_review_required`
- `human_decision`
- `final_handoff_summary`
- `trace_log`

The state is typed with `TypedDict` so the workflow stays small, explicit, and easy to inspect.

## Node Descriptions

- `ingest_case`: loads the selected mock case from `data/sample_cases.json`
- `load_rules`: loads the rule set for the case type from `data/rules.json`
- `validate_case`: performs deterministic field and document checks
- `determine_status`: classifies the automated result as `READY`, `MISSING_INFO`, or `ESCALATE_TO_HUMAN`
- `prepare_ready_packet`: builds a reviewer packet for clean cases
- `prepare_missing_info_packet`: builds a reviewer packet for incomplete cases
- `prepare_escalation_packet`: builds a reviewer packet for manual-handling scenarios
- `human_review`: pauses at an explicit human-in-the-loop checkpoint and waits for a reviewer decision
- `finalize_handoff`: creates the final structured handoff summary artifact

## Routing Logic

Routing is driven by the automated status after validation.

```text
determine_status
  READY -> prepare_ready_packet
  MISSING_INFO -> prepare_missing_info_packet
  ESCALATE_TO_HUMAN -> prepare_escalation_packet
```

All three branches converge into the same `human_review` node before finalization.

## Human-In-The-Loop Explanation

The human-in-the-loop checkpoint is implemented as a LangGraph pause using `interrupt(...)` inside the `human_review` node.

The app runs the automated portion first, then exposes:

- the automated status
- validation results
- missing items
- escalation reasons
- the workflow trace

The reviewer can then choose one of three actions:

- approve a `READY` handoff
- confirm a `MISSING_INFO` route
- escalate to `ESCALATE_TO_HUMAN`

That decision is resumed back into the graph and recorded in the final handoff summary.

## Trace And Logging

Each node appends a structured trace entry with:

- step index
- timestamp
- node name
- status
- message
- optional details

The workflow trace is visible in the Streamlit UI and also included in the final output JSON. This keeps the prototype screenshotable and easy to discuss in interviews.

## Design Tradeoffs

- Rules-first logic was chosen over heavy LLM usage because readiness checks are deterministic and easier to audit.
- Streamlit was used instead of a larger frontend so the demo stays fast to run and easy to explain.
- A single-agent graph was used to keep the architecture narrow and intentionally bounded.
- Sample data is mock-only and non-PHI so the repo remains safe to share.

## Why Rules-First

This workflow is about packet readiness, not interpretation of complex medical nuance. Required fields, required attachments, and escalation conditions are better represented as editable configuration than as model behavior. That makes the agent more transparent, easier to test, and more appropriate for healthcare administrative operations.
