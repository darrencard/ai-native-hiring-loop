#!/usr/bin/env python3
"""Write the illustrative Acme score sheets from compact score tables.

  python3 evals/make_fixtures.py

Deterministic: no randomness, fixed timestamps. Every candidate, interviewer and score is invented.
Each evidence note quotes the rubric anchor the score matched, so the sheets stay readable.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent / "skills" / "ai-native-hiring-loop" / "assets" / "example" / "acme"
LOOP = json.loads((HERE / "loop.json").read_text(encoding="utf-8"))

# Who scores which stage. The work sample has two independent scorers.
PANEL = {"S1": ["I-A", "I-B"], "S2": ["I-C"], "S3": ["I-D"], "S4": ["I-E"]}
DAY = {"S1": "2026-11-16", "S2": "2026-11-17", "S3": "2026-11-17", "S4": "2026-11-18"}
DEBRIEF = "2026-11-20T17:00:00+00:00"

# candidate -> interviewer -> item -> score (1 to 4)
TABLES = {
    "K-01": {
        "I-A": {"W1": 4, "W2": 3, "W3": 4, "W4": 3},
        "I-B": {"W1": 3, "W2": 3, "W3": 4, "W4": 3},
        "I-C": {"Q1": 3, "Q2": 4, "Q3": 3, "Q4": 3},
        "I-D": {"Q5": 4, "Q6": 3, "Q7": 3, "Q8": 4},
        "I-E": {"Q9": 3, "Q10": 3},
    },
    "K-02": {
        "I-A": {"W1": 4, "W2": 3, "W3": 2, "W4": 4},
        "I-B": {"W1": 4, "W2": 3, "W3": 1, "W4": 3},
        "I-C": {"Q1": 4, "Q2": 3, "Q3": 4, "Q4": 3},
        "I-D": {"Q5": 4, "Q6": 3, "Q7": 2, "Q8": 2},
        "I-E": {"Q9": 4, "Q10": 4},
    },
    "K-03": {
        "I-A": {"W1": 3, "W2": 4, "W3": 3, "W4": 3},
        "I-B": {"W1": 1, "W2": 2, "W3": 3, "W4": 2},
        "I-C": {"Q1": 3, "Q2": 3, "Q3": 3, "Q4": 2},
        "I-D": {"Q5": 3, "Q6": 3, "Q7": 3, "Q8": 3},
        "I-E": {"Q9": 3, "Q10": 3},
    },
}


def anchors() -> dict[str, dict[str, str]]:
    comp = {c["id"]: c["anchors"] for c in LOOP["competencies"]}
    out: dict[str, dict[str, str]] = {}
    for s in LOOP["stages"]:
        for it in s.get("criteria", []):
            out[it["id"]] = it["anchors"]
        for q in s.get("questions", []):
            out[q["id"]] = comp[q["competency"]]
    return out


def stage_of() -> dict[str, str]:
    return {it["id"]: s["id"] for s in LOOP["stages"] for it in s.get("criteria", []) + s.get("questions", [])}


def sheet(candidate: str) -> dict:
    a, st = anchors(), stage_of()
    asked = {s["id"]: [it["id"] for it in s.get("criteria", []) + s.get("questions", [])] for s in LOOP["stages"]}
    scores = []
    for who, items in TABLES[candidate].items():
        for n, (item, score) in enumerate(items.items()):
            stage = st[item]
            assert who in PANEL[stage], (candidate, who, item)
            scores.append(
                {
                    "interviewer": who,
                    "stage": stage,
                    "item": item,
                    "score": score,
                    "submitted_at": f"{DAY[stage]}T{16 + n // 2:02d}:{(n % 2) * 30:02d}:00+00:00",
                    "evidence": f"Illustrative. Matched anchor {score}: {a[item][str(score)]}",
                }
            )
    return {
        "candidate": candidate,
        "illustrative": True,
        "timestamps_from": "form",
        "loop_version": LOOP["version"],
        "debrief_started_at": DEBRIEF,
        "asked": asked,
        "scores": scores,
    }


def export_csv() -> str:
    """The same scores as a form export: one row per score, as import-csv reads them."""
    cols = ("candidate", "interviewer", "stage", "item", "score", "submitted_at", "evidence")
    rows = [{"candidate": c, **{k: r[k] for k in cols[1:]}} for c in TABLES for r in sheet(c)["scores"]]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main() -> None:
    out = HERE / "scores"
    out.mkdir(exist_ok=True)
    for cand in TABLES:
        (out / f"{cand}.json").write_text(json.dumps(sheet(cand), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out / (cand + '.json')}")
    (HERE / "form-export.csv").write_text(export_csv(), encoding="utf-8")
    print(f"wrote {HERE / 'form-export.csv'}")


if __name__ == "__main__":
    main()
