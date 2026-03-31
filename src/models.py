from __future__ import annotations

from typing import Any, Literal, TypedDict


ReadinessStatus = Literal["READY", "MISSING_INFO", "ESCALATE_TO_HUMAN"]
HumanReviewAction = Literal["APPROVE_READY", "CONFIRM_MISSING_INFO", "ESCALATE"]


class CaseData(TypedDict, total=False):
    case_id: str
    case_type: str
    patient_age_group: str
    service_requested: str
    ordering_provider: str
    payer: str
    diagnosis_code_present: bool
    clinical_notes_present: bool
    imaging_order_present: bool
    prior_conservative_therapy_documented: bool
    location_of_service: str
    urgency: str
    attached_documents: list[str]
    free_text_notes: str


class FieldRequirement(TypedDict, total=False):
    key: str
    label: str
    reason: str
    must_be_truthy: bool


class DocumentRequirement(TypedDict):
    key: str
    label: str
    reason: str


class ConditionalRequirement(TypedDict, total=False):
    when_field: str
    operator: str
    value: Any
    key: str
    label: str
    reason: str
    item_type: Literal["field", "document"]
    must_be_truthy: bool


class EscalationCondition(TypedDict):
    field: str
    operator: str
    value: Any
    reason: str


class RuleSet(TypedDict, total=False):
    case_type: str
    service_requested: str
    required_fields: list[FieldRequirement]
    required_documents: list[DocumentRequirement]
    conditional_requirements: list[ConditionalRequirement]
    escalation_conditions: list[EscalationCondition]


class ValidationResult(TypedDict, total=False):
    item_key: str
    label: str
    item_type: Literal["field", "document"]
    required: bool
    passed: bool
    reason: str
    detail: str


class MissingItem(TypedDict):
    item_key: str
    label: str
    item_type: Literal["field", "document"]
    reason: str


class ReviewPacket(TypedDict, total=False):
    case_id: str
    service_requested: str
    automated_status: ReadinessStatus
    missing_items: list[MissingItem]
    escalation_reason: str | None
    reviewer_prompt: str
    recommended_next_action: str


class HumanDecision(TypedDict):
    action: HumanReviewAction
    reviewer: str
    rationale: str


class TraceEntry(TypedDict, total=False):
    step_index: int
    timestamp: str
    node: str
    message: str
    status: str | None
    details: dict[str, Any]


class HandoffSummary(TypedDict, total=False):
    case_id: str
    requested_service: str
    automated_status: ReadinessStatus
    readiness_status: ReadinessStatus
    missing_items: list[MissingItem]
    escalation_reason: str | None
    human_review_decision: HumanDecision
    recommended_next_action: str
    summary_paragraph: str
    trace_log: list[TraceEntry]
