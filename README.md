# Explainable Scientific Reasoning Agent

A Python 3.11+ CLI and desktop GUI demo for multi-document scientific reasoning over scientific text snippets.

The project reads several short scientific document snippets, extracts key claims, compares evidence across documents, detects conflicts, tracks uncertainty, drafts a conclusion, critiques that conclusion, revises it when needed, and produces an explainable JSON report. The GUI lets users upload their own `.txt` or `.pdf` documents and inspect what the agent thinks at each intermediate step.

## Disclaimer

All included documents are synthetic demo data about a fictional oncology treatment called Therapy X for fictional Cancer Y. They are not real medical or scientific evidence. This project is for software demonstration only and is not medical, scientific, clinical, or research advice.

## Why This Is Different From RAG

This is not a generic retrieval-augmented generation chatbot. The demo does not simply retrieve snippets and ask a model to answer from them. Instead, it makes the reasoning process explicit:

- extracts claims from each document
- separates evidence for and against the question
- detects conflicts across studies
- tracks uncertainty and limitations
- drafts an answer
- critiques the answer for overclaiming and omissions
- revises the conclusion when the critique finds problems
- emits an audit trail and explainability report

## Workflow

```text
load_documents
  -> extract_claims
  -> compare_evidence
  -> draft_conclusion
  -> critique_conclusion
  -> [revision_needed?]
       -> yes: revise_conclusion
       -> no:  use draft conclusion
  -> final_explainable_report
```

The workflow is implemented in plain Python with a LangGraph-style state object, so it can be ported to LangGraph later without changing the conceptual design.

## Critique Loop

The critic checks whether the draft conclusion:

- overstates the evidence
- ignores conflicting findings
- omits limitations
- fails to mention subgroup-specific evidence
- assigns too much confidence

If any critique list is non-empty, `revision_needed` is set to `true` and the workflow runs `revise_conclusion`. The revised conclusion is expected to be more cautious, more explicit about uncertainty, and better aligned with the evidence comparison.

## Explainability Report

The final report is saved to `outputs/reasoning_report.json` and includes:

- the question
- final conclusion
- confidence level
- evidence for
- evidence against
- conflicts detected
- uncertainty sources
- critique of the initial answer
- audit trail with documents loaded, claims extracted, workflow steps, and LLM usage categories

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the environment with:

```powershell
.\venv\Scripts\Activate.ps1
```

Add your OpenAI API key to `.env` if you want live LLM-backed JSON outputs:

```text
OPENAI_API_KEY=your_api_key_here
```

If no API key is present, the project falls back to deterministic local mock outputs so the demo still runs.

## Run

Launch the GUI:

```bash
python gui.py
```

In the GUI, you can:

- add your own `.txt` documents
- add PDFs with extractable text
- fall back to the built-in synthetic demo set
- edit the scientific question
- run the reasoning workflow
- inspect document-level agent thoughts, extracted claims, evidence comparison, draft, critique, revision, and raw JSON

PDF support uses `pypdf` to extract embedded text. Scanned image-only PDFs may show no extractable text and are a good candidate for a future OCR extension.

Run the CLI:

```bash
python main.py --question "Does Therapy X show convincing evidence of benefit in Cancer Y?"
```

You can also run with the default question:

```bash
python main.py
```

The CLI prints:

- final conclusion
- confidence
- evidence for
- evidence against
- conflicts
- uncertainty sources
- whether revision was needed

The full JSON report is saved to:

```text
outputs/reasoning_report.json
```

## Project Structure

```text
explainable-scientific-reasoning-agent/
  documents/
    demo_set_01/
      doc_01.txt
      doc_02.txt
      doc_03.txt
      doc_04.txt
  agent/
    __init__.py
    loader.py
    claim_extractor.py
    evidence_comparator.py
    drafter.py
    critic.py
    reviser.py
    reporter.py
    workflow.py
  outputs/
  gui.py
  main.py
  requirements.txt
  README.md
  .env.example
  .gitignore
```

## Future Extensions

- real paper ingestion
- PubMed/arXiv retrieval
- citation-aware evidence tracking
- LangGraph implementation
- memory across reasoning sessions
