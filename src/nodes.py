from __future__ import annotations

from langgraph.types import interrupt

from src.handoff import build_handoff_summary
from src.models import HumanDecision, ReviewPacket
from src.rules import evaluate_escalation, evaluate_validation, load_rule_for_case, load_sample_cases
from src.state import WorkflowState
from src.tracing import append_trace


def ingest_case(state: WorkflowState) -> WorkflowState:
    cases = load_sample_cases(state.get("cases_path"))
    case_id = state["case_id"]
    if case_id not in cases:
        raise KeyError(f"Unknown case_id '{case_id}'.")

    case_data = cases[case_id]
    trace_log = append_trace(
        state.get("trace_log"),
        node="ingest_case",
        message=f"Loaded mock case {case_id} for {case_data['service_requested']}.",
        details={"case_type": case_data["case_type"]},
    )
    return {"case_data": case_data, "trace_log": trace_log}


def load_rules(state: WorkflowState) -> WorkflowState:
    rule_set = load_rule_for_case(state["case_data"], state.get("rules_path"))
    trace_log = append_trace(
        state.get("trace_log"),
        node="load_rules",
        message=f"Loaded rule set for {rule_set['case_type']}.",
        details={
            "required_fields": len(rule_set.get("required_fields", [])),
            "required_documents": len(rule_set.get("required_documents", [])),
        },
    )
    return {"rule_set": rule_set, "trace_log": trace_log}


def validate_case(state: WorkflowState) -> WorkflowState:
    validation_results, missing_items = evaluate_validation(state["case_data"], state["rule_set"])
    required_checks = sum(1 for result in validation_results if result["required"])
    passed_checks = sum(1 for result in validation_results if result["required"] and result["passed"])
    trace_log = append_trace(
        state.get("trace_log"),
        node="validate_case",
        message=(
            f"Completed {required_checks} required checks; "
            f"{passed_checks} passed and {len(missing_items)} missing item(s) were identified."
        ),
        details={"missing_labels": [item["label"] for item in missing_items]},
    )
    return {
        "validation_results": validation_results,
        "missing_items": missing_items,
        "trace_log": trace_log,
    }


def determine_status(state: WorkflowState) -> WorkflowState:
    escalation_reasons = evaluate_escalation(state["case_data"], state["rule_set"])
    if escalation_reasons:
        automated_status = "ESCALATE_TO_HUMAN"
        escalation_reason = " ".join(escalation_reasons)
    elif state.get("missing_items"):
        automated_status = "MISSING_INFO"
        escalation_reason = None
    else:
        automated_status = "READY"
        escalation_reason = None

    trace_log = append_trace(
        state.get("trace_log"),
        node="determine_status",
        message=f"Automated classification set to {automated_status}.",
        status=automated_status,
        details={"escalation_reasons": escalation_reasons},
    )
    return {
        "automated_status": automated_status,
        "readiness_status": automated_status,
        "escalation_reason": escalation_reason,
        "human_review_required": True,
        "trace_log": trace_log,
    }


def prepare_ready_packet(state: WorkflowState) -> WorkflowState:
    return _prepare_review_packet(
        state,
        reviewer_prompt="The automated checks found the packet complete. Confirm readiness or override if manual handling is safer.",
        recommended_next_action="Approve for payer submission if the packet looks complete.",
        node_name="prepare_ready_packet",
    )


def prepare_missing_info_packet(state: WorkflowState) -> WorkflowState:
    return _prepare_review_packet(
        state,
        reviewer_prompt="The packet is missing required information. Confirm the missing-info route or escalate if coordination is needed.",
        recommended_next_action="Collect the missing information before submission.",
        node_name="prepare_missing_info_packet",
    )


def prepare_escalation_packet(state: WorkflowState) -> WorkflowState:
    return _prepare_review_packet(
        state,
        reviewer_prompt="The automated workflow flagged a manual-handling scenario. Confirm escalation or override only if appropriate.",
        recommended_next_action="Route the case to a human coordinator for manual handling.",
        node_name="prepare_escalation_packet",
    )


def human_review(state: WorkflowState) -> WorkflowState:
    review_request = {
        "checkpoint": "human_review",
        "review_packet": state["review_packet"],
        "allowed_actions": ["APPROVE_READY", "CONFIRM_MISSING_INFO", "ESCALATE"],
    }
    raw_decision = interrupt(review_request)
    human_decision = normalize_human_decision(raw_decision)
    trace_log = append_trace(
        state.get("trace_log"),
        node="human_review",
        message=f"Human reviewer selected {human_decision['action']}.",
        status=state.get("automated_status"),
        details=human_decision,
    )
    return {"human_decision": human_decision, "trace_log": trace_log}


def finalize_handoff(state: WorkflowState) -> WorkflowState:
    handoff_summary = build_handoff_summary(state)
    trace_log = append_trace(
        state.get("trace_log"),
        node="finalize_handoff",
        message=f"Created final handoff summary with status {handoff_summary['readiness_status']}.",
        status=handoff_summary["readiness_status"],
        details={"recommended_next_action": handoff_summary["recommended_next_action"]},
    )
    handoff_summary["trace_log"] = trace_log
    return {
        "readiness_status": handoff_summary["readiness_status"],
        "escalation_reason": handoff_summary["escalation_reason"],
        "final_handoff_summary": handoff_summary,
        "trace_log": trace_log,
    }


def _prepare_review_packet(
    state: WorkflowState,
    *,
    reviewer_prompt: str,
    recommended_next_action: str,
    node_name: str,
) -> WorkflowState:
    review_packet: ReviewPacket = {
        "case_id": state["case_data"]["case_id"],
        "service_requested": state["case_data"]["service_requested"],
        "automated_status": state["automated_status"],
        "missing_items": state.get("missing_items", []),
        "escalation_reason": state.get("escalation_reason"),
        "reviewer_prompt": reviewer_prompt,
        "recommended_next_action": recommended_next_action,
    }
    trace_log = append_trace(
        state.get("trace_log"),
        node=node_name,
        message=f"Prepared review packet for automated status {state['automated_status']}.",
        status=state["automated_status"],
    )
    return {"review_packet": review_packet, "trace_log": trace_log}


def normalize_human_decision(raw_decision: object) -> HumanDecision:
    if not isinstance(raw_decision, dict):
        raise TypeError("Human review decision must be a dictionary.")

    action = raw_decision.get("action")
    reviewer = raw_decision.get("reviewer")
    rationale = raw_decision.get("rationale")
    valid_actions = {"APPROVE_READY", "CONFIRM_MISSING_INFO", "ESCALATE"}

    if action not in valid_actions:
        raise ValueError(f"Unsupported human review action: {action}")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Human review decision requires a reviewer name.")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("Human review decision requires a rationale.")

    return {
        "action": action,
        "reviewer": reviewer.strip(),
        "rationale": rationale.strip(),
    }
