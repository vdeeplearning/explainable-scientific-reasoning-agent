"""LangGraph workflow for explainable scientific reasoning."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.claim_extractor import extract_claims
from agent.critic import critique_conclusion
from agent.drafter import draft_conclusion
from agent.evidence_comparator import compare_evidence
from agent.loader import load_documents
from agent.reporter import final_explainable_report
from agent.reviser import revise_conclusion


DEFAULT_QUESTION = "Does Therapy X show convincing evidence of benefit in Cancer Y?"


class ReasoningState(TypedDict, total=False):
    question: str
    document_paths: list[Path | str]
    documents: list[dict[str, Any]]
    document_insights: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    evidence_for: list[dict[str, Any]]
    evidence_against: list[dict[str, Any]]
    conflicts: list[str]
    uncertainty_sources: list[str]
    draft_conclusion: str
    draft_confidence: str
    critique: dict[str, Any]
    revision_needed: bool
    final_conclusion: str
    confidence: str
    explainability_report: dict[str, Any]


def initial_state(
    question: str = DEFAULT_QUESTION,
    document_paths: list[Path | str] | None = None,
) -> ReasoningState:
    return {
        "question": question,
        "document_paths": document_paths or [],
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


def load_documents_node(state: ReasoningState) -> ReasoningState:
    return load_documents(state, file_paths=state.get("document_paths") or None)


def use_draft_as_final(state: ReasoningState) -> ReasoningState:
    state["final_conclusion"] = state.get("draft_conclusion", "")
    state["confidence"] = state.get("draft_confidence", "low")
    return state


def route_after_critique(state: ReasoningState) -> str:
    return "revise" if state.get("revision_needed") else "skip_revision"


def build_reasoning_graph():
    graph = StateGraph(ReasoningState)
    graph.add_node("load_documents", load_documents_node)
    graph.add_node("extract_claims", extract_claims)
    graph.add_node("compare_evidence", compare_evidence)
    graph.add_node("draft_conclusion", draft_conclusion)
    graph.add_node("critique_conclusion", critique_conclusion)
    graph.add_node("revise_conclusion", revise_conclusion)
    graph.add_node("use_draft_as_final", use_draft_as_final)
    graph.add_node("final_explainable_report", final_explainable_report)

    graph.add_edge(START, "load_documents")
    graph.add_edge("load_documents", "extract_claims")
    graph.add_edge("extract_claims", "compare_evidence")
    graph.add_edge("compare_evidence", "draft_conclusion")
    graph.add_edge("draft_conclusion", "critique_conclusion")
    graph.add_conditional_edges(
        "critique_conclusion",
        route_after_critique,
        {
            "revise": "revise_conclusion",
            "skip_revision": "use_draft_as_final",
        },
    )
    graph.add_edge("revise_conclusion", "final_explainable_report")
    graph.add_edge("use_draft_as_final", "final_explainable_report")
    graph.add_edge("final_explainable_report", END)

    return graph.compile()


REASONING_GRAPH = build_reasoning_graph()


def run_workflow(
    question: str = DEFAULT_QUESTION,
    document_paths: list[Path | str] | None = None,
) -> dict[str, Any]:
    state = initial_state(question, document_paths=document_paths)
    return dict(REASONING_GRAPH.invoke(state))
