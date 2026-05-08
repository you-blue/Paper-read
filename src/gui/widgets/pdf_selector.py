"""PDF file/folder selection widget with i18n support."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from utils.i18n import lang


class PDFSelector(ctk.CTkFrame):
    """Panel for selecting a PDF file or a folder of PDFs."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._pdf_paths: list[Path] = []
        self._is_folder_mode = False
        self._on_select_callback = None

        self._build_ui()
        lang.bind(self._on_lang_change)

    def _build_ui(self):
        # Section label
        self._section_label = ctk.CTkLabel(self, text=lang.tr("pdf_selection"),
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self._section_label.grid(row=0, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(0, 8))

        btn_style = {
            "fg_color": ["#E0E0E0", "#3B3B3B"],
            "hover_color": ["#CCCCCC", "#555555"],
            "text_color": ["#333333", "#FFFFFF"],
            "border_width": 1,
            "border_color": ["#CCCCCC", "#555555"],
        }

        # Select PDF button
        self._select_btn = ctk.CTkButton(
            self, text=lang.tr("select_pdf"),
            command=self._on_select_click, width=120, **btn_style,
        )
        self._select_btn.grid(row=1, column=0, sticky="w", padx=(20, 8))

        # Select Folder button
        self._folder_btn = ctk.CTkButton(
            self, text=lang.tr("select_folder"),
            command=self._on_select_folder_click, width=120, **btn_style,
        )
        self._folder_btn.grid(row=1, column=1, sticky="w", padx=(0, 12))

        # Info label
        self._info_label = ctk.CTkLabel(
            self, text=lang.tr("no_file"),
            anchor="w", font=ctk.CTkFont(size=12),
        )
        self._info_label.grid(row=1, column=2, sticky="w")

        # File size / count label
        self._size_label = ctk.CTkLabel(
            self, text="", anchor="w",
            font=ctk.CTkFont(size=11), text_color="gray",
        )
        self._size_label.grid(row=2, column=2, sticky="w", padx=(0, 8))

        # Clear button
        self._clear_btn = ctk.CTkButton(
            self, text="✕", width=30, command=self._clear,
            fg_color="transparent", border_width=1, text_color="gray",
        )
        self._clear_btn.grid(row=1, column=3, sticky="e")
        self._clear_btn.grid_remove()

    def _on_lang_change(self, _new_lang: str):
        """Refresh text when language changes."""
        self._section_label.configure(text=lang.tr("pdf_selection"))
        self._select_btn.configure(text=lang.tr("select_pdf"))
        self._folder_btn.configure(text=lang.tr("select_folder"))
        if not self._pdf_paths:
            self._info_label.configure(text=lang.tr("no_file"))

    def _on_select_click(self):
        """Open file dialog for single PDF selection."""
        file_path = filedialog.askopenfilename(
            title=lang.tr("select_pdf_title"),
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if file_path:
            self.set_pdfs([Path(file_path)])

    def _on_select_folder_click(self):
        """Open folder dialog to select all PDFs in a folder."""
        folder = filedialog.askdirectory(title=lang.tr("select_folder"))
        if folder:
            path = Path(folder)
            pdfs = sorted(path.rglob("*.pdf"))
            if pdfs:
                self.set_pdfs(pdfs, folder_mode=True)
            else:
                self._info_label.configure(
                    text=f"No PDFs found in {path.name}"
                )

    def set_pdfs(self, paths: list[Path], folder_mode: bool = False):
        """Set the selected PDFs and update display."""
        self._pdf_paths = paths
        self._is_folder_mode = folder_mode

        if len(paths) == 1:
            p = paths[0]
            self._info_label.configure(text=p.name)
            self._update_size(p)
        else:
            self._info_label.configure(
                text=lang.tr("pdf_count", n=len(paths))
                + (f" ({paths[0].parent.name})" if folder_mode else "")
            )
            self._size_label.configure(text="")

        self._clear_btn.grid()

        if self._on_select_callback:
            self._on_select_callback(paths)

    def _update_size(self, path: Path):
        try:
            size_bytes = path.stat().st_size
            if size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} {lang.tr('kb')}"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} {lang.tr('mb')}"
            self._size_label.configure(text=size_str)
        except OSError:
            self._size_label.configure(text="")

    def _clear(self):
        """Clear the selected file(s)."""
        self._pdf_paths = []
        self._is_folder_mode = False
        self._info_label.configure(text=lang.tr("no_file"))
        self._size_label.configure(text="")
        self._clear_btn.grid_remove()

    def on_select(self, callback):
        """Register callback for when PDF(s) are selected."""
        self._on_select_callback = callback

    @property
    def pdf_paths(self) -> list[Path]:
        return list(self._pdf_paths)

    @property
    def pdf_path(self) -> Path | None:
        """Return the first PDF path (backward compat with single-file API)."""
        return self._pdf_paths[0] if self._pdf_paths else None

    @property
    def has_pdf(self) -> bool:
        return len(self._pdf_paths) > 0 and all(p.exists() for p in self._pdf_paths)

    @property
    def is_folder_mode(self) -> bool:
        return self._is_folder_mode

    @property
    def pdf_count(self) -> int:
        return len(self._pdf_paths)
