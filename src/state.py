from __future__ import annotations

from typing import TypedDict

from src.models import (
    CaseData,
    HandoffSummary,
    HumanDecision,
    MissingItem,
    ReadinessStatus,
    ReviewPacket,
    RuleSet,
    TraceEntry,
    ValidationResult,
)


class WorkflowState(TypedDict, total=False):
    case_id: str
    cases_path: str
    rules_path: str
    case_data: CaseData
    rule_set: RuleSet
    validation_results: list[ValidationResult]
    missing_items: list[MissingItem]
    automated_status: ReadinessStatus
    readiness_status: ReadinessStatus
    escalation_reason: str | None
    human_review_required: bool
    review_packet: ReviewPacket
    human_decision: HumanDecision
    final_handoff_summary: HandoffSummary
    trace_log: list[TraceEntry]
