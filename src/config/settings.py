"""Configuration loader/saver with environment variable fallback."""

import os
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""


def _env_var_for(provider: str) -> str | None:
    """Return the environment variable name for a provider's API key."""
    mapping = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "qwen": "QWEN_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    return mapping.get(provider)


def _resolve_api_key(cfg: dict, provider: str) -> str | None:
    """Resolve API key: env var > config file."""
    env_var = _env_var_for(provider)
    if env_var and (env_val := os.environ.get(env_var)):
        return env_val
    return cfg.get("llm", {}).get(provider, {}).get("api_key") or None


def _detect_poppler_path() -> Path | None:
    """Auto-detect Poppler (pdftoppm) installation path on Windows."""
    # Common WinGet installation path
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return None

    winget_root = (
        Path(local_app_data)
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )
    if not winget_root.exists():
        return None

    # Look for oschwartz10612.Poppler_* directories (depth may vary)
    for entry in winget_root.iterdir():
        if "poppler" not in entry.name.lower():
            continue
        # Search recursively for Library/bin/pdftoppm.exe (max depth 3)
        for root, _dirs, files in os.walk(str(entry)):
            if "pdftoppm.exe" in files and root.endswith(os.sep.join(["Library", "bin"])):
                return Path(root)

    return None


class ConfigManager:
    """Manages application configuration from YAML and environment variables."""

    def __init__(self, config_path: Path = CONFIG_PATH):
        self._config_path = Path(config_path)
        self._data: dict = self._load()

    # ── Loading ──────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not self._config_path.exists():
            raise ConfigError(f"Configuration file not found: {self._config_path}")

        with open(self._config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        # Inject resolved values
        self._inject_resolved(cfg)
        return cfg

    def _inject_resolved(self, cfg: dict) -> None:
        """Inject runtime-resolved values (API keys, poppler path) into config."""
        for provider in ("anthropic", "openai", "qwen", "deepseek"):
            resolved = _resolve_api_key(cfg, provider)
            if resolved:
                cfg.setdefault("llm", {}).setdefault(provider, {})["api_key"] = resolved

        # Poppler path
        poppler_path = _detect_poppler_path()
        if poppler_path:
            cfg.setdefault("pdf", {})["poppler_path"] = str(poppler_path)

    # ── Saving ───────────────────────────────────────────────────────────

    def save(self, updates: dict | None = None) -> None:
        """Save current config back to YAML file. Merges updates if provided."""
        if updates:
            self._deep_merge(self._data, updates)

        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self._data, f, default_flow_style=False, allow_unicode=True)

    @staticmethod
    def _deep_merge(base: dict, overrides: dict) -> None:
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value

    # ── Accessors ────────────────────────────────────────────────────────

    @property
    def data(self) -> dict:
        return self._data

    def get(self, *keys: str, default=None):
        """Deep access: cfg.get('llm', 'anthropic', 'model')"""
        current = self._data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
        return current

    def get_api_key(self, provider: str) -> str | None:
        return _resolve_api_key(self._data, provider)

    def get_poppler_path(self) -> str | None:
        return self.get("pdf", "poppler_path")

    def get_vault_path(self) -> Path:
        raw = self.get("output", "vault_path", default="D:/.Note/Study Note/Papers")
        return Path(raw)

    # ── Reload ───────────────────────────────────────────────────────────

    def reload(self) -> dict:
        self._data = self._load()
        return self._data
