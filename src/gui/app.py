"""Main GUI application for PDF Paper Summarizer."""

from __future__ import annotations

import asyncio
import os
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from src.config.settings import ConfigManager, ConfigError
from src.gui.widgets.config_panel import ConfigPanel, PROVIDERS
from src.gui.widgets.pdf_selector import PDFSelector
from src.gui.widgets.progress_panel import ProgressPanel
from src.pipeline import SummarizationPipeline
from utils.i18n import lang


class PaperSummarizerApp(ctk.CTk):
    """Main application window."""

    TITLE_KEY = "app_title"
    DEFAULT_WIDTH = 850
    DEFAULT_HEIGHT = 820

    def __init__(self, config: ConfigManager | None = None):
        super().__init__()

        # Load config
        try:
            self._config = config or ConfigManager()
        except ConfigError as e:
            self._show_config_error(str(e))
            self._config = ConfigManager.__new__(ConfigManager)
            self._config._data = {}  # type: ignore

        # Window setup
        self.title(lang.tr(self.TITLE_KEY))
        geom = (
            self._config.get("gui", "window_width", default=self.DEFAULT_WIDTH),
            self._config.get("gui", "window_height", default=self.DEFAULT_HEIGHT),
        )
        self.geometry(f"{geom[0]}x{geom[1]}")
        self.minsize(700, 650)

        # Set theme to light
        ctk.set_appearance_mode("light")

        # Async setup
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._processing = False

        # Pipeline
        self._pipeline = SummarizationPipeline(self._config)

        # Build UI
        self._build_ui()

        # Listen for language changes
        lang.bind(self._on_lang_change)

        # Start async event loop
        self._start_async_loop()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the complete UI layout."""
        self.grid_columnconfigure(0, weight=1)

        pad = {"padx": 20, "pady": (8, 4)}

        # ── Title Bar (row 0) ────────────────────────────────────────────
        self._title_bar = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self._title_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 0))
        self._title_bar.grid_columnconfigure(0, weight=1)
        self._title_bar.grid_propagate(False)

        self._title_label = ctk.CTkLabel(
            self._title_bar,
            text=lang.tr("app_title"),
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        self._title_label.grid(row=0, column=0, sticky="w")

        # Language toggle button (top-right)
        self._lang_btn = ctk.CTkButton(
            self._title_bar,
            text=lang.tr("lang_en"),
            command=self._toggle_language,
            width=50,
            height=28,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=["#E0E0E0", "#3B3B3B"],
            hover_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
            border_width=1,
            border_color=["#CCCCCC", "#555555"],
        )
        self._lang_btn.grid(row=0, column=1, sticky="e")

        # ── LLM Config (row 1) ───────────────────────────────────────────
        provider = self._config.get("llm", "default_provider", default="anthropic")
        model = self._config.get("llm", provider, "model", default="")
        api_key = self._config.get_api_key(provider) or ""

        self._config_panel = ConfigPanel(
            self,
            default_provider=provider,
            default_model=model,
            default_api_key=api_key,
            on_change=self._on_config_change,
        )
        self._config_panel.grid(row=1, column=0, sticky="ew", **pad)

        # ── PDF Selection (row 2) ────────────────────────────────────────
        self._pdf_selector = PDFSelector(self)
        self._pdf_selector.grid(row=2, column=0, sticky="ew", **pad)

        # ── Options (row 3) ──────────────────────────────────────────────
        self._options_frame = ctk.CTkFrame(self)
        self._options_frame.grid(row=3, column=0, sticky="ew", **pad)

        self._opt_label = ctk.CTkLabel(self._options_frame, text=lang.tr("options"),
                                       font=ctk.CTkFont(size=14, weight="bold"))
        self._opt_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=(20, 0), pady=(0, 8))

        # Hybrid mode checkbox
        self._hybrid_var = ctk.BooleanVar(
            value=self._config.get("pdf", "hybrid_mode", default=True)
        )
        self._hybrid_cb = ctk.CTkCheckBox(
            self._options_frame, text=lang.tr("hybrid_mode"),
            variable=self._hybrid_var,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            checkmark_color="#FFFFFF",
        )
        self._hybrid_cb.grid(row=1, column=0, columnspan=2, sticky="w", padx=(20, 0), pady=(0, 6))

        # Frontmatter checkbox
        self._frontmatter_var = ctk.BooleanVar(
            value=self._config.get("output", "yaml_frontmatter", default=True)
        )
        self._frontmatter_cb = ctk.CTkCheckBox(
            self._options_frame, text=lang.tr("yaml_frontmatter"),
            variable=self._frontmatter_var,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            checkmark_color="#FFFFFF",
        )
        self._frontmatter_cb.grid(row=2, column=0, columnspan=2, sticky="w", padx=(20, 0))

        # Output path
        self._output_label = ctk.CTkLabel(self._options_frame, text=lang.tr("output"))
        self._output_label.grid(row=3, column=0, sticky="w", padx=(20, 0), pady=(4, 0))
        self._output_path_var = ctk.StringVar(
            value=str(self._config.get_vault_path())
        )
        self._output_entry = ctk.CTkEntry(
            self._options_frame, textvariable=self._output_path_var, width=400
        )
        self._output_entry.grid(row=3, column=1, sticky="w", padx=(12, 4), pady=(4, 0))

        self._browse_btn = ctk.CTkButton(
            self._options_frame, text=lang.tr("browse"), width=70,
            command=self._browse_output,
            fg_color=["#E0E0E0", "#3B3B3B"],
            hover_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
            border_width=1,
            border_color=["#CCCCCC", "#555555"],
        )
        self._browse_btn.grid(row=3, column=2, sticky="w", padx=(0, 0), pady=(4, 0))

        # Tags
        self._tags_label = ctk.CTkLabel(self._options_frame, text=lang.tr("tags"))
        self._tags_label.grid(row=4, column=0, sticky="w", padx=(20, 0), pady=(4, 0))
        default_tags = ", ".join(
            self._config.get("output", "tags", default=["paper", "summary"])
        )
        self._tags_var = ctk.StringVar(value=default_tags)
        self._tags_entry = ctk.CTkEntry(
            self._options_frame, textvariable=self._tags_var, width=300,
            placeholder_text=lang.tr("tags_placeholder"),
        )
        self._tags_entry.grid(row=4, column=1, sticky="w", padx=(12, 4), pady=(4, 0))
        self._tags_hint = ctk.CTkLabel(
            self._options_frame, text=lang.tr("comma_separated"),
            font=ctk.CTkFont(size=11), text_color="gray",
        )
        self._tags_hint.grid(row=4, column=2, sticky="w", pady=(4, 0))

        # Output language (row 5)
        self._output_lang_label = ctk.CTkLabel(
            self._options_frame, text=lang.tr("output_lang")
        )
        self._output_lang_label.grid(row=5, column=0, sticky="w", padx=(20, 0), pady=(4, 0))
        self._output_lang_var = ctk.StringVar(
            value=self._config.get("output", "language", default="zh")
        )
        self._output_lang_menu = ctk.CTkOptionMenu(
            self._options_frame,
            values=["中文", "English"],
            command=self._on_output_lang_change,
            width=120,
            fg_color=["#F5F5F5", "#2B2B2B"],
            button_color=["#D0D0D0", "#4B4B4B"],
            button_hover_color=["#AAAAAA", "#666666"],
            text_color=["#333333", "#FFFFFF"],
            dropdown_fg_color=["#FFFFFF", "#2B2B2B"],
            dropdown_hover_color=["#E8E8E8", "#444444"],
        )
        self._output_lang_menu.set("中文" if self._output_lang_var.get() == "zh" else "English")
        self._output_lang_menu.grid(row=5, column=1, sticky="w", padx=(12, 4), pady=(4, 0))

        # ── Process Button (row 4) ───────────────────────────────────────
        self._process_btn = ctk.CTkButton(
            self,
            text=lang.tr("process_btn"),
            command=self._on_process,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            text_color="#FFFFFF",
        )
        self._process_btn.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 4))

        # ── Progress & Log (row 5) ───────────────────────────────────────
        self._progress_panel = ProgressPanel(self)
        self._progress_panel.grid(row=5, column=0, sticky="nsew", padx=16, pady=(4, 12))
        self.grid_rowconfigure(5, weight=1)

    # ── Language toggle ──────────────────────────────────────────────────

    def _toggle_language(self):
        """Switch between Chinese and English."""
        new_lang = "en" if lang.lang == "zh" else "zh"
        lang.set_language(new_lang)

    def _on_lang_change(self, new_lang: str):
        """Refresh UI when language changes."""
        self.title(lang.tr("app_title"))
        self._title_label.configure(text=lang.tr("app_title"))

        # Toggle button shows the *other* language
        self._lang_btn.configure(text=lang.tr("lang_en") if new_lang == "zh" else lang.tr("lang_zh"))

        # Options panel
        self._opt_label.configure(text=lang.tr("options"))
        self._hybrid_cb.configure(text=lang.tr("hybrid_mode"))
        self._frontmatter_cb.configure(text=lang.tr("yaml_frontmatter"))
        self._output_label.configure(text=lang.tr("output"))
        self._browse_btn.configure(text=lang.tr("browse"))
        self._tags_label.configure(text=lang.tr("tags"))
        self._tags_entry.configure(placeholder_text=lang.tr("tags_placeholder"))
        self._tags_hint.configure(text=lang.tr("comma_separated"))
        self._output_lang_label.configure(text=lang.tr("output_lang"))

        # Process button
        if not self._processing:
            self._process_btn.configure(text=lang.tr("process_btn"))

    def _on_config_change(self, key: str, value: str):
        """Handle config panel changes — load per-provider API key on switch."""
        if key == "provider":
            stored_key = self._config.get_api_key(value) or ""
            self._config_panel.set_api_key(stored_key)

    def _on_output_lang_change(self, display: str):
        """Handle output language dropdown change."""
        lang_code = "zh" if display == "中文" else "en"
        self._output_lang_var.set(lang_code)

    # ── Event handlers ──────────────────────────────────────────────────

    def _browse_output(self):
        folder = filedialog.askdirectory(
            title="Select output folder",
            initialdir=self._output_path_var.get(),
        )
        if folder:
            self._output_path_var.set(folder)

    async def _run_pipeline(self, pdf_path: Path, file_index: int = 1, file_total: int = 1):
        """Run the full processing pipeline for a single PDF.

        Does NOT manage self._processing or button state — caller handles it.

        Args:
            pdf_path: Path to the PDF file.
            file_index: 1-based index for batch progress display.
            file_total: Total number of files in the batch.
        """
        if file_index == 1:
            self._progress_panel.reset()

        async def on_progress(msg: str):
            self._progress_panel.log(msg)
            self._progress_panel.update_status(msg)

        try:
            # Parse tags
            tags_str = self._tags_var.get().strip()
            tags = [t.strip() for t in tags_str.split(",") if t.strip()] or None

            # Determine provider config
            config_data = self._config_panel.get_config()
            provider = config_data["provider"]
            model = config_data["model"]
            api_key = config_data.get("api_key") or None
            base_url = config_data.get("base_url") or None

            # If no API key from UI, try env var
            if not api_key and provider in ("anthropic", "openai"):
                env_key = PROVIDERS[provider].get("key_env", "")
                api_key = os.environ.get(env_key, "")

            # Log batch progress header
            if file_total > 1:
                header = lang.tr("processing_file", i=file_index, n=file_total, name=pdf_path.name)
                self._progress_panel.log(f"── {header} ──", "progress")

            # Start indeterminate progress for LLM phase
            self._progress_panel.set_indeterminate(True)

            output_path = await self._pipeline.run(
                pdf_path=pdf_path,
                on_progress=on_progress,
                override_provider=provider if provider != self._config.get("llm", "default_provider") else None,
                override_model=model,
                override_api_key=api_key,
                override_base_url=base_url,
                hybrid_mode=self._hybrid_var.get(),
                output_vault=self._output_path_var.get(),
                tags=tags,
                output_language=self._output_lang_var.get(),
            )

            self._progress_panel.set_indeterminate(False)

            if file_total > 1:
                self._progress_panel.log(f"✓ {lang.tr('summary_saved', name=output_path.name)}", "success")
                self._progress_panel.update_status(
                    f"{file_index}/{file_total}: {pdf_path.name}")
                # Enable open buttons on last file
                if file_index == file_total:
                    self._progress_panel.show_complete(output_path)
                    subprocess.Popen(["explorer", "/select,", str(output_path)])
            else:
                self._progress_panel.show_complete(output_path)
                subprocess.Popen(["explorer", "/select,", str(output_path)])

        except Exception as e:
            self._progress_panel.set_indeterminate(False)
            self._progress_panel.log(f"✗ {lang.tr('error')}: {e}", "error")
            self._progress_panel.update_status(f"{lang.tr('error')}: {e}")
            import traceback
            self._progress_panel.log(traceback.format_exc(), "error")

    def _save_config(self):
        """Save current LLM config to config.yaml for next session."""
        provider = self._config_panel.provider
        model = self._config_panel.model
        api_key = self._config_panel.api_key

        updates = {
            "llm": {
                "default_provider": provider,
                provider: {"api_key": api_key},
            }
        }
        if model:
            updates["llm"][provider]["model"] = model
        if provider == "custom":
            updates["llm"][provider]["base_url"] = self._config_panel.base_url

        updates.setdefault("output", {})["language"] = self._output_lang_var.get()

        self._config.save(updates)

    def _on_process(self):
        """Handle process button click — supports single file and batch folder."""
        if not self._pdf_selector.has_pdf:
            self._progress_panel.log(lang.tr("select_pdf_first"), "error")
            return

        pdf_paths = self._pdf_selector.pdf_paths
        if not pdf_paths:
            return

        self._save_config()
        self._processing = True
        self._process_btn.configure(state="disabled", text=lang.tr("process_btn_processing"))

        file_total = len(pdf_paths)
        if file_total == 1:
            asyncio.run_coroutine_threadsafe(
                self._run_single(pdf_paths[0]), self._loop
            )
        else:
            asyncio.run_coroutine_threadsafe(
                self._run_batch(pdf_paths), self._loop
            )

    async def _run_single(self, pdf_path: Path):
        """Process a single PDF and reset state."""
        try:
            await self._run_pipeline(pdf_path, 1, 1)
        finally:
            self._processing = False
            self._process_btn.configure(state="normal", text=lang.tr("process_btn"))

    async def _run_batch(self, pdf_paths: list[Path]):
        """Process multiple PDFs sequentially."""
        total = len(pdf_paths)
        try:
            for i, path in enumerate(pdf_paths, 1):
                await self._run_pipeline(path, i, total)

            self._progress_panel.update_status(
                f"✓ Batch complete: {total} files processed"
            )
        finally:
            self._processing = False
            self._process_btn.configure(state="normal", text=lang.tr("process_btn"))

    # ── Async event loop management ─────────────────────────────────────

    def _start_async_loop(self):
        """Start asyncio event loop in a background thread."""
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever, daemon=True
        )
        self._loop_thread.start()

    def _stop_async_loop(self):
        """Safely stop the async event loop."""
        if not self._loop:
            return
        # Cancel all pending tasks first
        for task in asyncio.all_tasks(self._loop):
            task.cancel()
        # Schedule loop stop
        self._loop.call_soon_threadsafe(self._loop.stop)

    def _show_config_error(self, message: str):
        """Show a configuration error dialog."""
        print(f"Configuration Error: {message}")

    def _on_close(self):
        """Clean up on window close."""
        try:
            self._save_config()
        except Exception:
            pass
        try:
            self._stop_async_loop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        # Force tkinter mainloop to exit
        self.quit()
