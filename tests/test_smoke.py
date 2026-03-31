from src.graph import run_case_with_decision
from src.utils import default_human_decision_for_case


def test_sample_cases_cover_all_three_statuses() -> None:
    expected = {
        "case_001": "READY",
        "case_002": "MISSING_INFO",
        "case_003": "ESCALATE_TO_HUMAN",
    }

    observed_statuses = []
    for case_id, expected_status in expected.items():
        final_state = run_case_with_decision(case_id, default_human_decision_for_case(case_id))
        handoff = final_state["final_handoff_summary"]

        observed_statuses.append(handoff["readiness_status"])
        assert handoff["readiness_status"] == expected_status
        assert handoff["human_review_decision"]["action"]
        assert handoff["recommended_next_action"]
        assert any(entry["node"] == "human_review" for entry in handoff["trace_log"])

    assert set(observed_statuses) == {"READY", "MISSING_INFO", "ESCALATE_TO_HUMAN"}
