"""Claim extraction from multiple synthetic scientific documents."""

from __future__ import annotations

import json
from typing import Any

from agent.llm import call_openai_json


def _fallback_claims(documents: list[dict[str, Any]]) -> list[dict[str, str]]:
    claims_by_source = {
        "doc_01.txt": [
            {
                "source": "doc_01.txt",
                "claim": "Therapy X produced a 44% objective response rate in a small single-arm Cancer Y study.",
                "claim_type": "supportive",
                "limitation": "Small sample size, no control arm, and short follow-up.",
            }
        ],
        "doc_02.txt": [
            {
                "source": "doc_02.txt",
                "claim": "Therapy X did not improve overall survival in the full randomized Cancer Y population.",
                "claim_type": "opposing",
                "limitation": "Progression-free survival was numerically higher but not statistically significant.",
            }
        ],
        "doc_03.txt": [
            {
                "source": "doc_03.txt",
                "claim": "Therapy X may benefit Marker Z-positive Cancer Y patients but not biomarker-negative patients.",
                "claim_type": "conditional",
                "limitation": "Retrospective subgroup analysis and hypothesis-generating evidence.",
            }
        ],
        "doc_04.txt": [
            {
                "source": "doc_04.txt",
                "claim": "Preclinical Cancer Y models support Therapy X's Target Q mechanism, especially with Marker Z expression.",
                "claim_type": "mechanistic",
                "limitation": "Preclinical findings are not clinical validation.",
            }
        ],
    }

    claims: list[dict[str, str]] = []
    for document in documents:
        source = document["source"]
        known_claims = claims_by_source.get(source)
        if known_claims:
            claims.extend(known_claims)
        else:
            claims.append(_heuristic_claim(document))
    return claims


def _heuristic_claim(document: dict[str, Any]) -> dict[str, str]:
    text = document.get("text", "")
    lower_text = text.lower()
    first_sentence = _first_sentence(text)

    if any(term in lower_text for term in ("no benefit", "did not", "not statistically", "failed")):
        claim_type = "opposing"
    elif any(term in lower_text for term in ("subgroup", "biomarker", "marker", "only in")):
        claim_type = "conditional"
    elif any(term in lower_text for term in ("preclinical", "mechanism", "cell", "mouse", "pathway")):
        claim_type = "mechanistic"
    else:
        claim_type = "supportive"

    limitation_terms = []
    for term in ("small", "retrospective", "preclinical", "uncontrolled", "short follow-up", "not validated"):
        if term in lower_text:
            limitation_terms.append(term)
    limitation = (
        f"Potential limitation signals detected: {', '.join(limitation_terms)}."
        if limitation_terms
        else "Limitations require reviewer assessment; local fallback detected no explicit limitation keywords."
    )

    return {
        "source": document.get("source", "uploaded_document"),
        "claim": first_sentence or "The uploaded document contains scientific evidence relevant to the question.",
        "claim_type": claim_type,
        "limitation": limitation,
    }


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    for delimiter in (". ", "? ", "! "):
        if delimiter in cleaned:
            return cleaned.split(delimiter, 1)[0].strip() + delimiter.strip()
    return cleaned[:240]


def _document_insights(documents: list[dict[str, Any]], claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    insights = []
    for document in documents:
        source = document.get("source", "")
        related_claims = [claim for claim in claims if claim.get("source") == source]
        stance_counts: dict[str, int] = {}
        limitations = []
        for claim in related_claims:
            claim_type = claim.get("claim_type", "unknown")
            stance_counts[claim_type] = stance_counts.get(claim_type, 0) + 1
            if claim.get("limitation"):
                limitations.append(claim["limitation"])

        insights.append(
            {
                "source": source,
                "agent_thinks": _summarize_document_view(source, related_claims, stance_counts, limitations),
                "claims": related_claims,
                "stance_counts": stance_counts,
                "limitations": limitations,
            }
        )
    return insights


def _summarize_document_view(
    source: str,
    claims: list[dict[str, Any]],
    stance_counts: dict[str, int],
    limitations: list[str],
) -> str:
    if not claims:
        return f"{source}: No claim was extracted. The document may need manual review or a stronger LLM pass."

    dominant_stance = max(stance_counts, key=stance_counts.get)
    limitation_text = limitations[0] if limitations else "No explicit limitation was captured."
    return (
        f"{source}: The agent reads this as {dominant_stance} evidence. "
        f"Main claim: {claims[0].get('claim', '')} "
        f"Key limitation: {limitation_text}"
    )


def extract_claims(state: dict[str, Any]) -> dict[str, Any]:
    documents = state.get("documents", [])
    fallback = {"claims": _fallback_claims(documents)}
    document_payload = json.dumps(documents, indent=2)

    result = call_openai_json(
        system_prompt=(
            "Extract concise scientific claims from scientific documents. "
            "Return JSON only with a top-level claims array. Each claim must include "
            "source, claim, claim_type, and limitation."
        ),
        user_prompt=f"Documents:\n{document_payload}",
        fallback=fallback,
    )

    claims = result.get("claims", fallback["claims"]) if isinstance(result, dict) else fallback["claims"]
    state["claims"] = claims
    state["document_insights"] = _document_insights(documents, claims)
    state.setdefault("audit_trail", {})
    state["audit_trail"]["claims_extracted"] = len(claims)
    return state
