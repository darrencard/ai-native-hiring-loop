#!/usr/bin/env python3
"""Command line for the AI-native hiring loop.

  python3 scripts/run.py check-design LOOP.json [--kit OUT.md]
  python3 scripts/run.py score LOOP.json SHEET.json [SHEET.json ...] --out DIR
  python3 scripts/run.py check-note DIR/results.json NOTE.md

check-design validates the loop and, if it passes, writes the interview kit.
score runs every guardrail, combines the scores and writes results.json, ledger.csv
and packet.md to DIR. Any guardrail error stops it before anything is written.
check-note blocks a debrief note with an uncomputed figure, a wrong band or an overclaim.

Exit codes: 0 passed, 1 a guardrail or check failed, 2 a file could not be read.
Standard library only. Python 3.9 or later. No network calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate import interviewer_drift, score_candidate  # noqa: E402
from guardrails import check_design, check_pool, check_sheet, errors  # noqa: E402
from packet import check_note, ledger_csv, render_kit, render_packet  # noqa: E402
from schema import SchemaError, check_loop_shape, check_scores_shape, load_json  # noqa: E402


def _print(findings: list[dict[str, str]]) -> None:
    for f in findings:
        print(f"{f['level'].upper()} {f['rule']} [{f['where']}] {f['message']}")


def _load_loop(path: str) -> dict:
    loop = load_json(path)
    shape = check_loop_shape(loop)
    if shape:
        raise SchemaError("loop shape:\n  " + "\n  ".join(shape))
    return loop


def cmd_check_design(args: argparse.Namespace) -> int:
    loop = _load_loop(args.loop)
    findings = check_design(loop)
    _print(findings)
    if errors(findings):
        print(f"BLOCKED: {len(errors(findings))} design error(s). Fix the loop before using it.")
        return 1
    if args.kit:
        Path(args.kit).write_text(render_kit(loop), encoding="utf-8")
        print(f"Wrote {args.kit}")
    print("Design passed.")
    return 0


def build(loop: dict, sheet_paths: list[str]) -> dict:
    """Run every guardrail and, if none fails, every computation. Pure: writes nothing."""
    findings = check_design(loop)
    sheets: list[tuple[dict, str]] = []
    for p in sheet_paths:
        sheet = load_json(p)
        shape = check_scores_shape(sheet)
        if shape:
            raise SchemaError(f"{p} shape:\n  " + "\n  ".join(shape))
        sheets.append((sheet, Path(p).name))
    sheets.sort(key=lambda x: x[0]["candidate"])
    for sheet, _ in sheets:
        findings += check_sheet(loop, sheet)
    findings += check_pool(loop, [s for s, _ in sheets])
    if errors(findings):
        return {"findings": findings, "blocked": True}
    results = [score_candidate(loop, s, name) for s, name in sheets]
    pool_flags, pool_ledger = interviewer_drift(loop, sheets)
    ledger = [row for r in results for row in r["ledger"]] + pool_ledger
    return {"findings": findings, "blocked": False, "results": results, "pool_flags": pool_flags, "ledger": ledger}


def cmd_score(args: argparse.Namespace) -> int:
    loop = _load_loop(args.loop)
    out = build(loop, args.sheets)
    _print(out["findings"])
    if out["blocked"]:
        print(f"BLOCKED: {len(errors(out['findings']))} guardrail error(s). No figures were computed.")
        return 1
    d = Path(args.out)
    d.mkdir(parents=True, exist_ok=True)
    payload = {
        "loop": args.loop,
        "results": [{k: v for k, v in r.items() if k != "ledger"} for r in out["results"]],
        "pool_flags": out["pool_flags"],
        "ledger": out["ledger"],
    }
    (d / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (d / "ledger.csv").write_text(ledger_csv(out["ledger"]), encoding="utf-8")
    (d / "packet.md").write_text(render_packet(loop, out["results"], out["findings"], out["pool_flags"]), encoding="utf-8")
    for r in out["results"]:
        print(f"{r['candidate']}: overall {r['overall'] or 'none'}, {r['band']}, {len(r['flags'])} item(s) to discuss")
    print(f"Wrote {d / 'results.json'}, {d / 'ledger.csv'} and {d / 'packet.md'}")
    return 0


def cmd_check_note(args: argparse.Namespace) -> int:
    payload = load_json(args.results)
    loop = _load_loop(payload["loop"]) if not args.loop else _load_loop(args.loop)
    text = Path(args.note).read_text(encoding="utf-8")
    findings = check_note(text, loop, payload["results"], payload["ledger"])
    for f in findings:
        print(f"ERROR {f['rule']} [{f['where']}] {f['message']}")
    if findings:
        print(f"BLOCKED: {len(findings)} problem(s) in the note.")
        return 1
    print("Note passed.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("check-design", help="validate a loop design and write the interview kit")
    a.add_argument("loop")
    a.add_argument("--kit", help="write the interview kit (Markdown) here")
    a.set_defaults(fn=cmd_check_design)
    b = sub.add_parser("score", help="run the guardrails and combine scores")
    b.add_argument("loop")
    b.add_argument("sheets", nargs="+")
    b.add_argument("--out", required=True)
    b.set_defaults(fn=cmd_score)
    c = sub.add_parser("check-note", help="check a debrief note against the computed figures")
    c.add_argument("results")
    c.add_argument("note")
    c.add_argument("--loop", help="the loop design, if not at the path recorded in results.json")
    c.set_defaults(fn=cmd_check_note)
    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except SchemaError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
