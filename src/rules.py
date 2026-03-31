from __future__ import annotations

from typing import Any

from src.models import CaseData, MissingItem, RuleSet, ValidationResult
from src.utils import DEFAULT_CASES_PATH, DEFAULT_RULES_PATH, read_json, resolve_path


def load_sample_cases(cases_path: str | None = None) -> dict[str, CaseData]:
    data = read_json(resolve_path(cases_path, DEFAULT_CASES_PATH))
    return {item["case_id"]: item for item in data}


def load_rules_catalog(rules_path: str | None = None) -> dict[str, RuleSet]:
    return read_json(resolve_path(rules_path, DEFAULT_RULES_PATH))


def load_rule_for_case(case_data: CaseData, rules_path: str | None = None) -> RuleSet:
    rules_catalog = load_rules_catalog(rules_path)
    case_type = case_data["case_type"]
    if case_type not in rules_catalog:
        raise KeyError(f"No rule set found for case type '{case_type}'.")
    return rules_catalog[case_type]


def evaluate_validation(case_data: CaseData, rule_set: RuleSet) -> tuple[list[ValidationResult], list[MissingItem]]:
    results: list[ValidationResult] = []
    missing_items: list[MissingItem] = []

    for field_rule in rule_set.get("required_fields", []):
        key = field_rule["key"]
        label = field_rule["label"]
        must_be_truthy = bool(field_rule.get("must_be_truthy", False))
        value = case_data.get(key)
        passed = is_present(value, must_be_truthy=must_be_truthy)
        detail = "Present." if passed else "Missing or not documented."

        results.append(
            {
                "item_key": key,
                "label": label,
                "item_type": "field",
                "required": True,
                "passed": passed,
                "reason": field_rule["reason"],
                "detail": detail,
            }
        )
        if not passed:
            missing_items.append(
                {
                    "item_key": key,
                    "label": label,
                    "item_type": "field",
                    "reason": field_rule["reason"],
                }
            )

    attached_documents = set(case_data.get("attached_documents", []))
    for doc_rule in rule_set.get("required_documents", []):
        key = doc_rule["key"]
        label = doc_rule["label"]
        passed = key in attached_documents
        detail = "Attached." if passed else "Attachment missing."

        results.append(
            {
                "item_key": key,
                "label": label,
                "item_type": "document",
                "required": True,
                "passed": passed,
                "reason": doc_rule["reason"],
                "detail": detail,
            }
        )
        if not passed:
            missing_items.append(
                {
                    "item_key": key,
                    "label": label,
                    "item_type": "document",
                    "reason": doc_rule["reason"],
                }
            )

    for conditional_rule in rule_set.get("conditional_requirements", []):
        if not matches_condition(
            case_data.get(conditional_rule["when_field"]),
            conditional_rule["operator"],
            conditional_rule["value"],
        ):
            results.append(
                {
                    "item_key": conditional_rule["key"],
                    "label": conditional_rule["label"],
                    "item_type": conditional_rule.get("item_type", "field"),
                    "required": False,
                    "passed": True,
                    "reason": conditional_rule["reason"],
                    "detail": "Condition not triggered for this case.",
                }
            )
            continue

        item_type = conditional_rule.get("item_type", "field")
        key = conditional_rule["key"]
        label = conditional_rule["label"]
        if item_type == "document":
            passed = key in attached_documents
            detail = "Attached." if passed else "Attachment missing."
        else:
            passed = is_present(case_data.get(key), must_be_truthy=bool(conditional_rule.get("must_be_truthy", False)))
            detail = "Documented." if passed else "Missing or not documented."

        results.append(
            {
                "item_key": key,
                "label": label,
                "item_type": item_type,
                "required": True,
                "passed": passed,
                "reason": conditional_rule["reason"],
                "detail": detail,
            }
        )
        if not passed:
            missing_items.append(
                {
                    "item_key": key,
                    "label": label,
                    "item_type": item_type,
                    "reason": conditional_rule["reason"],
                }
            )

    return results, missing_items


def evaluate_escalation(case_data: CaseData, rule_set: RuleSet) -> list[str]:
    reasons: list[str] = []
    for condition in rule_set.get("escalation_conditions", []):
        if matches_condition(case_data.get(condition["field"]), condition["operator"], condition["value"]):
            reasons.append(condition["reason"])
    return reasons


def is_present(value: Any, *, must_be_truthy: bool = False) -> bool:
    if must_be_truthy:
        return bool(value)
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def matches_condition(actual_value: Any, operator: str, expected_value: Any) -> bool:
    if operator == "equals":
        return actual_value == expected_value
    if operator == "not_equals":
        return actual_value != expected_value
    if operator == "in":
        return actual_value in expected_value
    raise ValueError(f"Unsupported operator: {operator}")
