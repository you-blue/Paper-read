"""LLM provider initialization with config-driven factory."""

from __future__ import annotations


# Preset base URLs for OpenAI-compatible providers
PRESET_URLS = {
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "deepseek": "https://api.deepseek.com",
}


class UnknownProviderError(ValueError):
    """Raised when an unknown LLM provider is requested."""


def create_provider(provider_name: str, **kwargs):
    """Create an LLM provider instance by name.

    Providers are lazy-imported to avoid circular dependency issues.

    Supported providers:
        anthropic  — Claude API (Anthropic SDK)
        openai     — OpenAI GPT
        qwen       — Tongyi Qianwen (DashScope, OpenAI-compatible)
        deepseek   — DeepSeek API (OpenAI-compatible)
        custom     — Any OpenAI-compatible API (requires base_url)
        ollama     — Local Ollama

    Args:
        provider_name: Provider identifier.
        **kwargs: Provider-specific configuration.

    Returns:
        An LLMProvider instance.

    Raises:
        UnknownProviderError: If provider_name is not supported.
    """
    if provider_name == "anthropic":
        from src.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider(**kwargs)

    elif provider_name == "ollama":
        from src.llm.ollama_provider import OllamaProvider
        return OllamaProvider(**kwargs)

    elif provider_name in ("openai", "qwen", "deepseek", "custom"):
        from src.llm.openai_provider import OpenAIProvider

        # Inject preset base_url for qwen/deepseek if not explicitly provided
        if provider_name in PRESET_URLS and "base_url" not in kwargs:
            kwargs["base_url"] = PRESET_URLS[provider_name]

        # DeepSeek API doesn't support image inputs
        if provider_name == "deepseek":
            kwargs.setdefault("supports_vision", False)

        return OpenAIProvider(**kwargs)

    else:
        raise UnknownProviderError(
            f"Unknown LLM provider: {provider_name!r}. "
            f"Available: ['anthropic', 'openai', 'qwen', 'deepseek', 'custom', 'ollama']"
        )


__all__ = [
    "create_provider",
    "UnknownProviderError",
]
