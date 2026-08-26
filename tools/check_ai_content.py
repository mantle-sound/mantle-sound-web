#!/usr/bin/env python3
"""Scan Lektor content with Pangram AI detection.

Reads prose fields from .lr files under content/, submits them to the Pangram
Bulk API, and prints a summary. Use before publishing when you want a check that
site copy was written by a human.

Requires pangram-sdk and PANGRAM_API_KEY in the environment (or --api-key).

    export PANGRAM_API_KEY=...
    pip install pangram-sdk
    python3 tools/check_ai_content.py
    python3 tools/check_ai_content.py content/blog/mission-of-foss
    python3 tools/check_ai_content.py --fail-on ai,mixed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTENT = REPO / "content"

PROSE_FIELDS = ("body", "intro", "description", "subtitle")
FIELD_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$")
HIDDEN = re.compile(r"^_hidden:\s*yes\s*$", re.MULTILINE | re.IGNORECASE)
HTML_TAG = re.compile(r"<[^>]+>")
FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
PRE_BLOCK = re.compile(r"<pre\b[^>]*>.*?</pre>", re.DOTALL | re.IGNORECASE)
SOFTWARE_EXAMPLE = re.compile(
    r'<pre class="software-example">.*?</pre>', re.DOTALL | re.IGNORECASE
)
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class DocumentField:
    path: Path
    field: str
    text: str


def parse_lr_fields(path: Path) -> dict[str, str]:
    """Return single- and multi-line metadata fields from a .lr file."""
    raw = path.read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is None:
            return
        fields[current_key] = "\n".join(current_lines).strip()
        current_key = None
        current_lines = []

    for line in raw.splitlines():
        if line.strip() == "---":
            flush()
            continue
        match = FIELD_KEY.match(line)
        if match and not line.startswith(" "):
            flush()
            key, rest = match.group(1), match.group(2)
            if rest:
                fields[key] = rest.strip()
            else:
                current_key = key
            continue
        if current_key is not None:
            current_lines.append(line)

    flush()
    return fields


def plain_prose(text: str) -> str:
    """Drop markup and code so Pangram sees narrative copy, not shell examples."""
    text = FENCED_CODE.sub(" ", text)
    text = PRE_BLOCK.sub(" ", text)
    text = SOFTWARE_EXAMPLE.sub(" ", text)
    text = HTML_TAG.sub(" ", text)
    text = MARKDOWN_IMAGE.sub(" ", text)
    return WHITESPACE.sub(" ", text).strip()


def collect_documents(
    roots: list[Path],
    *,
    min_chars: int,
    include_hidden: bool,
) -> list[DocumentField]:
    docs: list[DocumentField] = []
    seen: set[Path] = set()

    for root in roots:
        root = root.resolve()
        if root.is_file():
            paths = [root]
        else:
            paths = sorted(root.rglob("contents.lr"))

        for path in paths:
            if path in seen:
                continue
            seen.add(path)

            raw = path.read_text(encoding="utf-8")
            if not include_hidden and HIDDEN.search(raw):
                continue

            fields = parse_lr_fields(path)
            for name in PROSE_FIELDS:
                value = fields.get(name)
                if not value:
                    continue
                prose = plain_prose(value)
                if len(prose) < min_chars:
                    continue
                docs.append(
                    DocumentField(
                        path=path.relative_to(REPO),
                        field=name,
                        text=prose,
                    )
                )
    return docs


def choose_model(client, requested: str | None) -> str:
    models = client.list_models()
    if not models:
        raise SystemExit("Pangram returned no models for this API key.")
    if requested:
        if requested not in models:
            raise SystemExit(
                f"Model {requested!r} is not enabled. Available: {', '.join(models)}"
            )
        return requested
    if "default" in models:
        return "default"
    return models[0]


def run_check(
    docs: list[DocumentField],
    *,
    api_key: str | None,
    model: str | None,
    fail_on: set[str],
) -> list[dict]:
    try:
        from pangram import Pangram
    except ImportError as exc:
        raise SystemExit(
            "pangram-sdk is not installed. Run: pip install pangram-sdk"
        ) from exc

    client = Pangram(api_key=api_key) if api_key else Pangram()
    selected_model = choose_model(client, model)

    items = [
        {"id": f"{doc.path}:{doc.field}", "text": doc.text}
        for doc in docs
    ]
    bulk = client.submit_bulk(items=items, model=selected_model)
    bulk_id = bulk["bulk_id"]
    client.wait_for_bulk(bulk_id)
    results = client.get_bulk_results(bulk_id)

    by_id = {doc.path.as_posix() + ":" + doc.field: doc for doc in docs}
    rows: list[dict] = []

    for item in results["items"]:
        doc = by_id.get(item["id"])
        if doc is None or item["result"] is None:
            continue
        result = item["result"]
        row = {
            "path": doc.path.as_posix(),
            "field": doc.field,
            "chars": len(doc.text),
            "prediction_short": result.get("prediction_short"),
            "fraction_ai": result.get("fraction_ai"),
            "fraction_ai_assisted": result.get("fraction_ai_assisted"),
            "fraction_human": result.get("fraction_human"),
            "prediction": result.get("prediction"),
        }
        if result.get("dashboard_link"):
            row["dashboard_link"] = result["dashboard_link"]
        rows.append(row)

    for failed in results["failed_items"]:
        rows.append(
            {
                "path": failed.get("id", "?"),
                "field": "?",
                "error": failed.get("error"),
            }
        )

    rows.sort(key=lambda row: (row.get("path", ""), row.get("field", "")))
    return rows


def print_human(rows: list[dict], *, fail_on: set[str]) -> int:
    flagged = 0
    errors = 0

    for row in rows:
        if "error" in row:
            errors += 1
            print(f"ERROR  {row['path']}: {row['error']}")
            continue

        label = (row.get("prediction_short") or "?").lower()
        ai = row.get("fraction_ai")
        assisted = row.get("fraction_ai_assisted")
        human = row.get("fraction_human")
        parts = [f"{row['path']} [{row['field']}]"]
        parts.append(row.get("prediction_short") or "?")
        if ai is not None:
            parts.append(f"ai={ai:.0%}")
        if assisted is not None:
            parts.append(f"assisted={assisted:.0%}")
        if human is not None:
            parts.append(f"human={human:.0%}")
        print("  ".join(parts))

        if label in fail_on:
            flagged += 1

    print()
    print(f"Checked {len(rows) - errors} field(s); {flagged} flagged; {errors} error(s).")
    if errors:
        return 2
    if flagged:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Content paths to scan (default: content/)",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=200,
        help="Skip fields shorter than this after markup is removed (default: 200)",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Also scan pages marked _hidden: yes",
    )
    parser.add_argument(
        "--model",
        help="Pangram model selector (default: list_models()[0] or 'default')",
    )
    parser.add_argument(
        "--api-key",
        help="Pangram API key (default: PANGRAM_API_KEY environment variable)",
    )
    parser.add_argument(
        "--fail-on",
        default="ai,mixed",
        help="Comma-separated prediction_short values that exit 1 (default: ai,mixed)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a table",
    )
    args = parser.parse_args(argv)

    roots = [REPO / p if not p.is_absolute() else p for p in args.paths]
    if not roots:
        roots = [CONTENT]

    docs = collect_documents(
        roots,
        min_chars=args.min_chars,
        include_hidden=args.include_hidden,
    )
    if not docs:
        print("No prose fields matched the scan criteria.", file=sys.stderr)
        return 0

    fail_on = {part.strip().lower() for part in args.fail_on.split(",") if part.strip()}
    rows = run_check(
        docs,
        api_key=args.api_key,
        model=args.model,
        fail_on=fail_on,
    )

    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        if any("error" in row for row in rows):
            return 2
        if any(
            (row.get("prediction_short") or "").lower() in fail_on for row in rows
        ):
            return 1
        return 0

    return print_human(rows, fail_on=fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
