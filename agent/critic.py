"""Critique the initial conclusion for overclaiming and omissions."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _local_critique(state: dict[str, Any]) -> dict[str, Any]:
    draft = state.get("draft_conclusion", "").lower()
    critique = {
        "overclaims": [],
        "missing_evidence": [],
        "ignored_conflicts": [],
        "revision_needed": False,
    }

    if "convincing" in draft or "strong" in draft or "broad clinical adoption" in draft:
        critique["overclaims"].append("Draft may overstate evidence despite no overall survival benefit.")
    if "overall survival" not in draft:
        critique["missing_evidence"].append("Draft should mention the randomized study found no overall survival benefit.")
    if "small" not in draft and "sample" not in draft:
        critique["missing_evidence"].append("Draft should mention the small single-arm sample size limitation.")
    if "marker z" not in draft and "biomarker" not in draft and "subgroup" not in draft:
        critique["missing_evidence"].append("Draft should mention that evidence may be subgroup-specific.")
    if "conflict" not in draft and state.get("conflicts"):
        critique["ignored_conflicts"].append("Draft does not explicitly acknowledge conflicts across studies.")
    if state.get("draft_confidence") in {"moderate", "high"}:
        critique["overclaims"].append("Confidence may be too high for mixed synthetic evidence.")

    critique["revision_needed"] = any(
        critique[key] for key in ("overclaims", "missing_evidence", "ignored_conflicts")
    )
    return critique


def critique_conclusion(state: dict[str, Any]) -> dict[str, Any]:
    fallback = _local_critique(state)
    result = call_openai_json(
        system_prompt=(
            "Critique the draft conclusion. Check overstatement, ignored conflicting findings, omitted "
            "limitations, missing subgroup-specific evidence, and excessive confidence. Return JSON with "
            "overclaims, missing_evidence, ignored_conflicts, and revision_needed."
        ),
        user_prompt=json.dumps(
            {
                "question": state.get("question"),
                "draft_conclusion": state.get("draft_conclusion"),
                "draft_confidence": state.get("draft_confidence"),
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

    for key in ("overclaims", "missing_evidence", "ignored_conflicts"):
        result.setdefault(key, [])
    result["revision_needed"] = any(result[key] for key in ("overclaims", "missing_evidence", "ignored_conflicts"))

    state["critique"] = result
    state["revision_needed"] = result["revision_needed"]
    return state
