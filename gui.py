"""Tkinter GUI for the Explainable Scientific Reasoning Agent."""

from __future__ import annotations

import json
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from agent.loader import read_document_text
from agent.reporter import save_report
from agent.workflow import DEFAULT_QUESTION, run_workflow


class ReasoningAgentApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Explainable Scientific Reasoning Agent")
        self.geometry("1180x760")
        self.minsize(980, 640)

        self.selected_files: list[Path] = []
        self.demo_mode = "revision"
        self.result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.current_state: dict[str, Any] | None = None

        self._configure_style()
        self._build_layout()
        self._load_revision_demo_documents()
        self.after(100, self._poll_result_queue)

    def _configure_style(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f6f7f9")
        self.style.configure("Header.TLabel", background="#f6f7f9", font=("Segoe UI", 17, "bold"))
        self.style.configure("Subtle.TLabel", background="#f6f7f9", foreground="#55606d")
        self.style.configure("TButton", padding=(10, 6))
        self.style.configure("Primary.TButton", padding=(12, 7))

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=18)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Explainable Scientific Reasoning Agent", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="Upload scientific documents, run the reasoning loop, and inspect the intermediate agent state.",
            style="Subtle.TLabel",
        ).pack(anchor=tk.W, pady=(4, 12))

        content = ttk.Frame(container)
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=0, minsize=380)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_sidebar(content)
        self._build_results_area(content)

    def _build_sidebar(self, parent: ttk.Frame) -> None:
        sidebar = ttk.Frame(parent, padding=(0, 0, 14, 0))
        sidebar.grid(row=0, column=0, sticky="nsew")

        ttk.Label(sidebar, text="Question", style="Subtle.TLabel").pack(anchor=tk.W)
        self.question_text = tk.Text(sidebar, height=4, wrap=tk.WORD, font=("Segoe UI", 10))
        self.question_text.pack(fill=tk.X, pady=(4, 14))
        self.question_text.insert("1.0", DEFAULT_QUESTION)

        ttk.Label(sidebar, text="OpenAI API Key", style="Subtle.TLabel").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        self.api_key_entry = ttk.Entry(sidebar, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=(4, 6))
        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            sidebar,
            text="Show key",
            variable=self.show_key_var,
            command=self._toggle_api_key_visibility,
        ).pack(anchor=tk.W, pady=(0, 14))

        ttk.Label(sidebar, text="Documents", style="Subtle.TLabel").pack(anchor=tk.W)
        self.file_list = tk.Listbox(sidebar, height=8, activestyle="dotbox", font=("Segoe UI", 10))
        self.file_list.bind("<<ListboxSelect>>", self._show_selected_document_text)
        self.file_list.pack(fill=tk.BOTH, expand=False, pady=(4, 10))

        button_row = ttk.Frame(sidebar)
        button_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(button_row, text="Add Files", command=self._add_files).pack(side=tk.LEFT)

        demo_row = ttk.Frame(sidebar)
        demo_row.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(demo_row, text="Demo: Revision", command=self._load_revision_demo_documents).pack(side=tk.LEFT)
        ttk.Button(demo_row, text="Demo: No Revision", command=self._load_no_revision_demo_documents).pack(
            side=tk.LEFT,
            padx=(8, 0),
        )

        ttk.Button(sidebar, text="Clear Documents", command=self._clear_files).pack(fill=tk.X, pady=(0, 12))
        self.run_button = ttk.Button(
            sidebar,
            text="Run Reasoning",
            style="Primary.TButton",
            command=self._run_reasoning,
        )
        self.run_button.pack(fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            sidebar,
            textvariable=self.status_var,
            style="Subtle.TLabel",
            wraplength=340,
            justify=tk.LEFT,
        )
        self.status_label.pack(fill=tk.X, pady=(12, 0))

        disclaimer = (
            "Demo documents are synthetic. Uploaded content is analyzed only as user-provided text. "
            "This tool does not provide medical or scientific advice."
        )
        disclaimer_label = ttk.Label(
            sidebar,
            text=disclaimer,
            style="Subtle.TLabel",
            wraplength=340,
            justify=tk.LEFT,
        )
        disclaimer_label.pack(fill=tk.X, pady=(14, 0))

    def _build_results_area(self, parent: ttk.Frame) -> None:
        right = ttk.Frame(parent)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        self.tabs = ttk.Notebook(right)
        self.tabs.grid(row=0, column=0, sticky="nsew")

        self.summary_view = self._add_text_tab("Final Report")
        self.uploaded_text_view = self._add_text_tab("Uploaded Text")
        self.documents_view = self._add_text_tab("Document Thoughts")
        self.claims_view = self._add_text_tab("Claims")
        self.comparison_view = self._add_text_tab("Evidence Comparison")
        self.draft_view = self._add_text_tab("Draft")
        self.critique_view = self._add_text_tab("Critique")
        self.revision_view = self._add_text_tab("Revision")
        self.json_view = self._add_text_tab("Raw JSON")

    def _add_text_tab(self, title: str) -> tk.Text:
        frame = ttk.Frame(self.tabs, padding=8)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10), undo=False)
        scrollbar = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.tabs.add(frame, text=title)
        return text

    def _toggle_api_key_visibility(self) -> None:
        self.api_key_entry.configure(show="" if self.show_key_var.get() else "*")

    def _load_revision_demo_documents(self) -> None:
        self.demo_mode = "revision"
        self.selected_files = sorted(Path("documents/demo_set_01").glob("*.txt"))
        self.question_text.delete("1.0", tk.END)
        self.question_text.insert("1.0", DEFAULT_QUESTION)
        self._refresh_file_list()

    def _load_no_revision_demo_documents(self) -> None:
        self.demo_mode = "no_revision"
        self.selected_files = sorted(Path("documents/demo_set_02_no_revision").glob("*.txt"))
        self.question_text.delete("1.0", tk.END)
        self.question_text.insert("1.0", "Does Therapy Z show consistent evidence on the predefined endpoint in Condition Q?")
        self._refresh_file_list()

    def _add_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Choose scientific documents",
            filetypes=[("Supported documents", "*.txt *.pdf"), ("Text files", "*.txt"), ("PDF files", "*.pdf")],
        )
        if not files:
            return
        existing = {path.resolve() for path in self.selected_files}
        for file_name in files:
            path = Path(file_name)
            if path.resolve() not in existing:
                self.selected_files.append(path)
        self.demo_mode = "custom"
        self._refresh_file_list()

    def _clear_files(self) -> None:
        self.demo_mode = "custom"
        self.selected_files = []
        self.current_state = None
        self._refresh_file_list()
        self._set_all_views("No documents loaded. Add files or choose a demo set, then run the workflow.")

    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, tk.END)
        for path in self.selected_files:
            self.file_list.insert(tk.END, path.name)
        self.status_var.set(f"{len(self.selected_files)} document(s) selected")
        if self.selected_files:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(0)
            self.file_list.activate(0)
            self._show_document_text(self.selected_files[0])
        else:
            self._replace_text(self.uploaded_text_view, "No document selected.")

    def _show_selected_document_text(self, _event: tk.Event | None = None) -> None:
        selection = self.file_list.curselection()
        if not selection:
            return
        index = selection[0]
        if index >= len(self.selected_files):
            return
        self._show_document_text(self.selected_files[index])

    def _show_document_text(self, path: Path) -> None:
        try:
            text = read_document_text(path)
        except Exception as exc:
            text = f"Could not preview {path.name}.\n\n{exc}"

        preview = [
            f"Source: {path.name}",
            f"Path: {path}",
            "",
            text or "[No text found.]",
        ]
        self._replace_text(self.uploaded_text_view, "\n".join(preview))

    def _run_reasoning(self) -> None:
        question = self.question_text.get("1.0", tk.END).strip() or DEFAULT_QUESTION
        if not self.selected_files:
            messagebox.showwarning("No documents", "Add at least one text or PDF document before running.")
            return

        api_key = self.api_key_var.get().strip()
        force_local_demo = self.demo_mode == "no_revision"
        if force_local_demo:
            os.environ["FORCE_LOCAL_LLM"] = "1"
            os.environ.pop("OPENAI_API_KEY", None)
        elif api_key:
            os.environ.pop("FORCE_LOCAL_LLM", None)
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            os.environ.pop("FORCE_LOCAL_LLM", None)
            os.environ.pop("OPENAI_API_KEY", None)

        self.run_button.configure(state=tk.DISABLED)
        mode = "deterministic demo fallback" if force_local_demo else ("OpenAI API" if api_key else "local fallback")
        self.status_var.set(f"Running workflow with {mode}...")
        self._set_all_views("Running. The agent is loading documents and building the reasoning state...")

        thread = threading.Thread(target=self._run_in_background, args=(question, list(self.selected_files)), daemon=True)
        thread.start()

    def _run_in_background(self, question: str, paths: list[Path]) -> None:
        try:
            state = run_workflow(question, document_paths=paths)
            output_path = save_report(state["explainability_report"])
            self.result_queue.put(("success", {"state": state, "output_path": output_path}))
        except Exception as exc:
            self.result_queue.put(("error", exc))

    def _poll_result_queue(self) -> None:
        try:
            status, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_result_queue)
            return

        self.run_button.configure(state=tk.NORMAL)
        if status == "error":
            self.status_var.set("Workflow failed")
            messagebox.showerror("Workflow failed", str(payload))
        else:
            self.current_state = payload["state"]
            self._render_state(self.current_state)
            self.status_var.set(f"Report saved: {payload['output_path']}")
        self.after(100, self._poll_result_queue)

    def _set_all_views(self, text: str) -> None:
        for widget in (
            self.summary_view,
            self.uploaded_text_view,
            self.documents_view,
            self.claims_view,
            self.comparison_view,
            self.draft_view,
            self.critique_view,
            self.revision_view,
            self.json_view,
        ):
            self._replace_text(widget, text)

    def _render_state(self, state: dict[str, Any]) -> None:
        report = state.get("explainability_report", {})
        self._replace_text(self.summary_view, self._format_summary(state))
        self._replace_text(self.uploaded_text_view, self._format_uploaded_documents(state))
        self._replace_text(self.documents_view, self._format_document_thoughts(state))
        self._replace_text(self.claims_view, self._format_claims(state))
        self._replace_text(self.comparison_view, self._format_comparison(state))
        self._replace_text(self.draft_view, state.get("draft_conclusion", ""))
        self._replace_text(self.critique_view, json.dumps(state.get("critique", {}), indent=2))
        self._replace_text(self.revision_view, self._format_revision(state))
        self._replace_text(self.json_view, json.dumps(report, indent=2))

    def _replace_text(self, widget: tk.Text, content: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state=tk.DISABLED)

    def _format_summary(self, state: dict[str, Any]) -> str:
        report = state.get("explainability_report", {})
        lines = [
            "Final conclusion",
            "================",
            state.get("final_conclusion", report.get("final_conclusion", "")),
            "",
            f"Confidence: {state.get('confidence', report.get('confidence', 'low'))}",
            "",
            f"Revised: {state.get('revision_needed', False)}",
        ]
        return "\n".join(lines)

    def _format_document_thoughts(self, state: dict[str, Any]) -> str:
        sections = []
        for insight in state.get("document_insights", []):
            sections.append(insight.get("agent_thinks", ""))
            for claim in insight.get("claims", []):
                sections.append(f"  - Claim: {claim.get('claim', '')}")
                sections.append(f"    Type: {claim.get('claim_type', 'unknown')}")
                sections.append(f"    Limitation: {claim.get('limitation', '')}")
            sections.append("")
        return "\n".join(sections).strip() or "No document insights available."

    def _format_uploaded_documents(self, state: dict[str, Any]) -> str:
        sections = []
        for document in state.get("documents", []):
            sections.append(f"Source: {document.get('source', '')}")
            sections.append(f"Path: {document.get('path', '')}")
            sections.append(f"Type: {document.get('file_type', 'txt')}")
            sections.append("")
            sections.append(document.get("text", "") or "[No text found.]")
            sections.append("\n" + "=" * 80 + "\n")
        return "\n".join(sections).strip() or "No uploaded text available."

    def _format_claims(self, state: dict[str, Any]) -> str:
        lines = []
        for claim in state.get("claims", []):
            lines.append(f"{claim.get('source', '')}")
            lines.append(f"  Claim: {claim.get('claim', '')}")
            lines.append(f"  Type: {claim.get('claim_type', '')}")
            lines.append(f"  Limitation: {claim.get('limitation', '')}")
            lines.append("")
        return "\n".join(lines).strip() or "No claims extracted."

    def _format_comparison(self, state: dict[str, Any]) -> str:
        sections = ["Evidence for", "------------"]
        for item in state.get("evidence_for", []):
            sections.append(f"- {item.get('source')}: {item.get('claim')}")
            sections.append(f"  Why it matters: {item.get('why_it_matters')}")

        sections.extend(["", "Evidence against", "----------------"])
        for item in state.get("evidence_against", []):
            sections.append(f"- {item.get('source')}: {item.get('claim')}")
            sections.append(f"  Why it matters: {item.get('why_it_matters')}")

        sections.extend(["", "Conflicts", "---------"])
        for conflict in state.get("conflicts", []):
            sections.append(f"- {conflict}")

        sections.extend(["", "Uncertainty sources", "-------------------"])
        for source in state.get("uncertainty_sources", []):
            sections.append(f"- {source}")

        return "\n".join(sections)

    def _format_revision(self, state: dict[str, Any]) -> str:
        if not state.get("revision_needed"):
            return "Revision was not needed. The draft conclusion was used as the final conclusion."
        return state.get("final_conclusion", "")


def main() -> None:
    app = ReasoningAgentApp()
    app.mainloop()


if __name__ == "__main__":
    main()
