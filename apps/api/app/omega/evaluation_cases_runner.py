from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.omega.confirmation_policy import SENSITIVE_HINTS


def load_omega_fixture_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def run_omega_fixture_evaluation(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for case in cases:
        text = f"{case.get('input', '')} {case.get('expected_claim', '')}".lower()
        sensitive = any(hint in text for hint in SENSITIVE_HINTS)
        model_generated = case.get("provenance") == "MODEL_GENERATED"
        expected_confirmation = bool(case.get("requires_confirmation"))
        actual_confirmation = sensitive or model_generated or case.get("truth_status") == "INFERRED"
        result = {
            "id": case["id"],
            "grounded": bool(case.get("expected_claim")),
            "scope_safe": "secret" not in text or expected_confirmation,
            "confirmation_gate_correct": actual_confirmation == expected_confirmation,
            "truth_status_correct": case.get("truth_status") != "OBSERVED" or not model_generated,
            "contradiction_detected": bool(case.get("expects_contradiction")) == (
                any(marker in text for marker in ("must not", "never", "cannot", "no "))
                and "will " in text
            ),
            "prediction_resolution_correct": bool(case.get("expects_prediction_resolution")) == ("outcome:" in text or "observed:" in text),
        }
        results.append(result)
    totals = {
        key: sum(1 for row in results if row[key])
        for key in [
            "grounded",
            "scope_safe",
            "confirmation_gate_correct",
            "truth_status_correct",
            "contradiction_detected",
            "prediction_resolution_correct",
        ]
    }
    return {"case_count": len(results), "totals": totals, "results": results}
