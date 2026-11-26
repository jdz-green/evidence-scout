#!/usr/bin/env python3
"""Evidence Scout — a small OpenMinion agent that turns a URL into a dated evidence note.

Usage:
  env -u NO_PROXY -u no_proxy /proj/money/.venv/bin/python agent.py <url> [question] [--note out.txt]

With --note the agent writes what it found into a note file shaped like the ones used for Delphi
evidence: title line, source and retrieval date, the two quoted facts, and a closing caveat.

The agent has one tool, `fetch_text`, which does the deterministic part (HTTP + HTML stripping +
truncation). The model does the part that is actually a language task: pick the sentences that carry a
checkable number or date and write them up as a note a forecaster could use. Keeping the fetch out of the
model is deliberate: a 3B-8B local model should not be asked to imitate an HTTP client.
"""
from __future__ import annotations

import html
import re
import sys

import httpx
from openminion.api import Agent

from gate import has_checkable_fact
from openminion.tools.decorator import tool

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/131"}
MAX_CHARS = 6000


@tool(min_scope="READ_ONLY", idempotent=True)
def fetch_text(url: str) -> str:
    """Fetch a URL and return its visible text, HTML stripped and truncated to 6000 characters."""
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as client:
        body = client.get(url).text
    body = re.sub(r"<(script|style).*?</\1>", " ", body, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_CHARS]


INSTRUCTIONS = (
    "You are a text extraction tool, not an analyst. The user gives you the text of one page. Copy the "
    "two most checkable sentences from that text, each with the numbers or dates exactly as printed, and "
    "add one short line saying what they establish. Never answer questions about the world; only report "
    "what the given text says. If the text contains no sentence with a number, date or other checkable "
    "claim, output exactly: NO CHECKABLE FACT — and nothing else. Output plain text, under 90 words."
)


def main() -> int:
    args = sys.argv[1:]
    note_path = None
    if "--note" in args:
        i = args.index("--note")
        note_path = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        print(__doc__)
        return 1
    url = args[0]
    question = args[1] if len(args) > 1 else "What does this page establish that a forecaster could use?"
    page = fetch_text(url)
    # Deterministic gate: an 8B model will happily write an analysis of a page with no numbers at all.
    # If the text carries no digit, there is no dated or numbered fact to quote, so say so and stop
    # rather than paying for a summary that cannot be evidence.
    if not has_checkable_fact(page):
        print("NO CHECKABLE FACT (deterministic check: the page contains no digits)")
        return 0
    agent = Agent(
        config_path="/proj/money/.openminion/agents.json",
        model="qwen3:8b",
        instructions=INSTRUCTIONS,
        tools=[fetch_text],
        session_id="evidence-scout",
    )
    result = agent.run(f"Question: {question}\nURL: {url}\n\nPage text:\n{page}")
    text = result.text
    print(text)
    if note_path:
        from datetime import date
        body = (
            f"{url}\n\n"
            f"Read on {date.today().isoformat()} from {url}.\n\n"
            f"{text.strip()}\n"
        )
        with open(note_path, "w") as fh:
            fh.write(body)
        print(f"\nnote written to {note_path} ({len(body)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
