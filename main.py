"""CLI entrypoint for the Explainable Scientific Reasoning Agent."""

from __future__ import annotations

import argparse
from typing import Any

from agent.reporter import save_report
from agent.workflow import DEFAULT_QUESTION, run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a multi-document explainable scientific reasoning demo."
    )
    parser.add_argument(
        "--question",
        default=DEFAULT_QUESTION,
        help="Scientific question to evaluate.",
    )
    return parser.parse_args()


def print_report_summary(report: dict[str, Any]) -> None:
    print("\nFinal conclusion")
    print("----------------")
    print(report.get("final_conclusion", ""))

    print(f"\nConfidence: {report.get('confidence', 'low')}")

    print("\nEvidence for")
    print("------------")
    for item in report.get("evidence_for", []):
        print(f"- {item.get('source')}: {item.get('claim')}")
        print(f"  Why it matters: {item.get('why_it_matters')}")

    print("\nEvidence against")
    print("----------------")
    for item in report.get("evidence_against", []):
        print(f"- {item.get('source')}: {item.get('claim')}")
        print(f"  Why it matters: {item.get('why_it_matters')}")

    print("\nConflicts")
    print("---------")
    for conflict in report.get("conflicts_detected", []):
        print(f"- {conflict}")

    print("\nUncertainty sources")
    print("-------------------")
    for source in report.get("uncertainty_sources", []):
        print(f"- {source}")

    critique = report.get("critique_of_initial_answer", {})
    print(f"\nRevision needed: {critique.get('revision_needed', False)}")


def main() -> None:
    args = parse_args()
    state = run_workflow(args.question)
    report = state["explainability_report"]
    output_path = save_report(report)
    print_report_summary(report)
    print(f"\nSaved report to: {output_path}")


if __name__ == "__main__":
    main()
