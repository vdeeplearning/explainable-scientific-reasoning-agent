"""Initial conclusion drafting."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _fallback_draft(state: dict[str, Any]) -> dict[str, str]:
    return {
        "draft_conclusion": (
            "Therapy X shows some evidence of benefit in Cancer Y, including an early response signal, "
            "subgroup benefit in Marker Z-positive patients, and preclinical support. However, the evidence "
            "is not yet convincing for the overall Cancer Y population because a randomized study found no "
            "overall survival benefit and several findings remain limited or hypothesis-generating."
        ),
        "confidence": "low",
    }


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
