"""Read one versioned topic without loading other languages into a model."""
import sys
from pathlib import Path

from i18n import LANGUAGES

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "knowledge"
TOPICS = ("ARCH", "SIGNALS", "ORDERS", "RECONNECT", "SUBACCOUNTS", "DATA", "AI", "MCP", "RELEASE", "BACKTEST", "VERIFY")


def knowledge_rule(language, topic):
    if language not in LANGUAGES or topic not in (*TOPICS, "index"):
        raise ValueError("Unknown language or knowledge topic")
    return (ROOT / language / f"{topic}.md").read_text(encoding="utf-8").strip()
