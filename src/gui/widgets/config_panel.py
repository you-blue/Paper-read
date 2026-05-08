"""LLM configuration panel widget with i18n support."""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Callable

import customtkinter as ctk
from utils.i18n import lang

# Provider definitions
PROVIDERS = {
    "anthropic": {
        "label": "Claude API (Anthropic)",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-sonnet-4-6-20250514",
            "claude-haiku-4-5-20251001",
        ],
        "needs_key": True,
        "key_env": "ANTHROPIC_API_KEY",
        "has_base_url": False,
    },
    "openai": {
        "label": "OpenAI GPT",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
        ],
        "needs_key": True,
        "key_env": "OPENAI_API_KEY",
        "has_base_url": False,
    },
    "qwen": {
        "label": "通义千问 (Qwen)",
        "models": [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen2.5-72b-instruct",
            "qwen2.5-32b-instruct",
            "qwen2.5-14b-instruct",
        ],
        "needs_key": True,
        "key_env": "QWEN_API_KEY",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "has_base_url": False,
    },
    "deepseek": {
        "label": "DeepSeek",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "needs_key": True,
        "key_env": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com",
        "has_base_url": False,
    },
    "ollama": {
        "label": "Ollama (Local)",
        "models": [
            "llama3.2-vision:latest",
            "llava:latest",
            "llama3.1:latest",
            "qwen2.5:latest",
        ],
        "needs_key": False,
        "key_env": None,
        "has_base_url": False,
    },
    "custom": {
        "label": "自定义 (Custom)",
        "models": [],
        "needs_key": True,
        "key_env": None,
        "base_url": "",
        "has_base_url": True,
    },
}


class ConfigPanel(ctk.CTkFrame):
    """Panel for LLM provider configuration."""

    def __init__(
        self,
        master,
        default_provider: str = "anthropic",
        default_model: str = "",
        default_api_key: str = "",
        default_base_url: str = "",
        on_change: Callable[[str, str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self._on_change = on_change
        self._provider_var = ctk.StringVar(value=default_provider)
        self._model_var = ctk.StringVar(value=default_model)
        self._api_key_var = ctk.StringVar(value=default_api_key)
        self._base_url_var = ctk.StringVar(value=default_base_url)

        self._build_ui()

        # Set default model
        if not default_model and default_provider in PROVIDERS:
            models = PROVIDERS[default_provider]["models"]
            if models:
                self._model_var.set(models[0])

        # Set default base_url for preset providers
        if not default_base_url and PROVIDERS.get(default_provider, {}).get("base_url"):
            self._base_url_var.set(PROVIDERS[default_provider]["base_url"])

        lang.bind(self._on_lang_change)

    _GRAY_BTN = ["#E0E0E0", "#3B3B3B"]
    _GRAY_BTN_HOVER = ["-#CCCCCC", "#555555"]
    _DROPDOWN_FG = ["#F5F5F5", "#2B2B2B"]
    _DROPDOWN_BTN = ["#D0D0D0", "#4B4B4B"]
    _ENTRY_FG = ["#FAFAFA", "#333333"]
    _ROW_PAD = (4, 2)

    def _build_ui(self):
        padx = {"padx": (20, 8)}
        input_pad = {"padx": (0, 8)}

        # Section label
        self._section_label = ctk.CTkLabel(self, text=lang.tr("llm_config"),
                                           font=ctk.CTkFont(size=14, weight="bold"))
        self._section_label.grid(row=0, column=0, columnspan=4, sticky="w", padx=(20, 0), pady=(0, 10))

        # Provider selection (row 1)
        self._backend_label = ctk.CTkLabel(self, text=lang.tr("backend"), width=80, anchor="w")
        self._backend_label.grid(row=1, column=0, sticky="w", **padx, pady=self._ROW_PAD)
        provider_options = [p["label"] for p in PROVIDERS.values()]
        provider_values = list(PROVIDERS.keys())
        self._provider_menu = ctk.CTkOptionMenu(
            self,
            values=provider_options,
            command=self._on_provider_change,
            width=200,
            fg_color=self._DROPDOWN_FG,
            button_color=self._DROPDOWN_BTN,
            button_hover_color=self._DROPDOWN_BTN,
            dropdown_fg_color=["#FFFFFF", "#2B2B2B"],
            dropdown_hover_color=["#E8E8E8", "#444444"],
            text_color=["#333333", "#FFFFFF"],
        )
        idx = provider_values.index(self._provider_var.get()) if self._provider_var.get() in provider_values else 0
        self._provider_menu.set(provider_options[idx])
        self._provider_menu.grid(row=1, column=1, sticky="w", **input_pad)

        # Model selection (row 2)
        self._model_label = ctk.CTkLabel(self, text=lang.tr("model"), width=80, anchor="w")
        self._model_label.grid(row=2, column=0, sticky="w", **padx, pady=self._ROW_PAD)
        current_models = PROVIDERS[self._provider_var.get()]["models"]
        self._model_menu = ctk.CTkOptionMenu(
            self,
            values=current_models if current_models else ["custom"],
            variable=self._model_var,
            width=300,
            fg_color=self._DROPDOWN_FG,
            button_color=self._DROPDOWN_BTN,
            button_hover_color=self._DROPDOWN_BTN,
            dropdown_fg_color=["#FFFFFF", "#2B2B2B"],
            dropdown_hover_color=["#E8E8E8", "#444444"],
            text_color=["#333333", "#FFFFFF"],
        )
        self._model_menu.grid(row=2, column=1, sticky="w", **input_pad)
        # Model entry for custom provider (hidden by default)
        self._model_entry = ctk.CTkEntry(
            self,
            textvariable=self._model_var,
            placeholder_text=lang.tr("model_placeholder"),
            width=300,
            fg_color=self._ENTRY_FG,
            border_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
        )
        self._model_entry.grid(row=2, column=1, sticky="w", **input_pad)
        self._model_entry.grid_remove()

        # Test Connection button
        self._test_btn = ctk.CTkButton(
            self,
            text=lang.tr("test_connection"),
            command=self._on_test_connection,
            width=130,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=self._GRAY_BTN,
            hover_color=self._GRAY_BTN_HOVER,
            text_color=["#333333", "#FFFFFF"],
            border_width=1,
            border_color=["#CCCCCC", "#555555"],
        )
        self._test_btn.grid(row=2, column=2, sticky="w", padx=(32, 0))

        # Connection status label
        self._test_status = ctk.CTkLabel(
            self, text="", anchor="w", font=ctk.CTkFont(size=12),
        )
        self._test_status.grid(row=2, column=3, sticky="w", padx=(28, 0))

        # API Key entry (row 3)
        self._api_key_label = ctk.CTkLabel(self, text=lang.tr("api_key"), width=80, anchor="w")
        self._api_key_label.grid(row=3, column=0, sticky="w", **padx, pady=self._ROW_PAD)
        self._api_key_entry = ctk.CTkEntry(
            self,
            textvariable=self._api_key_var,
            placeholder_text=lang.tr("api_key_placeholder"),
            show="*",
            width=300,
            fg_color=self._ENTRY_FG,
            border_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
        )
        self._api_key_entry.grid(row=3, column=1, sticky="w", **input_pad)

        env_hint = PROVIDERS[self._provider_var.get()]["key_env"]
        self._env_label = ctk.CTkLabel(
            self,
            text=lang.tr("or_env", env=env_hint) if env_hint else "",
            font=ctk.CTkFont(size=11),
            text_color=["#888888", "#AAAAAA"],
        )
        self._env_label.grid(row=3, column=2, sticky="w")

        # Base URL entry (row 4, only for "custom")
        self._base_url_label = ctk.CTkLabel(
            self, text=lang.tr("base_url"), width=80, anchor="w"
        )
        self._base_url_label.grid(row=4, column=0, sticky="w", **padx, pady=self._ROW_PAD)
        self._base_url_entry = ctk.CTkEntry(
            self,
            textvariable=self._base_url_var,
            placeholder_text=lang.tr("base_url_placeholder"),
            width=400,
            fg_color=self._ENTRY_FG,
            border_color=["#CCCCCC", "#555555"],
            text_color=["#333333", "#FFFFFF"],
        )
        self._base_url_entry.grid(row=4, column=1, sticky="w", **input_pad)

        self._update_visibility()

    def _on_lang_change(self, _new_lang: str):
        """Refresh text when language changes."""
        self._section_label.configure(text=lang.tr("llm_config"))
        self._backend_label.configure(text=lang.tr("backend"))
        self._model_label.configure(text=lang.tr("model"))
        self._model_entry.configure(placeholder_text=lang.tr("model_placeholder"))
        self._api_key_label.configure(text=lang.tr("api_key"))
        self._base_url_label.configure(text=lang.tr("base_url"))
        self._base_url_entry.configure(placeholder_text=lang.tr("base_url_placeholder"))
        self._test_btn.configure(text=lang.tr("test_connection"))

        provider = self._provider_var.get()
        env_hint = PROVIDERS[provider]["key_env"]
        needs_key = PROVIDERS[provider]["needs_key"]

        if needs_key:
            self._api_key_entry.configure(placeholder_text=lang.tr("api_key_placeholder"))
            self._env_label.configure(text=lang.tr("or_env", env=env_hint) if env_hint else "")
        else:
            self._api_key_entry.configure(placeholder_text=lang.tr("no_key_needed"))
            self._env_label.configure(text="")

    def _on_provider_change(self, label: str):
        """Handle provider dropdown change."""
        for key, info in PROVIDERS.items():
            if info["label"] == label:
                self._provider_var.set(key)

                # Update model list
                models = info["models"]
                if models:
                    self._model_menu.configure(values=models)
                    self._model_var.set(models[0])
                    self._model_menu.configure(state="normal")
                else:
                    self._model_menu.configure(values=["custom"])
                    self._model_var.set("")
                    self._model_menu.configure(state="normal")

                # Set default base_url for presets
                preset_url = info.get("base_url", "")
                if preset_url:
                    self._base_url_var.set(preset_url)

                self._update_visibility()
                self._clear_test_status()
                if self._on_change:
                    self._on_change("provider", key)
                break

    def _update_visibility(self):
        """Show/hide API key and base_url fields based on provider."""
        provider = self._provider_var.get()
        info = PROVIDERS[provider]

        # API key visibility
        needs_key = info["needs_key"]
        state = "normal" if needs_key else "disabled"
        self._api_key_entry.configure(state=state)
        if not needs_key:
            self._api_key_entry.configure(placeholder_text=lang.tr("no_key_needed"))

        env_hint = info["key_env"]
        self._env_label.configure(text=lang.tr("or_env", env=env_hint) if env_hint else "")

        # Model widget: dropdown for presets, entry for custom
        if provider == "custom":
            self._model_menu.grid_remove()
            self._model_entry.grid()
        else:
            self._model_entry.grid_remove()
            self._model_menu.grid()

        # Base URL visibility (only for "custom")
        show_base = info.get("has_base_url", False)
        if show_base:
            self._base_url_label.grid()
            self._base_url_entry.grid()
        else:
            self._base_url_label.grid_remove()
            self._base_url_entry.grid_remove()

    # ── Test Connection ──────────────────────────────────────────────────

    def _clear_test_status(self):
        self._test_status.configure(text="")

    def _on_test_connection(self):
        """Run connection test in background thread."""
        self._test_btn.configure(state="disabled", text=lang.tr("testing"))
        self._test_status.configure(text="", text_color="gray")

        thread = threading.Thread(target=self._run_test, daemon=True)
        thread.start()

    def _run_test(self):
        """Run async test in a thread and schedule UI update."""
        try:
            result = asyncio.run(self._async_test())
            self.after(0, self._on_test_success, result)
        except Exception as e:
            self.after(0, self._on_test_fail, str(e))

    async def _async_test(self) -> str:
        """Create provider and test connection."""
        from src.llm import create_provider

        provider = self._provider_var.get()
        model = self._model_var.get()
        api_key = self._api_key_var.get()

        # Resolve effective API key: UI > env var > empty
        info = PROVIDERS[provider]
        env_var = info.get("key_env")
        effective_key = api_key or (os.environ.get(env_var) if env_var else "") or ""

        # Build kwargs
        kwargs = {"api_key": effective_key, "model": model or "default"}

        # Pass base_url for custom (factory auto-injects for qwen/deepseek)
        if provider == "custom":
            kwargs["base_url"] = self._base_url_var.get()

        prov = create_provider(provider, **kwargs)
        return await prov.test_connection()

    def _on_test_success(self, msg: str):
        """Handle successful connection test."""
        self._test_btn.configure(state="normal", text=lang.tr("test_connection"))
        self._test_status.configure(
            text=lang.tr("test_success"),
            text_color="#2E7D32",
        )

    def _on_test_fail(self, error: str):
        """Handle failed connection test."""
        self._test_btn.configure(state="normal", text=lang.tr("test_connection"))
        self._test_status.configure(
            text=lang.tr("test_failed", error=error[:60]),
            text_color="#D32F2F",
        )

    # ── Getters ──────────────────────────────────────────────────────────

    @property
    def provider(self) -> str:
        return self._provider_var.get()

    @property
    def model(self) -> str:
        return self._model_var.get()

    @property
    def api_key(self) -> str:
        return self._api_key_var.get()

    @property
    def base_url(self) -> str:
        return self._base_url_var.get()

    def get_config(self) -> dict:
        cfg = {
            "provider": self.provider,
            "model": self.model,
            "api_key": self.api_key,
        }
        if PROVIDERS[self.provider].get("has_base_url"):
            cfg["base_url"] = self.base_url
        return cfg

    def set_api_key(self, key: str):
        self._api_key_var.set(key)
