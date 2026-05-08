"""Internationalization (i18n) support for the GUI.

Provides Chinese/English translations for all UI text.
Usage:
    from utils.i18n import lang
    label_text = lang.tr("llm_config")
"""

from __future__ import annotations

from typing import Callable

# ── Translation dictionary ────────────────────────────────────────────────

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # App
        "app_title": "PDF Paper Summarizer",
        "process_btn": "▶  PROCESS NOW",
        "process_btn_processing": "⏳ Processing...",
        "select_pdf_first": "Please select a PDF file first.",
        "error": "Error",

        # Config panel
        "llm_config": "LLM Configuration",
        "backend": "Backend:",
        "model": "Model:",
        "api_key": "API Key:",
        "api_key_placeholder": "Enter API key or set env var",
        "no_key_needed": "No API key needed",
        "or_env": "or {env}",
        "base_url": "API Base URL:",
        "base_url_placeholder": "https://api.example.com/v1",
        "model_placeholder": "Enter model name",
        "test_connection": "Test Connection",
        "testing": "Testing...",
        "test_success": "✓ Connected",
        "test_failed": "✗ {error}",

        # PDF selector
        "pdf_selection": "PDF Selection",
        "select_pdf": "📂  Select PDF...",
        "select_folder": "📁  Select Folder",
        "no_file": "No file selected",
        "pdf_count": "{n} PDF files",
        "select_pdf_title": "Select a PDF file",
        "processing_file": "Processing {i}/{n}: {name}",

        # Options panel
        "options": "Options",
        "output_lang": "Output Language:",
        "hybrid_mode": "Hybrid mode (text + images for math/figures)",
        "yaml_frontmatter": "Generate YAML frontmatter",
        "output": "Output:",
        "browse": "Browse",
        "tags": "Tags:",
        "tags_placeholder": "paper, summary",
        "comma_separated": "comma-separated",

        # Progress panel
        "progress_log": "Progress & Log",
        "ready": "Ready",
        "open_output": "📂  Open Output Folder",
        "open_obsidian": "📄  Open in Obsidian",
        "summary_saved": "✓ Summary saved: {name}",

        # File info
        "kb": "KB",
        "mb": "MB",

        # Language
        "lang_zh": "中",
        "lang_en": "EN",
    },
    "zh": {
        # App
        "app_title": "PDF 论文总结工具",
        "process_btn": "▶  开始处理",
        "process_btn_processing": "⏳ 处理中...",
        "select_pdf_first": "请先选择一篇 PDF 论文",
        "error": "错误",

        # Config panel
        "llm_config": "LLM 配置",
        "backend": "后端:",
        "model": "模型:",
        "api_key": "API 密钥:",
        "api_key_placeholder": "输入 API 密钥或设置环境变量",
        "no_key_needed": "无需 API 密钥",
        "or_env": "或 {env}",
        "base_url": "API 地址:",
        "base_url_placeholder": "https://api.example.com/v1",
        "model_placeholder": "输入模型名称",
        "test_connection": "测试连接",
        "testing": "测试中...",
        "test_success": "✓ 连接成功",
        "test_failed": "✗ {error}",

        # PDF selector
        "pdf_selection": "选择 PDF",
        "select_pdf": "📂  选择 PDF...",
        "select_folder": "📁  选择文件夹",
        "no_file": "未选择文件",
        "pdf_count": "{n} 个 PDF 文件",
        "select_pdf_title": "选择 PDF 文件",
        "processing_file": "正在处理第 {i}/{n} 个：{name}",

        # Options panel
        "options": "选项",
        "output_lang": "输出语言:",
        "hybrid_mode": "混合模式（文本 + 公式/图表页转图片）",
        "yaml_frontmatter": "生成 YAML 前言元数据",
        "output": "输出路径:",
        "browse": "浏览",
        "tags": "标签:",
        "tags_placeholder": "论文, 总结",
        "comma_separated": "用逗号分隔",

        # Progress panel
        "progress_log": "进度与日志",
        "ready": "就绪",
        "open_output": "📂  打开输出文件夹",
        "open_obsidian": "📄  在 Obsidian 中打开",
        "summary_saved": "✓ 总结已保存: {name}",

        # File info
        "kb": "KB",
        "mb": "MB",

        # Language
        "lang_zh": "中",
        "lang_en": "EN",
    },
}


class LanguageManager:
    """Singleton language manager for GUI translations."""

    def __init__(self):
        self._current_lang: str = "zh"  # default to Chinese
        self._listeners: list[Callable[[str], None]] = []

    @property
    def lang(self) -> str:
        return self._current_lang

    def set_language(self, lang: str) -> None:
        """Switch language and notify all listeners."""
        if lang not in TRANSLATIONS:
            lang = "en"
        self._current_lang = lang
        for listener in self._listeners:
            listener(lang)

    def tr(self, key: str, **kwargs) -> str:
        """Translate a key to the current language.

        Args:
            key: Translation key.
            **kwargs: Optional format arguments (e.g. name="file.pdf").

        Returns:
            Translated string, or the key itself if not found.
        """
        text = TRANSLATIONS.get(self._current_lang, {}).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text

    def bind(self, callback: Callable[[str], None]) -> None:
        """Register a listener that gets called when language changes."""
        self._listeners.append(callback)

    def unbind(self, callback: Callable[[str], None]) -> None:
        """Remove a registered listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)


# Singleton instance
lang = LanguageManager()
