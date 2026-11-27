#!/usr/bin/env python3
"""Command line for the AI-native hiring loop.

  python3 scripts/run.py demo --out DIR
  python3 scripts/run.py new --role pm|designer|engineer --out LOOP.json
  python3 scripts/run.py check-design LOOP.json [--kit OUT.md]
  python3 scripts/run.py blank LOOP.json --candidate ID --out SHEET.json
  python3 scripts/run.py import-csv LOOP.json EXPORT.csv --debrief ID=TIME [...] --timestamps-from ats|form|self-reported [--map OURS=THEIRS ...] --out DIR
  python3 scripts/run.py score LOOP.json SHEET.json [SHEET.json ...] --out DIR
  python3 scripts/run.py check-note DIR/results.json NOTE.md

demo runs the bundled, illustrative Acme example end to end (about a second).
new copies a starter loop for a role family; edit it, then run check-design.
blank writes an empty score sheet for one candidate, with every item listed.
import-csv turns a form or tracker export (one row per score) into one sheet per candidate.
check-design validates the loop and, if it passes, writes the interview kit.
score runs every guardrail, combines the scores and writes results.json, ledger.csv,
packet.md and packet.html (one self-contained page in the Leader Report style) to DIR. Any guardrail error stops it before anything is written.
check-note blocks a debrief note with an uncomputed figure, a wrong band or an overclaim.

Exit codes: 0 passed, 1 a guardrail or check failed, 2 a file could not be read.
Standard library only. Python 3.11 or later. No network calls.
"""

from __future__ import annotations

import sys

# Check the interpreter before importing or reading anything (stop with a plain message, not an import error,
# on the macOS system Python).
if sys.version_info < (3, 11):  # noqa: UP036
    sys.exit("ai-native-hiring-loop needs Python 3.11 or later; try python3.12 (this is " + sys.version.split()[0] + ")")

import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aggregate import guardrail_figures, interviewer_drift, score_candidate, show  # noqa: E402
from guardrails import check_design, check_pool, check_sheet, decision_owner, errors, finding  # noqa: E402
from importer import read_rows, to_sheets  # noqa: E402
from packet import check_note, ledger_csv, render_kit, render_packet  # noqa: E402
from render_html import page  # noqa: E402
from schema import SchemaError, check_loop_shape, check_scores_shape, load_json, stage_items  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
EXAMPLE = ASSETS / "example" / "acme"
ROLES = ("pm", "designer", "engineer")


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
    if not decision_owner(loop):
        findings = [f for f in findings if f["rule"] != "decision-owner"]
        findings.append(finding("decision-owner", "error", "decision", "name the hiring manager in decision.owner; the packet says who decides"))
    if errors(findings):
        return {"findings": findings, "blocked": True}
    results = [score_candidate(loop, s, name) for s, name in sheets]
    pool_flags, pool_ledger = interviewer_drift(loop, sheets)
    guards = guardrail_figures(loop, sheets)
    ledger = [row for r in results for row in r["ledger"]] + pool_ledger + guards
    return {"findings": findings, "blocked": False, "results": results, "pool_flags": pool_flags, "ledger": ledger, "guardrails": guards}


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
    (d / "packet.md").write_text(render_packet(loop, out["results"], out["findings"], out["pool_flags"], out["guardrails"]), encoding="utf-8")
    html = page(loop, out["results"], out["findings"], out["pool_flags"], out["ledger"], out["guardrails"])
    (d / "packet.html").write_text(html, encoding="utf-8")
    for r in out["results"]:
        print(f"{r['candidate']}: overall {show(r['overall']) or 'none'}, {r['band']}, {len(r['flags'])} item(s) to discuss")
    print(f"Wrote {d / 'results.json'}, {d / 'ledger.csv'}, {d / 'packet.md'} and {d / 'packet.html'}")
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


def cmd_demo(args: argparse.Namespace) -> int:
    d = Path(args.out)
    d.mkdir(parents=True, exist_ok=True)
    loop_path = str(EXAMPLE / "loop.json")
    code = cmd_check_design(argparse.Namespace(loop=loop_path, kit=str(d / "kit.md")))
    if code:
        return code
    sheets = sorted(str(p) for p in (EXAMPLE / "scores").glob("*.json"))
    return cmd_score(argparse.Namespace(loop=loop_path, sheets=sheets, out=str(d)))


def cmd_new(args: argparse.Namespace) -> int:
    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"ERROR {out} exists; pass --force to replace it", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ASSETS / "starters" / f"{args.role}.json", out)
    print(f"Wrote {out}. Replace the outcomes with your own, name the hiring manager in decision.owner, adjust weights and anchors, then run check-design.")
    return 0


def cmd_blank(args: argparse.Namespace) -> int:
    loop = _load_loop(args.loop)
    rows = []
    for s in loop["stages"]:
        items = s.get("criteria") if s["kind"] == "work_sample" else s.get("questions")
        for _ in range(s.get("min_scorers", 1)):
            rows += [{"interviewer": "", "stage": s["id"], "item": it["id"], "score": None, "submitted_at": "", "evidence": ""} for it in items]
    sheet = {
        "candidate": args.candidate,
        "loop_version": loop.get("version"),
        "timestamps_from": "self-reported",
        "debrief_started_at": "",
        "asked": stage_items(loop),
        "scores": rows,
    }
    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"ERROR {out} exists; pass --force to replace it", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} with {len(rows)} rows to fill. Fill every row and debrief_started_at; a blank row blocks scoring.")
    print("Set timestamps_from to ats or form if the times come from a system clock.")
    return 0


def cmd_import_csv(args: argparse.Namespace) -> int:
    loop = _load_loop(args.loop)
    debriefs = {}
    for pair in args.debrief:
        cand, sep, when = pair.partition("=")
        if not sep:
            raise SchemaError(f"--debrief {pair!r}: use CANDIDATE=TIME")
        debriefs[cand.strip()] = when.strip()
    mapping = {}
    for pair in args.map:
        ours, sep, theirs = pair.partition("=")
        if not sep:
            raise SchemaError(f"--map {pair!r}: use OUR_COLUMN=YOUR_COLUMN, for example candidate=Candidate ID")
        mapping[ours.strip()] = theirs.strip()
    sheets = to_sheets(loop, read_rows(args.csv, mapping), debriefs, args.timestamps_from)
    d = Path(args.out)
    d.mkdir(parents=True, exist_ok=True)
    for sheet in sheets:
        path = d / f"{sheet['candidate']}.json"
        path.write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path} ({len(sheet['scores'])} scores)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("demo", help="run the illustrative Acme example end to end")
    m.add_argument("--out", required=True)
    m.set_defaults(fn=cmd_demo)
    n = sub.add_parser("new", help="start a loop from a role starter")
    n.add_argument("--role", choices=ROLES, required=True)
    n.add_argument("--out", required=True)
    n.add_argument("--force", action="store_true")
    n.set_defaults(fn=cmd_new)
    k = sub.add_parser("blank", help="write an empty score sheet for one candidate")
    k.add_argument("loop")
    k.add_argument("--candidate", required=True)
    k.add_argument("--out", required=True)
    k.add_argument("--force", action="store_true")
    k.set_defaults(fn=cmd_blank)
    i = sub.add_parser("import-csv", help="turn a form or tracker export into score sheets")
    i.add_argument("loop")
    i.add_argument("csv")
    i.add_argument("--debrief", action="append", default=[], help="CANDIDATE=ISO time the debrief started; repeat per candidate")
    i.add_argument("--timestamps-from", required=True, choices=("ats", "form", "self-reported"))
    i.add_argument("--map", action="append", default=[], help="OUR_COLUMN=YOUR_COLUMN when the export names a column differently; repeat per column")
    i.add_argument("--out", required=True)
    i.set_defaults(fn=cmd_import_csv)
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
