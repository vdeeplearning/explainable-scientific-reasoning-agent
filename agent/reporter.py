"""Build the final explainable report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.llm import call_openai_json


def _fallback_report(state: dict[str, Any]) -> dict[str, Any]:
    workflow_steps = [
        "load_documents",
        "extract_claims",
        "compare_evidence",
        "draft_conclusion",
        "critique_conclusion",
    ]
    if state.get("revision_needed"):
        workflow_steps.append("revise_conclusion")
    workflow_steps.append("final_explainable_report")

    return {
        "question": state.get("question", ""),
        "final_conclusion": state.get("final_conclusion", ""),
        "confidence": state.get("confidence", "low"),
        "evidence_for": state.get("evidence_for", []),
        "evidence_against": state.get("evidence_against", []),
        "conflicts_detected": state.get("conflicts", []),
        "uncertainty_sources": state.get("uncertainty_sources", []),
        "critique_of_initial_answer": state.get("critique", {}),
        "audit_trail": {
            "documents_loaded": len(state.get("documents", [])),
            "claims_extracted": len(state.get("claims", [])),
            "workflow_steps": workflow_steps,
            "llm_used_for": [
                "claim_extraction",
                "drafting",
                "critique",
                "revision",
                "report_generation",
            ],
        },
        "demo_data_notice": "All documents are synthetic demo data and are not real medical or scientific evidence.",
    }


def final_explainable_report(state: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback_report(state)
    result = call_openai_json(
        system_prompt=(
            "Create the final explainable scientific reasoning report as JSON. Preserve the requested schema, "
            "include evidence for and against, conflicts, uncertainty, critique, and audit trail."
        ),
        user_prompt=json.dumps(fallback, indent=2),
        fallback=fallback,
    )

    if not isinstance(result, dict):
        result = fallback

    result.setdefault("demo_data_notice", fallback["demo_data_notice"])
    state["explainability_report"] = result
    return state


def save_report(report: dict[str, Any], output_path: Path | str = "outputs/reasoning_report.json") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path
