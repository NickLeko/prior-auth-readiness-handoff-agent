from __future__ import annotations

from typing import Any

import streamlit as st

from src.graph import resume_case_review, start_case_review
from src.rules import load_sample_cases


STATUS_COPY = {
    "READY": "The packet satisfies the configured readiness checks and can move to handoff after human-in-the-loop review.",
    "MISSING_INFO": "The packet is not ready for submission because required fields or attachments are missing.",
    "ESCALATE_TO_HUMAN": "The workflow identified a manual-handling scenario and requires human escalation.",
}

DECISION_OPTIONS = {
    "Approve READY handoff": "APPROVE_READY",
    "Confirm MISSING_INFO route": "CONFIRM_MISSING_INFO",
    "Route to ESCALATE_TO_HUMAN": "ESCALATE",
}


def reset_review_state() -> None:
    for key in ("thread_id", "review_state", "final_state", "selected_case_id"):
        st.session_state.pop(key, None)


def default_decision_label(status: str) -> str:
    if status == "READY":
        return "Approve READY handoff"
    if status == "MISSING_INFO":
        return "Confirm MISSING_INFO route"
    return "Route to ESCALATE_TO_HUMAN"


def build_default_rationale(state: dict[str, Any], action: str) -> str:
    if action == "APPROVE_READY":
        return "The packet is complete under the configured readiness rules and can move to payer submission."
    if action == "CONFIRM_MISSING_INFO":
        return "The missing fields and attachments should be collected before the packet is submitted."
    if state.get("escalation_reason"):
        return state["escalation_reason"]
    return "Manual handling is appropriate for this administrative scenario."


def render_validation_results(state: dict[str, Any]) -> None:
    rows = []
    for item in state.get("validation_results", []):
        rows.append(
            {
                "Item": item["label"],
                "Type": item["item_type"],
                "Required": "Yes" if item["required"] else "Conditional",
                "Passed": "Yes" if item["passed"] else "No",
                "Detail": item["detail"],
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


def render_trace_log(state: dict[str, Any]) -> None:
    rows = []
    for entry in state.get("trace_log", []):
        rows.append(
            {
                "Step": entry["step_index"],
                "Node": entry["node"],
                "Status": entry.get("status") or "-",
                "Message": entry["message"],
                "Timestamp": entry["timestamp"],
            }
        )
    st.dataframe(rows, width="stretch", hide_index=True)


st.set_page_config(
    page_title="Prior Auth Readiness Handoff Agent",
    layout="wide",
)

st.title("Prior Auth Readiness Handoff Agent")
st.caption(
    "Rules-first LangGraph workflow for prior authorization packet readiness, human-in-the-loop review, and structured administrative handoff."
)

cases = load_sample_cases()
case_ids = list(cases.keys())
selected_case_id = st.selectbox(
    "Select a mock prior auth case",
    case_ids,
    format_func=lambda item: f"{item} - {cases[item]['service_requested']}",
    help="These cases are mock administrative packets with no PHI.",
)

if st.session_state.get("selected_case_id") != selected_case_id:
    reset_review_state()
    st.session_state["selected_case_id"] = selected_case_id

selected_case = cases[selected_case_id]

top_col_1, top_col_2, top_col_3 = st.columns(3)
top_col_1.metric("Sample cases", len(cases))
top_col_2.metric("Core logic", "Rules-first")
top_col_3.metric("Human-in-the-loop", "Required")

st.markdown(
    "`ingest_case -> load_rules -> validate_case -> determine_status -> prepare_*_packet -> human_review -> finalize_handoff`"
)
st.caption("Administrative workflow only. No diagnosis, treatment, or medical necessity decisions.")

with st.expander("Mock case payload", expanded=True):
    st.json(selected_case)

run_col, sample_col = st.columns([2, 1])
with run_col:
    if st.button("Run automated readiness review", width="stretch"):
        run_result = start_case_review(selected_case_id)
        st.session_state["thread_id"] = run_result["thread_id"]
        st.session_state["review_state"] = run_result["state"]
        st.session_state.pop("final_state", None)

with sample_col:
    st.info(
        "Expected review outcomes:\n"
        f"- {case_ids[0]} -> READY\n"
        f"- {case_ids[1]} -> MISSING_INFO\n"
        f"- {case_ids[2]} -> ESCALATE_TO_HUMAN"
    )

review_state = st.session_state.get("review_state")
if review_state:
    automated_status = review_state.get("automated_status", "READY")
    missing_count = len(review_state.get("missing_items", []))

    status_col_1, status_col_2, status_col_3 = st.columns(3)
    status_col_1.metric("Automated classification", automated_status)
    status_col_2.metric("Missing items", missing_count)
    status_col_3.metric("Human-in-the-loop required", "Yes" if review_state.get("human_review_required") else "No")

    st.write(STATUS_COPY[automated_status])

    if review_state.get("escalation_reason"):
        st.warning(f"Manual-handling trigger: {review_state['escalation_reason']}")

    automated_col, trace_col = st.columns(2)

    with automated_col:
        st.subheader("Validation checks")
        render_validation_results(review_state)

        st.subheader("Missing items for handoff")
        if review_state.get("missing_items"):
            st.json(review_state["missing_items"])
        else:
            st.success("No missing fields or attachments were identified under the configured rules.")

    with trace_col:
        st.subheader("Workflow trace")
        render_trace_log(review_state)

    st.subheader("Human-in-the-loop review")
    default_label = default_decision_label(automated_status)
    default_index = list(DECISION_OPTIONS.keys()).index(default_label)
    decision_label = st.radio(
        "Reviewer decision",
        options=list(DECISION_OPTIONS.keys()),
        index=default_index,
        horizontal=True,
        help="This explicit reviewer checkpoint is required before the final handoff summary is created.",
    )
    decision_action = DECISION_OPTIONS[decision_label]

    rationale = st.text_area(
        "Reviewer rationale",
        value=build_default_rationale(review_state, decision_action),
        height=100,
        help="Explain why the case should proceed as READY, MISSING_INFO, or ESCALATE_TO_HUMAN.",
    )

    if st.button("Apply reviewer decision and finalize handoff", type="primary", width="stretch"):
        human_decision = {
            "action": decision_action,
            "reviewer": "Mock Operations Reviewer",
            "rationale": rationale.strip() or build_default_rationale(review_state, decision_action),
        }
        final_state = resume_case_review(st.session_state["thread_id"], human_decision)
        st.session_state["final_state"] = final_state

final_state = st.session_state.get("final_state")
if final_state and final_state.get("final_handoff_summary"):
    handoff = final_state["final_handoff_summary"]
    st.subheader("Final handoff summary")
    final_status = handoff["readiness_status"]

    if final_status == "READY":
        st.success(handoff["summary_paragraph"])
    elif final_status == "MISSING_INFO":
        st.warning(handoff["summary_paragraph"])
    else:
        st.error(handoff["summary_paragraph"])

    artifact_col, trace_col = st.columns(2)
    with artifact_col:
        st.json(handoff)
    with trace_col:
        st.subheader("Final workflow trace")
        render_trace_log(final_state)
