"""Conclusion revision step."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _fallback_revision(state: dict[str, Any]) -> dict[str, str]:
    question = state.get("question", "the question")
    evidence_for = state.get("evidence_for", [])
    evidence_against = state.get("evidence_against", [])
    conflicts = state.get("conflicts", [])
    uncertainty_sources = state.get("uncertainty_sources", [])
    critique = state.get("critique", {})

    supporting = _join_claims(evidence_for)
    opposing = _join_claims(evidence_against)
    conflict_text = _join_list(conflicts, "No explicit conflicts were detected.")
    uncertainty_text = _join_list(uncertainty_sources, "No major uncertainty sources were detected by the local fallback.")
    critique_text = _summarize_critique(critique)
    confidence = "low" if evidence_against or conflicts or critique_text else "moderate"

    return {
        "final_conclusion": (
            f"For the question '{question}', the revised conclusion is cautious because the initial answer "
            f"needed correction. Supporting evidence includes: {supporting}. Evidence against includes: "
            f"{opposing}. Conflicts or tensions to preserve in the answer: {conflict_text}. Uncertainty "
            f"sources include: {uncertainty_text}. Overall, the evidence should be interpreted with "
            f"{confidence} confidence rather than as a definitive answer."
        ),
        "confidence": confidence,
    }


def _join_claims(items: list[dict[str, Any]]) -> str:
    if not items:
        return "none identified"
    return "; ".join(f"{item.get('source', 'unknown')}: {item.get('claim', '')}" for item in items)


def _join_list(items: list[str], empty_text: str) -> str:
    if not items:
        return empty_text
    return "; ".join(items)


def _summarize_critique(critique: dict[str, Any]) -> str:
    critique_items = []
    for key in ("overclaims", "missing_evidence", "ignored_conflicts"):
        critique_items.extend(critique.get(key, []))
    return "; ".join(critique_items)


def revise_conclusion(state: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback_revision(state)
    result = call_openai_json(
        system_prompt=(
            "Revise the conclusion to address critique items. Be explicit about conflicts, limitations, "
            "subgroup-specific evidence, and confidence. Return JSON with final_conclusion and confidence."
        ),
        user_prompt=json.dumps(
            {
                "question": state.get("question"),
                "draft_conclusion": state.get("draft_conclusion"),
                "critique": state.get("critique"),
                "evidence_for": state.get("evidence_for"),
                "evidence_against": state.get("evidence_against"),
                "conflicts": state.get("conflicts"),
                "uncertainty_sources": state.get("uncertainty_sources"),
            },
            indent=2,
        ),
        fallback=fallback,
    )

    if not isinstance(result, dict):
        result = fallback

    state["final_conclusion"] = result.get("final_conclusion", fallback["final_conclusion"])
    state["confidence"] = result.get("confidence", fallback["confidence"])
    return state
