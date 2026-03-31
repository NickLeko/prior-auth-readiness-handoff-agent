import pytest

from src.graph import run_case_with_decision, start_case_review
from src.utils import default_human_decision_for_case


def test_human_reviewer_can_override_ready_case_to_escalation() -> None:
    final_state = run_case_with_decision(
        "case_001",
        {
            "action": "ESCALATE",
            "reviewer": "Mock Operations Reviewer",
            "rationale": "Manual handling is preferred for this portfolio demo override.",
        },
    )

    handoff = final_state["final_handoff_summary"]
    assert handoff["automated_status"] == "READY"
    assert handoff["readiness_status"] == "ESCALATE_TO_HUMAN"
    assert handoff["human_review_decision"]["action"] == "ESCALATE"
    assert handoff["escalation_reason"] == "Human reviewer requested manual handling."


def test_missing_info_case_keeps_expected_missing_items_order() -> None:
    final_state = run_case_with_decision("case_002", default_human_decision_for_case("case_002"))

    handoff = final_state["final_handoff_summary"]
    assert handoff["readiness_status"] == "MISSING_INFO"
    assert handoff["human_review_decision"]["action"] == "CONFIRM_MISSING_INFO"
    assert [item["label"] for item in handoff["missing_items"]] == [
        "Clinical notes flag",
        "PT referral attachment",
        "Supporting clinical notes attachment",
    ]


def test_unknown_case_id_fails_safely() -> None:
    with pytest.raises(KeyError):
        start_case_review("case_999")
