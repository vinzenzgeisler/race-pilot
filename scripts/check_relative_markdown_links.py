#!/usr/bin/env python3
"""Fail when a relative Markdown link points at a missing repository file."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for heading in HEADING.findall(text):
        label = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        label = label.replace("`", "").strip().lower()
        base = re.sub(r"[^\w\- ]", "", label, flags=re.UNICODE).replace(" ", "-")
        base = re.sub(r"-+", "-", base).strip("-")
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def main() -> int:
    failures: list[str] = []
    checked = 0
    for markdown in sorted(ROOT.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part, _, fragment = target.partition("#")
            path_part = unquote(path_part)
            fragment = unquote(fragment)
            if not path_part:
                continue
            checked += 1
            resolved = (markdown.parent / path_part).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(f"{markdown.relative_to(ROOT)}: link escapes repository: {target}")
                continue
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(ROOT)}: missing target: {target}")
                continue
            if fragment and resolved.suffix.lower() == ".md":
                anchors = heading_anchors(resolved.read_text(encoding="utf-8"))
                if fragment not in anchors:
                    failures.append(f"{markdown.relative_to(ROOT)}: missing anchor: {target}")
    if failures:
        print("relative Markdown link check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(f"relative Markdown link check passed: {checked} relative links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
