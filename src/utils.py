from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.models import HumanDecision


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT_DIR / "data" / "sample_cases.json"
DEFAULT_RULES_PATH = ROOT_DIR / "data" / "rules.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "outputs"


def resolve_path(raw_path: str | None, default_path: Path) -> Path:
    return Path(raw_path) if raw_path else default_path


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_thread_id(case_id: str) -> str:
    return f"{case_id}-{uuid4().hex[:8]}"


def default_human_decision_for_case(case_id: str) -> HumanDecision:
    decisions: dict[str, HumanDecision] = {
        "case_001": {
            "action": "APPROVE_READY",
            "reviewer": "Mock Operations Reviewer",
            "rationale": "Packet is complete and ready for payer submission after coordinator sign-off.",
        },
        "case_002": {
            "action": "CONFIRM_MISSING_INFO",
            "reviewer": "Mock Operations Reviewer",
            "rationale": "Supporting notes and the PT referral should be collected before submission.",
        },
        "case_003": {
            "action": "ESCALATE",
            "reviewer": "Mock Operations Reviewer",
            "rationale": "Urgent contrast imaging for this payer is configured for manual handling.",
        },
    }
    return decisions[case_id]
