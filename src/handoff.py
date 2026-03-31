from __future__ import annotations

from src.models import HandoffSummary, ReadinessStatus
from src.state import WorkflowState


NEXT_ACTIONS: dict[ReadinessStatus, str] = {
    "READY": "Submit the prior auth packet to the payer queue after coordinator sign-off.",
    "MISSING_INFO": "Request the missing fields or attachments before the case is submitted.",
    "ESCALATE_TO_HUMAN": "Route the case to a human utilization management or prior auth coordinator for manual handling.",
}


def build_handoff_summary(state: WorkflowState) -> HandoffSummary:
    final_status, escalation_reason = resolve_final_status_and_reason(state)
    case_data = state["case_data"]
    human_decision = state["human_decision"]
    next_action = NEXT_ACTIONS[final_status]
    missing_labels = ", ".join(item["label"] for item in state.get("missing_items", []))
    missing_phrase = missing_labels or "the required readiness items captured by the workflow"

    if final_status == "READY":
        summary_paragraph = (
            f"Case {case_data['case_id']} for {case_data['service_requested']} is complete under the configured "
            "readiness rules. Human review approved the packet as ready, and the next administrative step is payer submission."
        )
    elif final_status == "MISSING_INFO":
        summary_paragraph = (
            f"Case {case_data['case_id']} is not ready for submission. Missing items include {missing_phrase}, "
            "and human review confirmed the missing-information route before handoff."
        )
    else:
        summary_paragraph = (
            f"Case {case_data['case_id']} requires manual handling. Human review escalated the request because "
            f"{escalation_reason or 'the workflow flagged a manual-review scenario'}"
        )

    return {
        "case_id": case_data["case_id"],
        "requested_service": case_data["service_requested"],
        "automated_status": state["automated_status"],
        "readiness_status": final_status,
        "missing_items": state.get("missing_items", []),
        "escalation_reason": escalation_reason,
        "human_review_decision": human_decision,
        "recommended_next_action": next_action,
        "summary_paragraph": summary_paragraph,
        "trace_log": state.get("trace_log", []),
    }


def resolve_final_status_and_reason(state: WorkflowState) -> tuple[ReadinessStatus, str | None]:
    decision = state["human_decision"]["action"]
    if decision == "APPROVE_READY":
        return "READY", None
    if decision == "CONFIRM_MISSING_INFO":
        return "MISSING_INFO", None
    return "ESCALATE_TO_HUMAN", state.get("escalation_reason") or "Human reviewer requested manual handling."
