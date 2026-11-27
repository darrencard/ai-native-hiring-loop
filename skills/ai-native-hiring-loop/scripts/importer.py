"""Turn a form or applicant-tracking-system export (CSV, one row per score) into score sheets.

Columns (header row required, extra columns ignored and never read):
  candidate, interviewer, stage, item, score, submitted_at, evidence
If your tool names a column differently, map it (--map candidate="Candidate ID") rather than editing the export.

What each stage "asked" is taken from the items scored for that candidate. So a skipped
question is missing from the sheet and the same-questions guardrail blocks it; nothing is
filled in on the candidate's behalf. Standard library only.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from schema import TIMESTAMP_SOURCES, SchemaError, parse_time

COLUMNS = ("candidate", "interviewer", "stage", "item", "score", "submitted_at", "evidence")


def read_rows(path: str | Path, mapping: dict[str, str] | None = None) -> list[dict[str, str]]:
    """Read the export. mapping says which of the file's columns holds each of ours, for example {"candidate": "Candidate ID"}."""
    p = Path(path)
    mapping = {k.strip().lower(): v.strip().lower() for k, v in (mapping or {}).items()}
    unknown = sorted(set(mapping) - set(COLUMNS))
    if unknown:
        raise SchemaError(f"--map names {unknown}; the columns are {list(COLUMNS)}")
    theirs = {v: k for k, v in mapping.items()}
    try:
        with p.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            header = [theirs.get(h.strip().lower(), h.strip().lower()) for h in reader.fieldnames or []]
            missing = [c for c in COLUMNS if c not in header]
            if missing:
                raise SchemaError(f"{p}: missing columns {missing}; map yours with --map {missing[0]}=YOUR_COLUMN")
            reader.fieldnames = header
            return [{k: (v or "").strip() for k, v in row.items() if k in COLUMNS} for row in reader]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise SchemaError(f"{p}: cannot read CSV ({exc})") from exc


def _score(value: str, where: str) -> int:
    try:
        n = int(value)
    except ValueError:
        raise SchemaError(f"{where}: score {value!r} is not a whole number") from None
    return n


def to_sheets(loop: dict[str, Any], rows: list[dict[str, str]], debriefs: dict[str, str], timestamps_from: str) -> list[dict[str, Any]]:
    """Group rows by candidate into sheets. Every candidate needs a debrief start time."""
    if timestamps_from not in TIMESTAMP_SOURCES:
        raise SchemaError(f"timestamps_from must be one of {list(TIMESTAMP_SOURCES)}")
    order = [s["id"] for s in loop["stages"]]
    by_cand: dict[str, list[tuple[int, dict[str, str]]]] = {}
    for n, r in enumerate(rows, 2):  # row 1 is the header
        if not r["candidate"]:
            raise SchemaError(f"row {n}: no candidate")
        by_cand.setdefault(r["candidate"], []).append((n, r))
    missing = sorted(set(by_cand) - set(debriefs))
    if missing:
        raise SchemaError(f"no debrief start time for {missing}; pass --debrief CANDIDATE=YYYY-MM-DDTHH:MM:SS+00:00")
    sheets = []
    for cand in sorted(by_cand):
        if parse_time(debriefs[cand]) is None:
            raise SchemaError(f"{cand}: debrief time {debriefs[cand]!r} is not ISO 8601 with a UTC offset")
        asked: dict[str, list[str]] = {}
        scores = []
        for n, r in by_cand[cand]:
            asked.setdefault(r["stage"], [])
            if r["item"] not in asked[r["stage"]]:
                asked[r["stage"]].append(r["item"])
            scores.append(
                {
                    "interviewer": r["interviewer"],
                    "stage": r["stage"],
                    "item": r["item"],
                    "score": _score(r["score"], f"row {n}"),
                    "submitted_at": r["submitted_at"],
                    "evidence": r["evidence"],
                }
            )
        asked = {sid: asked[sid] for sid in sorted(asked, key=lambda s: order.index(s) if s in order else len(order))}
        sheets.append(
            {
                "candidate": cand,
                "loop_version": loop.get("version"),
                "timestamps_from": timestamps_from,
                "debrief_started_at": debriefs[cand],
                "asked": asked,
                "scores": scores,
            }
        )
    return sheets
