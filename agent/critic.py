"""Critique the initial conclusion for overclaiming and omissions."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _local_critique(state: dict[str, Any]) -> dict[str, Any]:
    draft = state.get("draft_conclusion", "").lower()
    evidence_against = state.get("evidence_against", [])
    conflicts = state.get("conflicts", [])
    uncertainty_sources = state.get("uncertainty_sources", [])
    claims = state.get("claims", [])
    critique = {
        "overclaims": [],
        "missing_evidence": [],
        "ignored_conflicts": [],
        "revision_needed": False,
    }
    draft_terms = _important_terms(draft)

    mixed_evidence = bool(evidence_against or conflicts)
    if mixed_evidence and any(term in draft for term in ("convincing", "strong", "established", "definitive")):
        critique["overclaims"].append("Draft may overstate evidence despite opposing or conflicting findings.")
    if evidence_against and not any(_important_terms(item.get("claim", "")) & draft_terms for item in evidence_against):
        critique["missing_evidence"].append("Draft should mention the main evidence against the conclusion.")
    if _has_uncertainty_term(uncertainty_sources, ("small", "sample")) and "small" not in draft and "sample" not in draft:
        critique["missing_evidence"].append("Draft should mention the small sample size limitation.")
    if _has_uncertainty_term(uncertainty_sources, ("retrospective", "hypothesis-generating")) and "retrospective" not in draft:
        critique["missing_evidence"].append("Draft should mention retrospective or hypothesis-generating limitations.")
    if _has_conditional_claim(claims) and not any(term in draft for term in ("marker", "biomarker", "subgroup", "conditional")):
        critique["missing_evidence"].append("Draft should mention that evidence may be subgroup-specific.")
    if conflicts and "conflict" not in draft:
        critique["ignored_conflicts"].append("Draft does not explicitly acknowledge conflicts across studies.")
    if mixed_evidence and state.get("draft_confidence") in {"moderate", "high"}:
        critique["overclaims"].append("Confidence may be too high for mixed evidence.")

    critique["revision_needed"] = any(
        critique[key] for key in ("overclaims", "missing_evidence", "ignored_conflicts")
    )
    return critique


def _important_terms(text: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "did",
        "for",
        "in",
        "is",
        "not",
        "of",
        "or",
        "the",
        "to",
        "with",
    }
    return {word.strip(".,:;()[]").lower() for word in text.split() if len(word) > 5 and word.lower() not in stop_words}


def _has_uncertainty_term(uncertainty_sources: list[str], terms: tuple[str, ...]) -> bool:
    joined = " ".join(uncertainty_sources).lower()
    return any(term in joined for term in terms)


def _has_conditional_claim(claims: list[dict[str, Any]]) -> bool:
    return any(claim.get("claim_type") == "conditional" for claim in claims)


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
