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
        claims.extend(claims_by_source.get(document["source"], []))
    return claims


def extract_claims(state: dict[str, Any]) -> dict[str, Any]:
    documents = state.get("documents", [])
    fallback = {"claims": _fallback_claims(documents)}
    document_payload = json.dumps(documents, indent=2)

    result = call_openai_json(
        system_prompt=(
            "Extract concise scientific claims from synthetic demo documents. "
            "Return JSON only with a top-level claims array. Each claim must include "
            "source, claim, claim_type, and limitation."
        ),
        user_prompt=f"Documents:\n{document_payload}",
        fallback=fallback,
    )

    claims = result.get("claims", fallback["claims"]) if isinstance(result, dict) else fallback["claims"]
    state["claims"] = claims
    state.setdefault("audit_trail", {})
    state["audit_trail"]["claims_extracted"] = len(claims)
    return state
