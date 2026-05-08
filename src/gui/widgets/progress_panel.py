"""Progress and logging panel widget with i18n support."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from utils.i18n import lang


class ProgressPanel(ctk.CTkFrame):
    """Panel showing progress bar, log output, and action buttons."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._output_path: Path | None = None
        self._build_ui()
        lang.bind(self._on_lang_change)

    def _build_ui(self):
        # Section label
        self._section_label = ctk.CTkLabel(self, text=lang.tr("progress_log"),
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self._section_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Progress bar
        self._progress_bar = ctk.CTkProgressBar(self)
        self._progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        self._progress_bar.set(0)

        # Status label
        self._status_label = ctk.CTkLabel(
            self, text=lang.tr("ready"), anchor="w", font=ctk.CTkFont(size=12)
        )
        self._status_label.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))

        # Configure grid weights for resizing
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1, minsize=120)

        # Action buttons row (above log)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 4))

        self._open_btn = ctk.CTkButton(
            button_frame,
            text=lang.tr("open_output"),
            command=self._open_output_folder,
            state="disabled",
            fg_color=["#E0E0E0", "#3B3B3B"],
            hover_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
            border_width=1,
            border_color=["#CCCCCC", "#555555"],
        )
        self._open_btn.pack(side="left")

        # Log text box
        self._log_box = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self._log_box.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(0, 8))
        self._log_box._textbox.tag_config("info", foreground="#5B9BD5")
        self._log_box._textbox.tag_config("success", foreground="#70AD47")
        self._log_box._textbox.tag_config("error", foreground="#FF4444")
        self._log_box._textbox.tag_config("progress", foreground="#FFC000")

    def _on_lang_change(self, _new_lang: str):
        """Refresh text when language changes."""
        self._section_label.configure(text=lang.tr("progress_log"))
        self._open_btn.configure(text=lang.tr("open_output"))
        if not self._output_path:
            self._status_label.configure(text=lang.tr("ready"))

    # ── Logging ──────────────────────────────────────────────────────────

    def log(self, message: str, tag: str = "info"):
        """Append a timestamped message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"
        self._log_box.configure(state="normal")
        self._log_box.insert("end", line, tag)
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def update_status(self, message: str, progress: float | None = None):
        """Update status label and optionally progress bar."""
        self._status_label.configure(text=message)
        if progress is not None:
            self._progress_bar.set(progress)

    def set_progress(self, value: float):
        """Set progress bar value (0.0 to 1.0)."""
        self._progress_bar.set(value)

    def set_indeterminate(self, active: bool):
        """Switch progress bar to indeterminate mode."""
        if active:
            self._progress_bar.configure(mode="indeterminate")
            self._progress_bar.start()
        else:
            self._progress_bar.stop()
            self._progress_bar.configure(mode="determinate")

    # ── Results ──────────────────────────────────────────────────────────

    def show_complete(self, output_path: Path):
        """Show completion state with action buttons enabled."""
        self._output_path = output_path
        self._open_btn.configure(state="normal")
        self._progress_bar.set(1.0)
        self.log(lang.tr("summary_saved", name=output_path.name), "success")

    def reset(self):
        """Reset to initial state."""
        self._output_path = None
        self._status_label.configure(text=lang.tr("ready"))
        self._progress_bar.set(0)
        self._open_btn.configure(state="disabled")
        self._progress_bar.configure(mode="determinate")

    # ── Actions ──────────────────────────────────────────────────────────

    def _open_output_folder(self):
        """Open the output folder in Windows Explorer."""
        if self._output_path:
            import subprocess
            subprocess.Popen(["explorer", "/select,", str(self._output_path)])
