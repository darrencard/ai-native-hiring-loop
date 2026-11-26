"""Load and check the shape of a loop design and a candidate's score sheet.

A loop design (loop.json) holds the role scorecard, the stages, the rubrics, the
questions and the calibration rules. A score sheet (one per candidate) holds the
questions each stage actually used, the time the debrief started, and every score.

This module checks shape only: required keys, types, ranges and references.
Fairness and evidence rules live in guardrails.py. Standard library only.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCORE_MIN = 1
SCORE_MAX = 4
ANCHOR_KEYS = ("1", "2", "3", "4")
STAGE_KINDS = ("work_sample", "structured_interview")
# The three kinds of judgment in AI use the loop must test. Every loop needs all three.
AI_JUDGMENT_KINDS = ("evals", "cost", "restraint")


class SchemaError(ValueError):
    """Raised when a file cannot be read as a loop design or a score sheet."""


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"{p}: cannot read JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise SchemaError(f"{p}: top level must be an object")
    return data


def parse_time(value: Any) -> datetime | None:
    """Parse an ISO 8601 timestamp with a UTC offset. Return None if it is not one."""
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def _req(obj: dict[str, Any], key: str, kind: type | tuple[type, ...], where: str, problems: list[str]) -> Any:
    if key not in obj:
        problems.append(f"{where}: missing '{key}'")
        return None
    value = obj[key]
    if not isinstance(value, kind) or (isinstance(value, bool) and kind is not bool):
        problems.append(f"{where}.{key}: wrong type")
        return None
    return value


def _check_anchors(anchors: Any, where: str, problems: list[str]) -> None:
    if not isinstance(anchors, dict):
        problems.append(f"{where}.anchors: must be an object with keys 1 to 4")
        return
    for k in ANCHOR_KEYS:
        text = anchors.get(k)
        if not isinstance(text, str) or not text.strip():
            problems.append(f"{where}.anchors.{k}: missing or empty")
    extra = sorted(set(anchors) - set(ANCHOR_KEYS))
    if extra:
        problems.append(f"{where}.anchors: unexpected keys {extra}")


def check_loop_shape(loop: dict[str, Any]) -> list[str]:
    """Return shape problems in a loop design. An empty list means the shape is sound."""
    problems: list[str] = []
    role = _req(loop, "role", dict, "loop", problems)
    if role is not None:
        for key in ("title", "level", "team"):
            _req(role, key, str, "role", problems)

    outcomes = _req(loop, "outcomes", list, "loop", problems) or []
    for i, o in enumerate(outcomes):
        where = f"outcomes[{i}]"
        if not isinstance(o, dict):
            problems.append(f"{where}: must be an object")
            continue
        for key in ("id", "text", "measure"):
            _req(o, key, str, where, problems)
        _req(o, "by_month", int, where, problems)

    comps = _req(loop, "competencies", list, "loop", problems) or []
    comp_ids: set[str] = set()
    for i, c in enumerate(comps):
        where = f"competencies[{i}]"
        if not isinstance(c, dict):
            problems.append(f"{where}: must be an object")
            continue
        cid = _req(c, "id", str, where, problems)
        if cid in comp_ids:
            problems.append(f"{where}: duplicate id {cid}")
        if cid:
            comp_ids.add(cid)
        _req(c, "name", str, where, problems)
        weight = _req(c, "weight", int, where, problems)
        if weight is not None and weight <= 0:
            problems.append(f"{where}.weight: must be a positive whole number")
        floor = c.get("floor")
        if floor is not None and (not isinstance(floor, (int, float)) or isinstance(floor, bool) or not SCORE_MIN <= floor <= SCORE_MAX):
            problems.append(f"{where}.floor: must be a number from {SCORE_MIN} to {SCORE_MAX}")
        kind = c.get("ai_judgment")
        if kind is not None and kind not in AI_JUDGMENT_KINDS:
            problems.append(f"{where}.ai_judgment: must be one of {list(AI_JUDGMENT_KINDS)} or absent")
        _check_anchors(c.get("anchors"), where, problems)
        outs = c.get("outcomes", [])
        if not isinstance(outs, list):
            problems.append(f"{where}.outcomes: must be a list of outcome ids")

    stages = _req(loop, "stages", list, "loop", problems) or []
    item_ids: set[str] = set()
    stage_ids: set[str] = set()
    for i, s in enumerate(stages):
        where = f"stages[{i}]"
        if not isinstance(s, dict):
            problems.append(f"{where}: must be an object")
            continue
        sid = _req(s, "id", str, where, problems)
        if sid in stage_ids:
            problems.append(f"{where}: duplicate id {sid}")
        if sid:
            stage_ids.add(sid)
        _req(s, "name", str, where, problems)
        _req(s, "minutes", int, where, problems)
        kind = _req(s, "kind", str, where, problems)
        if kind is not None and kind not in STAGE_KINDS:
            problems.append(f"{where}.kind: must be one of {list(STAGE_KINDS)}")
        if kind == "work_sample":
            _req(s, "task", str, where, problems)
            items = _req(s, "criteria", list, where, problems) or []
            label = "criteria"
        else:
            items = _req(s, "questions", list, where, problems) or []
            label = "questions"
        for j, it in enumerate(items):
            iw = f"{where}.{label}[{j}]"
            if not isinstance(it, dict):
                problems.append(f"{iw}: must be an object")
                continue
            iid = _req(it, "id", str, iw, problems)
            if iid in item_ids:
                problems.append(f"{iw}: duplicate id {iid} (ids must be unique across the loop)")
            if iid:
                item_ids.add(iid)
            _req(it, "text", str, iw, problems)
            cid = _req(it, "competency", str, iw, problems)
            if cid is not None and cid not in comp_ids:
                problems.append(f"{iw}.competency: unknown competency {cid}")
            if kind == "work_sample":
                _check_anchors(it.get("anchors"), iw, problems)
                ai = it.get("ai_judgment")
                if ai is not None and ai not in AI_JUDGMENT_KINDS:
                    problems.append(f"{iw}.ai_judgment: must be one of {list(AI_JUDGMENT_KINDS)} or absent")

    cal = _req(loop, "calibration", dict, "loop", problems)
    if cal is not None:
        bar = _req(cal, "bar", (int, float), "calibration", problems)
        if bar is not None and not SCORE_MIN <= bar <= SCORE_MAX:
            problems.append(f"calibration.bar: must be from {SCORE_MIN} to {SCORE_MAX}")
        pm = _req(cal, "panel_min", int, "calibration", problems)
        if pm is not None and pm < 2:
            problems.append("calibration.panel_min: must be at least 2")
        sf = _req(cal, "spread_flag", int, "calibration", problems)
        if sf is not None and not 1 <= sf <= SCORE_MAX - SCORE_MIN:
            problems.append(f"calibration.spread_flag: must be from 1 to {SCORE_MAX - SCORE_MIN}")
        steps = _req(cal, "steps", list, "calibration", problems)
        if steps is not None and not steps:
            problems.append("calibration.steps: must list at least one step")
    return problems


def check_scores_shape(sheet: dict[str, Any]) -> list[str]:
    """Return shape problems in one candidate's score sheet."""
    problems: list[str] = []
    _req(sheet, "candidate", str, "sheet", problems)
    started = _req(sheet, "debrief_started_at", str, "sheet", problems)
    if started is not None and parse_time(started) is None:
        problems.append("sheet.debrief_started_at: must be ISO 8601 with a UTC offset")
    asked = _req(sheet, "asked", dict, "sheet", problems)
    if asked is not None:
        for sid, ids in asked.items():
            if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
                problems.append(f"sheet.asked.{sid}: must be a list of item ids")
    scores = _req(sheet, "scores", list, "sheet", problems) or []
    for i, r in enumerate(scores):
        where = f"scores[{i}]"
        if not isinstance(r, dict):
            problems.append(f"{where}: must be an object")
            continue
        for key in ("interviewer", "stage", "item"):
            _req(r, key, str, where, problems)
        score = _req(r, "score", int, where, problems)
        if score is not None and not SCORE_MIN <= score <= SCORE_MAX:
            problems.append(f"{where}.score: must be a whole number from {SCORE_MIN} to {SCORE_MAX}")
        if parse_time(r.get("submitted_at")) is None:
            problems.append(f"{where}.submitted_at: missing or not ISO 8601 with a UTC offset")
        if not isinstance(r.get("evidence"), str):
            problems.append(f"{where}.evidence: missing")
    return problems


def item_index(loop: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Map each criterion or question id to {stage, competency, kind, ai_judgment}."""
    index: dict[str, dict[str, Any]] = {}
    for s in loop.get("stages", []):
        items = s.get("criteria") if s.get("kind") == "work_sample" else s.get("questions")
        for it in items or []:
            index[it["id"]] = {
                "stage": s["id"],
                "competency": it["competency"],
                "kind": s["kind"],
                "ai_judgment": it.get("ai_judgment"),
            }
    return index


def stage_items(loop: dict[str, Any]) -> dict[str, list[str]]:
    """Map each stage id to the ordered list of item ids every candidate must get."""
    out: dict[str, list[str]] = {}
    for s in loop.get("stages", []):
        items = s.get("criteria") if s.get("kind") == "work_sample" else s.get("questions")
        out[s["id"]] = [it["id"] for it in items or []]
    return out
