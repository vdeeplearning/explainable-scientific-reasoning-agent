"""Document loading for scientific snippets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_documents(
    state: dict[str, Any],
    docs_dir: Path | str = "documents/demo_set_01",
    file_paths: list[Path | str] | None = None,
) -> dict[str, Any]:
    documents = []
    paths = [Path(file_path) for file_path in file_paths] if file_paths else sorted(Path(docs_dir).glob("*.txt"))

    for file_path in paths:
        documents.append(
            {
                "source": file_path.name,
                "path": str(file_path),
                "text": file_path.read_text(encoding="utf-8").strip(),
                "synthetic_demo_data": "demo_set_01" in file_path.parts,
            }
        )

    state["documents"] = documents
    state.setdefault("audit_trail", {})
    state["audit_trail"]["documents_loaded"] = len(documents)
    return state
