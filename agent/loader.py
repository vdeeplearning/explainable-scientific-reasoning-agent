"""Document loading for synthetic scientific snippets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_documents(state: dict[str, Any], docs_dir: Path | str = "documents/demo_set_01") -> dict[str, Any]:
    path = Path(docs_dir)
    documents = []

    for file_path in sorted(path.glob("*.txt")):
        documents.append(
            {
                "source": file_path.name,
                "path": str(file_path),
                "text": file_path.read_text(encoding="utf-8").strip(),
                "synthetic_demo_data": True,
            }
        )

    state["documents"] = documents
    state.setdefault("audit_trail", {})
    state["audit_trail"]["documents_loaded"] = len(documents)
    return state
