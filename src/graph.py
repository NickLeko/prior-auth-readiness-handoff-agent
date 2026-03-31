from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from src.nodes import (
    determine_status,
    finalize_handoff,
    human_review,
    ingest_case,
    load_rules,
    prepare_escalation_packet,
    prepare_missing_info_packet,
    prepare_ready_packet,
    validate_case,
)
from src.rules import load_sample_cases
from src.state import WorkflowState
from src.utils import (
    DEFAULT_CASES_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_RULES_PATH,
    build_thread_id,
    default_human_decision_for_case,
    write_json,
)


MEMORY = MemorySaver()


def route_by_status(state: WorkflowState) -> str:
    return state["automated_status"]


def build_graph():
    workflow = StateGraph(WorkflowState)

    workflow.add_node("ingest_case", ingest_case)
    workflow.add_node("load_rules", load_rules)
    workflow.add_node("validate_case", validate_case)
    workflow.add_node("determine_status", determine_status)
    workflow.add_node("prepare_ready_packet", prepare_ready_packet)
    workflow.add_node("prepare_missing_info_packet", prepare_missing_info_packet)
    workflow.add_node("prepare_escalation_packet", prepare_escalation_packet)
    workflow.add_node("human_review", human_review)
    workflow.add_node("finalize_handoff", finalize_handoff)

    workflow.add_edge(START, "ingest_case")
    workflow.add_edge("ingest_case", "load_rules")
    workflow.add_edge("load_rules", "validate_case")
    workflow.add_edge("validate_case", "determine_status")
    workflow.add_conditional_edges(
        "determine_status",
        route_by_status,
        {
            "READY": "prepare_ready_packet",
            "MISSING_INFO": "prepare_missing_info_packet",
            "ESCALATE_TO_HUMAN": "prepare_escalation_packet",
        },
    )
    workflow.add_edge("prepare_ready_packet", "human_review")
    workflow.add_edge("prepare_missing_info_packet", "human_review")
    workflow.add_edge("prepare_escalation_packet", "human_review")
    workflow.add_edge("human_review", "finalize_handoff")
    workflow.add_edge("finalize_handoff", END)

    return workflow.compile(checkpointer=MEMORY)


GRAPH = build_graph()


def start_case_review(
    case_id: str,
    *,
    cases_path: str | None = None,
    rules_path: str | None = None,
    thread_id: str | None = None,
) -> dict[str, Any]:
    config = {"configurable": {"thread_id": thread_id or build_thread_id(case_id)}}
    initial_state: WorkflowState = {
        "case_id": case_id,
        "cases_path": str(Path(cases_path) if cases_path else DEFAULT_CASES_PATH),
        "rules_path": str(Path(rules_path) if rules_path else DEFAULT_RULES_PATH),
        "trace_log": [],
    }
    interrupt_payload = GRAPH.invoke(initial_state, config=config)
    snapshot = GRAPH.get_state(config)
    return {
        "thread_id": config["configurable"]["thread_id"],
        "interrupt": interrupt_payload,
        "state": snapshot.values,
    }


def resume_case_review(thread_id: str, human_decision: dict[str, str]) -> WorkflowState:
    config = {"configurable": {"thread_id": thread_id}}
    GRAPH.invoke(Command(resume=human_decision), config=config)
    snapshot = GRAPH.get_state(config)
    return snapshot.values


def run_case_with_decision(
    case_id: str,
    human_decision: dict[str, str],
    *,
    cases_path: str | None = None,
    rules_path: str | None = None,
) -> WorkflowState:
    run_start = start_case_review(case_id, cases_path=cases_path, rules_path=rules_path)
    return resume_case_review(run_start["thread_id"], human_decision)


def generate_sample_outputs(output_dir: str | None = None) -> dict[str, Any]:
    cases = load_sample_cases()
    destination = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    outputs: dict[str, Any] = {}
    for case_id in cases:
        final_state = run_case_with_decision(case_id, default_human_decision_for_case(case_id))
        handoff_summary = final_state["final_handoff_summary"]
        write_json(destination / f"{case_id}_output.json", handoff_summary)
        outputs[case_id] = handoff_summary
    return outputs
