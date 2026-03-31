# Prior Auth Readiness Handoff Agent

A small, rules-first LangGraph workflow for prior authorization packet readiness.

This repo shows how a narrow healthcare administrative workflow can validate a mock prior auth case, surface missing information, require an explicit human-in-the-loop review, and produce a structured handoff summary with traceable steps.

## 30-Second Overview

- `What it is`: a bounded administrative workflow agent for mock prior auth readiness checks
- `Why it matters`: incomplete prior auth packets create avoidable rework, delays, and unclear handoffs
- `What it demonstrates`: LangGraph orchestration, typed shared state, rules-first validation, visible traces, and explicit human-in-the-loop review
- `What it does not demonstrate`: diagnosis, treatment guidance, medical necessity adjudication, payer integration, or production infrastructure

## What This Repo Demonstrates

- LangGraph stateful orchestration with clearly named nodes
- rules-first logic for packet readiness
- three explicit statuses: `READY`, `MISSING_INFO`, `ESCALATE_TO_HUMAN`
- an explicit human-in-the-loop checkpoint before final handoff
- trace visibility for every workflow step
- a final structured handoff summary artifact that is easy to inspect

## What It Does Not Do

- no diagnosis or treatment recommendations
- no clinician-facing decision support
- no EHR or payer integrations
- no PHI
- no autonomous submission or medical action
- no database, auth, or deployment platform complexity
- no production-readiness claims

## Workflow Summary

```text
ingest_case
  -> load_rules
  -> validate_case
  -> determine_status
  -> prepare_ready_packet / prepare_missing_info_packet / prepare_escalation_packet
  -> human_review
  -> finalize_handoff
```

The core logic is deterministic and configuration-driven. LangGraph handles shared state, routing, the human-in-the-loop pause, and final handoff completion.

## Statuses

- `READY`: the required fields and attachments are present under the configured rules
- `MISSING_INFO`: the packet is incomplete and should not move forward yet
- `ESCALATE_TO_HUMAN`: the workflow identified a manual-handling scenario even if the packet is otherwise complete

Sample outputs:

- [case_001_output.json](/Users/nicholasleko/projects/Langraph-agent/outputs/case_001_output.json)
- [case_002_output.json](/Users/nicholasleko/projects/Langraph-agent/outputs/case_002_output.json)
- [case_003_output.json](/Users/nicholasleko/projects/Langraph-agent/outputs/case_003_output.json)

## Where Human-In-The-Loop Appears

The automated review stops at the `human_review` node. A reviewer can:

- approve a `READY` handoff
- confirm a `MISSING_INFO` route
- force or confirm `ESCALATE_TO_HUMAN`

That decision is then resumed back into the graph and recorded in the final handoff summary.

## Where Traces Appear

- in the Streamlit app during the automated review
- in the final Streamlit view after human-in-the-loop review
- inside the saved `trace_log` field of each output JSON

## Screenshots

- Home / case selector: [app_home.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/app_home.png)
- Validation and trace visibility: [validation_trace_case_002.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/validation_trace_case_002.png)
- Final handoff summary: [final_handoff_case_003.png](/Users/nicholasleko/projects/Langraph-agent/assets/screenshots/final_handoff_case_003.png)

## Repo Map

- [app.py](/Users/nicholasleko/projects/Langraph-agent/app.py): one-page Streamlit demo for case selection, automated review, human-in-the-loop review, traces, and final handoff
- [src/graph.py](/Users/nicholasleko/projects/Langraph-agent/src/graph.py): LangGraph assembly and run helpers
- [src/nodes.py](/Users/nicholasleko/projects/Langraph-agent/src/nodes.py): workflow nodes, routing prep, and human-in-the-loop pause
- [src/state.py](/Users/nicholasleko/projects/Langraph-agent/src/state.py): typed shared state
- [data/sample_cases.json](/Users/nicholasleko/projects/Langraph-agent/data/sample_cases.json): three mock prior auth cases
- [data/rules.json](/Users/nicholasleko/projects/Langraph-agent/data/rules.json): editable readiness rules and escalation conditions
- [outputs/](/Users/nicholasleko/projects/Langraph-agent/outputs): saved handoff summaries for the sample cases
- [docs/architecture.md](/Users/nicholasleko/projects/Langraph-agent/docs/architecture.md): workflow and design explanation
- [docs/demo_walkthrough.md](/Users/nicholasleko/projects/Langraph-agent/docs/demo_walkthrough.md): demo path and screenshot guidance
- [docs/scope_and_boundaries.md](/Users/nicholasleko/projects/Langraph-agent/docs/scope_and_boundaries.md): scope lock and safety boundaries

## Run Locally

```bash
cd /Users/nicholasleko/projects/Langraph-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then:

1. Select a mock prior auth case.
2. Run the automated readiness review.
3. Inspect validation checks, missing items, and the workflow trace.
4. Apply a human-in-the-loop decision.
5. Review the final handoff summary artifact.

## Why This Is An Administrative Workflow Agent, Not Medical AI

This system checks packet completeness, readiness status, and handoff routing. It does not diagnose, recommend treatment, or adjudicate medical necessity. The purpose is administrative workflow quality and auditability, not clinical decision-making.
