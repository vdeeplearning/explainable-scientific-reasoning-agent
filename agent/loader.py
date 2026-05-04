"""Document loading for scientific documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".txt", ".pdf"}


def load_documents(
    state: dict[str, Any],
    docs_dir: Path | str = "documents/demo_set_01",
    file_paths: list[Path | str] | None = None,
) -> dict[str, Any]:
    documents = []
    paths = [Path(file_path) for file_path in file_paths] if file_paths else sorted(Path(docs_dir).glob("*.txt"))

    for file_path in paths:
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        documents.append(
            {
                "source": file_path.name,
                "path": str(file_path),
                "text": read_document_text(file_path),
                "file_type": file_path.suffix.lower().lstrip("."),
                "synthetic_demo_data": "demo_set_01" in file_path.parts,
            }
        )

    state["documents"] = documents
    state.setdefault("audit_trail", {})
    state["audit_trail"]["documents_loaded"] = len(documents)
    return state


def read_document_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8").strip()
    if suffix == ".pdf":
        return read_pdf_text(file_path)
    raise ValueError(f"Unsupported document type: {file_path.suffix}")


def read_pdf_text(file_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF support requires pypdf. Install dependencies with: pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(str(file_path))
    page_text = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            page_text.append(f"[Page {page_number}]\n{text.strip()}")

    if not page_text:
        return "[No extractable text found in this PDF. Scanned PDFs may require OCR.]"
    return "\n\n".join(page_text)
