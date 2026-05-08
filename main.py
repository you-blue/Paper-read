#!/usr/bin/env python3
"""PDF Paper Summarizer — Entry point.

Reads local PDF papers, uses configurable LLM backends to summarize them,
and saves the summaries as Markdown files to an Obsidian vault.
"""

import sys
import os

# When frozen by PyInstaller, use the EXE's directory as root
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.executable))
    # Also add the bundle temp dir to import path for bundled modules
    sys.path.insert(0, sys._MEIPASS)
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


def main():
    """Launch the GUI application."""
    try:
        from src.config.settings import ConfigManager, ConfigError
        from src.gui.app import PaperSummarizerApp
    except ImportError as e:
        print(f"Error: Missing dependencies. Please run: pip install -r requirements.txt")
        print(f"Details: {e}")
        sys.exit(1)

    try:
        config = ConfigManager()
    except ConfigError as e:
        print(f"Configuration Error: {e}")
        # Still launch with empty config so the user can configure via GUI
        config = None

    app = PaperSummarizerApp(config=config)
    app.mainloop()


if __name__ == "__main__":
    main()
