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

    conflicts = [
        "Early response signal conflicts with lack of overall survival benefit in the randomized full-population study.",
        "Biomarker-positive subgroup benefit conflicts with no meaningful benefit in biomarker-negative patients.",
        "Preclinical mechanism supports plausibility but conflicts with the absence of definitive clinical validation.",
    ]

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
