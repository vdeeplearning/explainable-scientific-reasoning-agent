"""LangGraph-style state workflow implemented with plain Python functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.claim_extractor import extract_claims
from agent.critic import critique_conclusion
from agent.drafter import draft_conclusion
from agent.evidence_comparator import compare_evidence
from agent.loader import load_documents
from agent.reporter import final_explainable_report
from agent.reviser import revise_conclusion


DEFAULT_QUESTION = "Does Therapy X show convincing evidence of benefit in Cancer Y?"


def initial_state(question: str = DEFAULT_QUESTION) -> dict[str, Any]:
    return {
        "question": question,
        "documents": [],
        "document_insights": [],
        "claims": [],
        "evidence_for": [],
        "evidence_against": [],
        "conflicts": [],
        "uncertainty_sources": [],
        "draft_conclusion": "",
        "critique": {},
        "revision_needed": False,
        "final_conclusion": "",
        "explainability_report": {},
    }


def run_workflow(
    question: str = DEFAULT_QUESTION,
    document_paths: list[Path | str] | None = None,
) -> dict[str, Any]:
    state = initial_state(question)

    state = load_documents(state, file_paths=document_paths)
    state = extract_claims(state)
    state = compare_evidence(state)
    state = draft_conclusion(state)
    state = critique_conclusion(state)

    if state.get("revision_needed"):
        state = revise_conclusion(state)
    else:
        state["final_conclusion"] = state.get("draft_conclusion", "")
        state["confidence"] = state.get("draft_confidence", "low")

    state = final_explainable_report(state)
    return state
