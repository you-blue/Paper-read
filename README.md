# PDF Paper Summarizer

A desktop GUI tool that reads academic PDF papers, summarizes them using LLMs, and exports the summaries as Markdown files (with Obsidian vault support).

## Features

- **Multi-LLM support** — Anthropic Claude, OpenAI GPT, DeepSeek, Qwen, Ollama (local), and custom OpenAI-compatible endpoints
- **PDF intelligence** — automatic page-type detection (text vs. math/figures), hybrid rendering for accurate extraction
- **Obsidian integration** — configurable vault path, YAML frontmatter, filename templates
- **Customizable output** — language selection, tags, subdirectory organization
- **GUI application** — built with customtkinter, dark/light theme

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Configuration

Copy the example config and fill in your settings:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys and preferences
```

Supported providers: `anthropic`, `openai`, `deepseek`, `qwen`, `ollama`, `custom`.

## Project Structure

```
├── main.py                          # Entry point
├── config.example.yaml              # Configuration template
├── src/
│   ├── config/settings.py           # Configuration management
│   ├── gui/
│   │   ├── app.py                   # Main GUI application
│   │   ├── widgets/
│   │   │   ├── config_panel.py      # Settings panel
│   │   │   ├── pdf_selector.py      # PDF file browser
│   │   │   └── progress_panel.py    # Progress display
│   ├── llm/                         # LLM providers
│   │   ├── base.py                  # Abstract base provider
│   │   ├── anthropic_provider.py
│   │   ├── openai_provider.py
│   │   └── ollama_provider.py
│   ├── output/markdown.py           # Markdown writer
│   ├── pdf/                         # PDF processing
│   │   ├── detector.py              # Page type detection
│   │   ├── extractor.py             # Text extraction
│   │   └── renderer.py              # Page rendering
│   └── pipeline.py                  # Orchestration pipeline
└── utils/
    ├── helpers.py                   # Utility functions
    ├── i18n.py                      # Internationalization
    └── prompts.py                   # LLM prompt templates
```

## Requirements

- Python 3.10+
- Poppler (for PDF rendering) — install via `winget install oschwartz10612.Poppler` on Windows
