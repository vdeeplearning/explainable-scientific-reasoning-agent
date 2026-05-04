"""Evidence comparison, conflict detection, and uncertainty tracking."""

from __future__ import annotations

from typing import Any


def compare_evidence(state: dict[str, Any]) -> dict[str, Any]:
    evidence_for = []
    evidence_against = []
    uncertainty_sources = []

    for claim in state.get("claims", []):
        claim_type = claim.get("claim_type", "")
        source = claim.get("source", "")
        text = claim.get("claim", "")
        limitation = claim.get("limitation", "")

        if claim_type in {"supportive", "conditional", "mechanistic"}:
            evidence_for.append(
                {
                    "source": source,
                    "claim": text,
                    "why_it_matters": _why_support_matters(claim_type),
                }
            )

        if claim_type == "opposing" or "not improve overall survival" in text.lower():
            evidence_against.append(
                {
                    "source": source,
                    "claim": text,
                    "why_it_matters": "Directly challenges a broad conclusion that Therapy X benefits all Cancer Y patients.",
                }
            )

        if limitation:
            uncertainty_sources.append(f"{source}: {limitation}")

    conflicts = _detect_conflicts(state.get("claims", []))

    state["evidence_for"] = evidence_for
    state["evidence_against"] = evidence_against
    state["conflicts"] = conflicts
    state["uncertainty_sources"] = uncertainty_sources
    return state


def _why_support_matters(claim_type: str) -> str:
    if claim_type == "conditional":
        return "Suggests benefit may depend on biomarker status rather than applying to all patients."
    if claim_type == "mechanistic":
        return "Provides biological plausibility but does not establish clinical effectiveness."
    return "Shows an early efficacy signal that warrants comparison against stronger studies."


def _detect_conflicts(claims: list[dict[str, Any]]) -> list[str]:
    claim_types = {claim.get("claim_type", "") for claim in claims}
    conflicts = []
    if "supportive" in claim_types and "opposing" in claim_types:
        conflicts.append(
            "Supportive evidence appears alongside opposing evidence, so the conclusion should avoid a one-sided interpretation."
        )
    if "conditional" in claim_types and "supportive" in claim_types:
        conflicts.append(
            "Some evidence suggests a conditional or subgroup-specific effect, which may limit broad claims of benefit."
        )
    if "mechanistic" in claim_types and ("supportive" in claim_types or "opposing" in claim_types):
        conflicts.append(
            "Mechanistic or preclinical evidence supports plausibility but does not resolve the clinical evidence question."
        )

    if not conflicts and len(claims) > 1:
        conflicts.append(
            "Multiple documents contribute different claims; reviewers should compare study design, population, and limitations before drawing a firm conclusion."
        )

    return conflicts
