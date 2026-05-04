"""Initial conclusion drafting."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _fallback_draft(state: dict[str, Any]) -> dict[str, str]:
    question = state.get("question", "the question")
    evidence_for = state.get("evidence_for", [])
    evidence_against = state.get("evidence_against", [])
    conflicts = state.get("conflicts", [])
    uncertainty_sources = state.get("uncertainty_sources", [])

    if evidence_against or conflicts:
        supporting = _join_claims(evidence_for)
        opposing = _join_claims(evidence_against)
        return {
            "draft_conclusion": (
                f"For the question '{question}', the evidence is mixed. Supporting evidence includes: "
                f"{supporting}. Evidence against includes: {opposing}. The conclusion should remain cautious "
                "because several limitations or unresolved issues are present."
            ),
            "confidence": "low",
        }

    if evidence_for:
        supporting = _join_claims(evidence_for)
        limitation_text = (
            f" Remaining limitations include: {'; '.join(uncertainty_sources)}"
            if uncertainty_sources
            else " No major limitations were detected by the local fallback."
        )
        return {
            "draft_conclusion": (
                f"For the question '{question}', the available documents support a moderate-confidence conclusion. "
                f"The main supporting evidence is: {supporting}.{limitation_text}"
            ),
            "confidence": "moderate",
        }

    return {
        "draft_conclusion": (
            f"For the question '{question}', the available documents do not provide enough extracted evidence "
            "to support a confident conclusion."
        ),
        "confidence": "low",
    }


def _join_claims(items: list[dict[str, Any]]) -> str:
    if not items:
        return "none identified"
    return "; ".join(f"{item.get('source', 'unknown')}: {item.get('claim', '')}" for item in items)


def draft_conclusion(state: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback_draft(state)
    result = call_openai_json(
        system_prompt=(
            "Draft a cautious scientific conclusion from evidence_for, evidence_against, conflicts, "
            "and uncertainty_sources. Return JSON with draft_conclusion and confidence."
        ),
        user_prompt=json.dumps(
            {
                "question": state.get("question"),
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

    state["draft_conclusion"] = result.get("draft_conclusion", fallback["draft_conclusion"])
    state["draft_confidence"] = result.get("confidence", fallback["confidence"])
    return state
