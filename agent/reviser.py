"""Conclusion revision step."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _fallback_revision(state: dict[str, Any]) -> dict[str, str]:
    return {
        "final_conclusion": (
            "Therapy X does not yet show convincing evidence of broad benefit in Cancer Y. The synthetic "
            "documents support a cautious, low-confidence interpretation: there is an early response signal "
            "from a small uncontrolled study, mechanistic plausibility from preclinical work, and possible "
            "benefit in Marker Z-positive patients. Against that, the randomized full-population study found "
            "no overall survival benefit, the subgroup result is retrospective, and the preclinical mechanism "
            "has not been clinically validated. The most defensible conclusion is that Therapy X warrants "
            "further biomarker-guided investigation rather than claims of established clinical benefit."
        ),
        "confidence": "low",
    }


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
