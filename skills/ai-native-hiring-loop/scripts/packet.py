"""Render the interview kit and the calibration packet, write the ledger, and check a debrief note.

- render_kit: the loop as interviewers use it (scorecard, tasks, rubrics, questions, calibration).
  Every candidate gets this one kit, so every candidate gets the same questions.
- render_packet: each candidate's figures, band and flags, and the calibration agenda.
- check_note: blocks a debrief note that prints a figure the code did not compute,
  states a band the code did not reach, or uses an overclaim or a banned criterion.

Standard library only.
"""

from __future__ import annotations

import csv
import io
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any

from aggregate import DRIFT_FLAG, NEAR_BAR, fmt
from guardrails import banned_terms

LEDGER_FIELDS = ("id", "candidate", "figure", "value", "unit", "source", "window_from", "window_to", "as_of", "method")

OVERCLAIMS = (
    "will succeed",
    "will be successful",
    "guaranteed",
    "guarantee",
    "proven",
    "no doubt",
    "certain to",
    "best candidate",
    "best hire",
    "top performer",
    "10x",
    "predicts",
    "a sure thing",
)
BAND_PHRASES = {
    "meets bar": re.compile(r"\bmeets (?:the )?bar\b|\babove (?:the )?bar\b|\bclears (?:the )?bar\b"),
    "below bar": re.compile(r"\bbelow (?:the )?bar\b|\bunder (?:the )?bar\b|\bmisses (?:the )?bar\b"),
    "insufficient evidence": re.compile(r"\binsufficient evidence\b|\bnot enough evidence\b"),
}
# Identifiers such as K-01, C2, Q10 or S3 carry digits but are not figures.
IDENT = re.compile(r"\b[A-Za-z]+-?\d+(?:\.\d+)*\b")
NUMBER = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")


def cell(text: Any) -> str:
    """Make a value safe for one Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def render_kit(loop: dict[str, Any]) -> str:
    role = loop["role"]
    lines = [f"# Hiring loop: {role['title']}, {role['level']}", ""]
    if loop.get("illustrative"):
        lines += ["*Illustrative. Every name, figure and score in this kit is invented.*", ""]
    if loop.get("starter"):
        lines += ["*Starter loop. Replace the outcomes with your own and adjust weights and anchors before using it.*", ""]
    lines += [f"Team: {role['team']}. Loop version {loop.get('version', 'unversioned')}.", ""]
    lines += ["## Outcomes for the first year", "", "| ID | Outcome | Measure | By month |", "|---|---|---|---|"]
    lines += [f"| {o['id']} | {cell(o['text'])} | {cell(o['measure'])} | {o['by_month']} |" for o in loop["outcomes"]]
    lines += ["", "## Scorecard", "", "| ID | Competency | Weight | Floor | Serves | AI judgment |", "|---|---|---|---|---|---|"]
    for c in loop["competencies"]:
        floor = c.get("floor", "none")
        lines.append(f"| {c['id']} | {cell(c['name'])} | {c['weight']} | {floor} | {', '.join(c.get('outcomes', []))} | {c.get('ai_judgment') or 'none'} |")
    lines.append("")
    for c in loop["competencies"]:
        lines += [f"### {c['id']} {c['name']}", ""]
        if c.get("description"):
            lines += [c["description"], ""]
        lines += [f"- **{k}:** {c['anchors'][k]}" for k in ("1", "2", "3", "4")]
        lines.append("")
    for s in loop["stages"]:
        lines += [f"## {s['id']} {s['name']} ({s['minutes']} minutes)", ""]
        if s["kind"] == "work_sample":
            lines += ["**Task.** " + s["task"], ""]
            for it in s["criteria"]:
                tag = f", tests {it['ai_judgment']}" if it.get("ai_judgment") else ""
                lines += [f"### {it['id']} {it['text']} ({it['competency']}{tag})", ""]
                lines += [f"- **{k}:** {it['anchors'][k]}" for k in ("1", "2", "3", "4")]
                lines.append("")
        else:
            lines += ["Ask every question, in this order, to every candidate. Score each against its competency's anchors.", ""]
            for n, q in enumerate(s["questions"], 1):
                lines.append(f"{n}. **{q['id']}** ({q['competency']}) {q['text']}")
                lines += [f"   - Follow-up: {f}" for f in q.get("follow_ups", [])]
            lines.append("")
    cal = loop["calibration"]
    lines += [
        "## Calibration",
        "",
        f"Bar: {cal['bar']} on a 1 to 4 scale. Panel: at least {cal['panel_min']} interviewers. Spread flag: {cal['spread_flag']} points.",
        "",
    ]
    lines += [f"{n}. {step}" for n, step in enumerate(cal["steps"], 1)]
    lines.append("")
    return "\n".join(lines)


def view(loop: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, str]], pool_flags: list[dict[str, str]], guards: list[dict[str, Any]]) -> dict[str, Any]:
    """Everything the packet prints, in one place, so the Markdown and the HTML page say the same thing.

    Every number in it is a ledger value or a value from the loop design. No text here is written by a model.
    """
    role = loop["role"]
    g = {r["id"].removeprefix("pool."): r for r in guards}
    decision = loop.get("decision") or {}
    owner = decision.get("owner", "").strip()
    sources = sorted({r.get("timestamps_from") or "not stated" for r in results})
    n, items = g["candidates"]["value"], g["items"]["value"]
    who = f"{owner} ({decision['role']})" if decision.get("role") else owner
    lede = f"{n} candidates, the same {items} items each, scored in code against the rubric before the debrief. {who} makes the hire decision."
    candidates = []
    for r in results:
        floors = [f for f in r["flags"] if f["rule"] == "floor"]
        if r["band"] == "insufficient evidence":
            why = "At least one competency has no eligible score, so there is no overall score."
        elif floors:
            under = "; ".join(f["message"].split(";")[0] for f in floors)
            if Fraction(r["overall"]) < Fraction(r["bar"]):
                why = f"Overall {r['overall']} is under the bar of {r['bar']}, and {under}."
            else:
                why = f"Overall {r['overall']} clears the bar of {r['bar']}, but {under}, so the band is below bar."
        elif r["band"] == "below bar":
            why = f"Overall {r['overall']} is under the bar of {r['bar']}."
        else:
            why = f"Overall {r['overall']} against a bar of {r['bar']}, with no competency under its floor."
        candidates.append({**r, "why": why})
    guardrails = [
        ("Same questions", f"{g['same_questions']['value']} of {n} candidates got all {items} items, in order. A skipped or added question blocks the packet."),
        (
            "Scores before discussion",
            f"{g['counted']['value']} scores counted; {g['after_debrief']['value']} recorded at or after the debrief started. Score times from: {', '.join(sources)}.",
        ),
        ("Independent scoring", f"Every work-sample criterion has at least {g['work_sample_scorers']['value']} scorers who did not confer."),
        ("No protected attributes", "Sheets carry candidate codes only. A field for a name, age, photo or school, or evidence that mentions one, blocks the packet."),
        ("No banned criteria", "Criteria that judge the person, not the work (fit, a hunch, the right school), are blocked in the loop, in the evidence and in the decision note."),
    ]
    warnings = [f"{f['where']}: {f['message']}" for f in findings if f["level"] == "warning"]
    return {
        "title": f"Hiring loop: {role['title']}",
        "level": role["level"],
        "team": role["team"],
        "version": loop.get("version", "unversioned"),
        "illustrative": bool(loop.get("illustrative")),
        "as_of": g["candidates"]["as_of"],
        "lede": lede,
        "owner": who,
        "by": decision.get("by", ""),
        "decision": "Hire or not, for each candidate. The band says how the evidence compares with the bar this loop set. It does not decide, and it does not predict performance.",
        "bar": results[0]["bar"] if results else fmt(Fraction(str(loop["calibration"]["bar"]))),
        "candidates": candidates,
        "pool_flags": pool_flags,
        "guardrails": guardrails,
        "warnings": warnings,
        "steps": loop["calibration"]["steps"],
        "foot": "Code computed every figure from the score sheets named in the ledger; the model wrote none. A named hiring manager decides and owns the note.",
    }


def render_packet(loop: dict[str, Any], results: list[dict[str, Any]], findings: list[dict[str, str]], pool_flags: list[dict[str, str]], guards: list[dict[str, Any]]) -> str:
    """The plain-text twin of the HTML page."""
    v = view(loop, results, findings, pool_flags, guards)
    lines = [f"# {v['title']}", ""]
    if v["illustrative"]:
        lines += ["*Illustrative. Acme is an invented company; every candidate, interviewer, name and score here is invented.*", ""]
    lines += [f"{v['level']}. {v['team']} Loop version {v['version']}. Debrief {v['as_of'][:10]}.", "", v["lede"], ""]
    by = f" By {v['by']}." if v["by"] else ""
    lines += ["## Decision", "", f"**Owner: {v['owner']}.**{by} {v['decision']}", ""]
    lines += [
        "## Candidates against the bar",
        "",
        "| Candidate | Overall | Bar | Band | Evals | Cost | Restraint | Counted | Not counted |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in v["candidates"]:
        ai = {k: x or "none" for k, x in r["ai_judgment"].items()}
        cols = [r["candidate"], r["overall"] or "none", r["bar"], r["band"], ai["evals"], ai["cost"], ai["restraint"], r["eligible"], r["excluded"]]
        lines.append("| " + " | ".join(str(c) for c in cols) + " |")
    lines += ["", "The overall score summarises; it does not decide. Read the competency rows and the evidence first.", ""]
    for r in v["candidates"]:
        lines += [f"## {r['candidate']}: {r['band']}", "", r["why"], "", "| Competency | Weight | Mean | Interviewers | Spread |", "|---|---|---|---|---|"]
        for c in r["competencies"]:
            lines.append(f"| {c['id']} {cell(c['name'])} | {c['weight']} | {c['mean'] or 'none'} | {c['raters']} | {c['spread'] or 'none'} |")
        lines.append("")
        if r["flags"]:
            lines += ["To discuss:", ""] + [f"- {f['message']}" for f in r["flags"]] + [""]
    if v["pool_flags"]:
        lines += ["## Interviewer calibration", ""] + [f"- {f['message']}" for f in v["pool_flags"]] + [""]
    lines += ["## Fairness guardrails", ""] + [f"- **{k}.** {t}" for k, t in v["guardrails"]] + [""]
    if v["warnings"]:
        lines += ["## Warnings", ""] + [f"- {cell(w)}" for w in v["warnings"]] + [""]
    lines += ["## Calibration steps", ""] + [f"{n}. {s}" for n, s in enumerate(v["steps"], 1)] + [""]
    lines += [v["foot"], ""]
    return "\n".join(lines)


def ledger_csv(rows: list[dict[str, str]]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LEDGER_FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        flat = {**r, "window_from": r["window"]["from"], "window_to": r["window"]["to"]}
        w.writerow({k: flat[k] for k in LEDGER_FIELDS})
    return buf.getvalue()


def _num(text: str) -> Decimal | None:
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _allowed_numbers(loop: dict[str, Any], ledger: list[dict[str, str]]) -> set[Decimal]:
    """Every value a note may print. Compared as numbers, so 4.00 may be written 4.0 or 4."""
    texts = {"1", "2", "3", "4"}  # the score scale
    texts |= {r["value"] for r in ledger}
    cal = loop["calibration"]
    texts |= {str(cal["bar"]), str(cal["panel_min"]), str(cal["spread_flag"])}
    texts |= {str(c["weight"]) for c in loop["competencies"]}
    texts |= {str(c["floor"]) for c in loop["competencies"] if "floor" in c}
    texts |= {str(s["minutes"]) for s in loop["stages"]}
    texts |= {fmt(NEAR_BAR), fmt(DRIFT_FLAG)}  # the method's own thresholds
    # The role description, the loop version, the decision date and each figure's window and as_of are design
    # and record facts, not scores; a note may repeat them.
    facts = [loop["role"].get(k, "") for k in ("title", "level", "team")] + [str(loop.get("version", "")), str((loop.get("decision") or {}).get("by", ""))]
    facts += [t for r in ledger for t in (r.get("as_of", ""), (r.get("window") or {}).get("from", ""), (r.get("window") or {}).get("to", ""))]
    texts |= {n for f in facts for n in NUMBER.findall(IDENT.sub(" ", f))}
    out = {_num(t) for t in texts}
    # A negative drift may be written without its sign ("0.33 below the panel").
    out |= {abs(v) for v in out if v is not None}
    out.discard(None)
    return out


def check_note(text: str, loop: dict[str, Any], results: list[dict[str, Any]], ledger: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return findings for a free-text debrief note. Any finding blocks it."""
    out: list[dict[str, str]] = []
    allowed = _allowed_numbers(loop, ledger)
    bands = {r["candidate"]: r["band"] for r in results}
    for n, sentence in enumerate(re.split(r"(?<=[.!?])\s+|\n+", text), 1):
        if not sentence.strip():
            continue
        low = sentence.lower()
        stripped = IDENT.sub(" ", sentence)
        for num in NUMBER.findall(stripped):
            if _num(num) not in allowed:
                out.append({"rule": "figure-not-computed", "where": f"sentence {n}", "message": f"{num} is not a computed figure; cite one from ledger.csv or remove it"})
        for phrase in OVERCLAIMS:
            if re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", low):
                out.append({"rule": "overclaim", "where": f"sentence {n}", "message": f"'{phrase}' claims more than a loop can show"})
        for term in banned_terms(sentence):
            out.append({"rule": "banned-criterion", "where": f"sentence {n}", "message": f"'{term}' is not a job criterion"})
        named = [c for c in bands if re.search(r"\b" + re.escape(c) + r"\b", sentence)]
        for band, pattern in BAND_PHRASES.items():
            if pattern.search(low):
                for c in named:
                    if bands[c] != band:
                        out.append({"rule": "band-mismatch", "where": f"sentence {n}", "message": f"says {c} is '{band}'; the computed band is '{bands[c]}'"})
    return out
