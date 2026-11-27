"""Combine eligible scores into figures, deterministically, with a ledger row per figure.

Method (fixed, documented in references/method.md):
- A competency's score is the mean of every eligible item score on it, across interviewers.
- The overall score is the weight-averaged mean of competency scores.
- Means are exact fractions, rounded half-up to 2 decimals only when printed.
- The band is "insufficient evidence" if any competency has no eligible score, "below bar"
  if the overall score is under the bar or any competency is under its floor, else "meets bar".
- A competency is flagged for calibration when interviewers' means on it differ by the
  loop's spread_flag or more.
- Across the pool, an interviewer is flagged when their mean differs from the panel mean of
  the same items by DRIFT_FLAG or more, with at least two candidates scored.

The model never does this arithmetic. Standard library only.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Any

from guardrails import eligible_scores
from schema import AI_JUDGMENT_KINDS, item_index, min_scorers, stage_items, utc

NEAR_BAR = Fraction(1, 4)
DRIFT_FLAG = Fraction(3, 4)

SCORE_UNIT = "score, 1 to 4"
POINTS_UNIT = "points on the 1 to 4 scale"


def figure(fid: str, candidate: str, label: str, value: str, unit: str, source: str, window: tuple[str, str], as_of: str, method: str) -> dict[str, Any]:
    """One ledger row: every figure carries value, unit, source, window (from, to) and as_of."""
    return {
        "id": fid,
        "candidate": candidate,
        "figure": label,
        "value": value,
        "unit": unit,
        "source": source,
        "window": {"from": window[0], "to": window[1]},
        "as_of": as_of,
        "method": method,
    }


def candidate_window(sheet: dict[str, Any]) -> tuple[str, str]:
    """From the first score recorded to the moment the debrief started. Only scores inside it count."""
    started = utc(sheet["debrief_started_at"]) or ""
    times = sorted(t for t in (utc(r.get("submitted_at")) for r in sheet.get("scores", [])) if t)
    return (times[0] if times else started, started)


def fmt(value: Fraction | None) -> str | None:
    """Round half-up to 2 decimals. The only place a figure becomes a printed number."""
    if value is None:
        return None
    d = Decimal(value.numerator) / Decimal(value.denominator)
    return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _mean(values: list[int]) -> Fraction | None:
    return Fraction(sum(values), len(values)) if values else None


def _refs(sheet_name: str, positions: list[int]) -> str:
    return "; ".join(f"{sheet_name}#scores[{p}]" for p in sorted(positions))


def score_candidate(loop: dict[str, Any], sheet: dict[str, Any], sheet_name: str) -> dict[str, Any]:
    """Return a candidate's figures, band, calibration flags and ledger rows."""
    cand = sheet["candidate"]
    index = item_index(loop)
    eligible = eligible_scores(loop, sheet)
    cal = loop["calibration"]
    bar = Fraction(str(cal["bar"]))
    spread_flag = cal["spread_flag"]
    ledger: list[dict[str, Any]] = []
    window = candidate_window(sheet)

    def row(fid: str, label: str, value: Fraction | int | None, positions: list[int], method: str, unit: str = SCORE_UNIT) -> None:
        printed = fmt(value) if isinstance(value, Fraction) or value is None else str(value)
        source = _refs(sheet_name, positions) if positions else f"{sheet_name}: no eligible score"
        ledger.append(figure(f"{cand}.{fid}", cand, label, printed if printed is not None else "none", unit, source, window, window[1], method))

    comps: list[dict[str, Any]] = []
    weighted = Fraction(0)
    weight_sum = 0
    missing = False
    floor_breach: list[tuple[str, str, Fraction, Fraction]] = []
    flags: list[dict[str, str]] = []
    for c in loop["competencies"]:
        rows = [(p, r) for p, r in eligible if index[r["item"]]["competency"] == c["id"]]
        mean = _mean([r["score"] for _, r in rows])
        positions = [p for p, _ in rows]
        by_rater: dict[str, list[int]] = {}
        for _, r in rows:
            by_rater.setdefault(r["interviewer"], []).append(r["score"])
        rater_means = {k: Fraction(sum(v), len(v)) for k, v in sorted(by_rater.items())}
        spread = max(rater_means.values()) - min(rater_means.values()) if rater_means else None
        row(f"{c['id']}.mean", f"{c['name']}: mean score (1 to 4)", mean, positions, "mean of eligible item scores")
        row(f"{c['id']}.raters", f"{c['name']}: interviewers scoring", len(rater_means), positions, "count of distinct interviewers", "interviewers")
        if spread is not None:
            row(f"{c['id']}.spread", f"{c['name']}: spread between interviewers", spread, positions, "max minus min of interviewer means", POINTS_UNIT)
        if mean is None:
            missing = True
        else:
            weighted += mean * c["weight"]
            weight_sum += c["weight"]
            floor = c.get("floor")
            if floor is not None and mean < Fraction(str(floor)):
                floor_breach.append((c["id"], c["name"], mean, Fraction(str(floor))))
        if spread is not None and spread >= spread_flag:
            flags.append(
                {
                    "rule": "spread",
                    "where": c["id"],
                    "message": f"interviewers differ by {fmt(spread)} on {c['name']}; read the evidence aloud against the anchors, lowest score first",
                }
            )
        comps.append(
            {
                "id": c["id"],
                "name": c["name"],
                "weight": c["weight"],
                "mean": fmt(mean),
                "raters": len(rater_means),
                "spread": fmt(spread),
                "rater_means": {k: fmt(v) for k, v in rater_means.items()},
            }
        )

    overall = None if missing or weight_sum == 0 else weighted / weight_sum
    all_positions = [p for p, _ in eligible]
    row("overall", "Overall weighted score (1 to 4)", overall, all_positions, "weight-averaged mean of competency scores")

    ai: dict[str, str | None] = {}
    for kind in AI_JUDGMENT_KINDS:
        rows = [(p, r) for p, r in eligible if index[r["item"]]["ai_judgment"] == kind]
        m = _mean([r["score"] for _, r in rows])
        ai[kind] = fmt(m)
        row(f"ai.{kind}", f"AI judgment, {kind}: mean score (1 to 4)", m, [p for p, _ in rows], "mean of eligible work-sample criterion scores")

    if overall is None:
        band = "insufficient evidence"
    elif overall < bar or floor_breach:
        band = "below bar"
    else:
        band = "meets bar"
    if overall is not None and abs(overall - bar) < NEAR_BAR:
        flags.append({"rule": "near-bar", "where": "overall", "message": f"overall {fmt(overall)} is within {fmt(NEAR_BAR)} of the bar {fmt(bar)}; discuss before deciding"})
    for cid, name, mean, floor in floor_breach:
        flags.append({"rule": "floor", "where": cid, "message": f"{name} is {fmt(mean)}, under its floor of {fmt(floor)}; the band is below bar whatever the overall score"})

    counted = {p for p, _ in eligible}
    excluded_positions = [p for p in range(len(sheet.get("scores", []))) if p not in counted]
    excluded = len(excluded_positions)
    row("eligible", "Scores counted", len(eligible), all_positions, "count of eligible scores", "scores")
    row("excluded", "Scores not counted", excluded, excluded_positions, "scores recorded after the debrief, unasked, duplicated or without evidence", "scores")

    return {
        "candidate": cand,
        "overall": fmt(overall),
        "bar": fmt(bar),
        "band": band,
        "competencies": comps,
        "ai_judgment": ai,
        "eligible": len(eligible),
        "excluded": excluded,
        "timestamps_from": sheet.get("timestamps_from"),
        "flags": flags,
        "ledger": ledger,
    }


def interviewer_drift(loop: dict[str, Any], sheets: list[tuple[dict[str, Any], str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Flag interviewers who score well above or below the panel on the same items.

    Compares each interviewer's mean with the panel mean on the items that interviewer
    scored, so an interviewer who only sees hard questions is not penalised.
    """
    per_item: dict[tuple[str, str], list[int]] = {}
    mine: dict[str, list[tuple[str, str, int]]] = {}
    refs: dict[str, list[str]] = {}
    candidates: dict[str, set[str]] = {}
    for sheet, name in sheets:
        cand = sheet["candidate"]
        for pos, r in eligible_scores(loop, sheet):
            per_item.setdefault((cand, r["item"]), []).append(r["score"])
            mine.setdefault(r["interviewer"], []).append((cand, r["item"], r["score"]))
            refs.setdefault(r["interviewer"], []).append(f"{name}#scores[{pos}]")
            candidates.setdefault(r["interviewer"], set()).add(cand)
    flags: list[dict[str, str]] = []
    ledger: list[dict[str, Any]] = []
    window = pool_window(sheets)
    for who in sorted(mine):
        if len(candidates[who]) < 2:
            continue
        own = Fraction(sum(s for _, _, s in mine[who]), len(mine[who]))
        panel_vals = [v for cand, item, _ in mine[who] for v in per_item[(cand, item)]]
        panel = Fraction(sum(panel_vals), len(panel_vals))
        drift = own - panel
        ledger.append(
            figure(
                f"pool.{who}.drift",
                "pool",
                f"{who}: mean minus panel mean on the same items",
                fmt(drift) or "none",
                POINTS_UNIT,
                "; ".join(sorted(refs[who])),
                window,
                window[1],
                "interviewer mean minus mean of all eligible scores on the same candidate and item",
            )
        )
        if abs(drift) >= DRIFT_FLAG:
            direction = "above" if drift > 0 else "below"
            flags.append({"rule": "drift", "where": who, "message": f"{who} scores {fmt(abs(drift))} {direction} the panel on the same items; review their anchors"})
    return flags, ledger


def pool_window(sheets: list[tuple[dict[str, Any], str]]) -> tuple[str, str]:
    """From the first score in the pool to the last debrief start."""
    windows = [candidate_window(s) for s, _ in sheets]
    return (min(w[0] for w in windows), max(w[1] for w in windows)) if windows else ("", "")


def guardrail_figures(loop: dict[str, Any], sheets: list[tuple[dict[str, Any], str]]) -> list[dict[str, Any]]:
    """The fairness figures the packet prints, computed from the sheets that passed every guardrail.

    The packet only exists if every guardrail passed, so these restate what was checked as counts a reader can trace.
    """
    window = pool_window(sheets)
    names = "; ".join(name for _, name in sheets)
    required = stage_items(loop)
    items = sum(len(v) for v in required.values())
    same = sum(1 for s, _ in sheets if {k: list(v) for k, v in (s.get("asked") or {}).items()} == required)
    late = 0
    counted = 0
    for s, _ in sheets:
        start = utc(s["debrief_started_at"])
        late += sum(1 for r in s.get("scores", []) if (utc(r.get("submitted_at")) or "") >= (start or ""))
        counted += len(eligible_scores(loop, s))
    need = min_scorers(loop)
    ws = [st["id"] for st in loop["stages"] if st["kind"] == "work_sample"]
    least = None
    for s, _ in sheets:
        for sid in ws:
            for item in required[sid]:
                n = len({r["interviewer"] for _, r in eligible_scores(loop, s) if r["item"] == item})
                least = n if least is None else min(least, n)
    rows = [
        ("candidates", "Candidates in the pool", len(sheets), "candidates", "count of score sheets"),
        ("items", "Items every candidate must get", items, "items", "count of criteria and questions in the loop"),
        ("same_questions", "Candidates asked exactly those items, in order", same, "candidates", "sheets whose asked list matches the loop"),
        ("counted", "Scores counted", counted, "scores", "eligible scores across the pool"),
        ("after_debrief", "Scores recorded at or after the debrief started", late, "scores", "submitted_at at or after debrief_started_at; any one blocks the packet"),
        (
            "work_sample_scorers",
            "Fewest independent scorers on any work-sample criterion",
            least if least is not None else 0,
            "interviewers",
            f"minimum distinct interviewers per criterion; the loop needs {max([need[s] for s in ws] or [0])}",
        ),
    ]
    return [figure(f"pool.{fid}", "pool", label, str(v), unit, names, window, window[1], method) for fid, label, v, unit, method in rows]
