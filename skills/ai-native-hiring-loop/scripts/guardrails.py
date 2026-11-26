"""Fairness and evidence rules for a hiring loop. Any error blocks the packet.

Design rules (check_design) run on loop.json before anyone is interviewed.
Sheet rules (check_sheet) run on each candidate's score sheet before scores are combined.
Pool rules (check_pool) run across every candidate in the same loop.

Each finding is a dict: {"rule", "level" ("error" or "warning"), "where", "message"}.
Standard library only. No text read from a file ever changes a rule or its result.
"""

from __future__ import annotations

import re
from typing import Any

from schema import AI_JUDGMENT_KINDS, item_index, parse_time, stage_items

WEIGHT_TOTAL = 100
MIN_EVIDENCE_CHARS = 20
MIN_STAGES_PER_COMPETENCY = 2

# Criteria that invite bias or measure something other than the job. They may not
# appear in a scorecard, a rubric, a task or a question.
BANNED_CRITERIA = (
    "culture fit",
    "gut feel",
    "gut feeling",
    "overqualified",
    "digital native",
    "young",
    "energetic",
    "native speaker",
    "pedigree",
    "top school",
    "beer test",
    "airport test",
    "rockstar",
    "ninja",
)


PLACEHOLDER = re.compile(r"<[^<>]+>")


def finding(rule: str, level: str, where: str, message: str) -> dict[str, str]:
    return {"rule": rule, "level": level, "where": where, "message": message}


def banned_terms(text: str) -> list[str]:
    low = text.lower()
    return [t for t in BANNED_CRITERIA if re.search(r"\b" + re.escape(t) + r"\b", low)]


def _texts(loop: dict[str, Any]) -> list[tuple[str, str]]:
    """Every piece of free text in a loop design, with where it sits."""
    out: list[tuple[str, str]] = []
    role = loop.get("role") or {}
    out.extend((f"role {k}", role.get(k, "")) for k in ("title", "level", "team"))
    out.append(("calibration", " ".join(str(x) for x in (loop.get("calibration") or {}).get("steps", []))))
    for c in loop.get("competencies", []):
        out.append((f"competency {c['id']}", c.get("name", "")))
        out.append((f"competency {c['id']}", c.get("description", "")))
        out.extend((f"competency {c['id']} anchor {k}", v) for k, v in (c.get("anchors") or {}).items())
    for o in loop.get("outcomes", []):
        out.append((f"outcome {o['id']}", o.get("text", "")))
    for s in loop.get("stages", []):
        out.append((f"stage {s['id']} task", s.get("task", "")))
        for it in (s.get("criteria") or []) + (s.get("questions") or []):
            out.append((f"item {it['id']}", it.get("text", "")))
            out.extend((f"item {it['id']} follow-up", f) for f in it.get("follow_ups", []))
            out.extend((f"item {it['id']} anchor {k}", v) for k, v in (it.get("anchors") or {}).items())
    return out


def check_design(loop: dict[str, Any]) -> list[dict[str, str]]:
    """Rules a loop design must pass before it is used on any candidate."""
    out: list[dict[str, str]] = []
    comps = loop.get("competencies", [])
    stages = loop.get("stages", [])

    total = sum(c.get("weight", 0) for c in comps)
    if total != WEIGHT_TOTAL:
        out.append(finding("weights-total", "error", "competencies", f"weights add to {total}; they must add to {WEIGHT_TOTAL}"))

    kinds = {s.get("kind") for s in stages}
    if "work_sample" not in kinds:
        out.append(finding("needs-work-sample", "error", "stages", "the loop has no work-sample stage; judgment in AI use must be shown, not described"))
    if "structured_interview" not in kinds:
        out.append(finding("needs-structured-interview", "error", "stages", "the loop has no structured interview stage"))

    index = item_index(loop)
    covered = {index[i]["ai_judgment"] for i in index if index[i]["kind"] == "work_sample" and index[i]["ai_judgment"]}
    for kind in AI_JUDGMENT_KINDS:
        if kind not in covered:
            out.append(finding("ai-judgment-coverage", "error", "stages", f"no work-sample criterion tests '{kind}'"))

    stages_per_comp: dict[str, set[str]] = {c["id"]: set() for c in comps}
    for info in index.values():
        stages_per_comp.setdefault(info["competency"], set()).add(info["stage"])
    for cid, sids in sorted(stages_per_comp.items()):
        if len(sids) < MIN_STAGES_PER_COMPETENCY:
            out.append(
                finding(
                    "competency-coverage",
                    "error",
                    f"competency {cid}",
                    f"assessed in {len(sids)} stage(s); each competency needs at least {MIN_STAGES_PER_COMPETENCY} so no single interviewer decides it",
                )
            )

    outcome_ids = {o["id"] for o in loop.get("outcomes", [])}
    linked: set[str] = set()
    for c in comps:
        for oid in c.get("outcomes", []):
            if oid not in outcome_ids:
                out.append(finding("outcome-link", "error", f"competency {c['id']}", f"links to unknown outcome {oid}"))
            linked.add(oid)
        if not c.get("outcomes"):
            out.append(finding("outcome-link", "error", f"competency {c['id']}", "links to no outcome; every competency must serve an outcome of the role"))
    for oid in sorted(outcome_ids - linked):
        out.append(finding("outcome-link", "warning", f"outcome {oid}", "no competency tests this outcome"))

    for where, text in _texts(loop):
        if PLACEHOLDER.search(text or ""):
            out.append(finding("unfilled-placeholder", "error", where, "still holds template text in angle brackets"))
        for term in banned_terms(text or ""):
            out.append(finding("banned-criterion", "error", where, f"'{term}' is not a job criterion; replace it with observable behaviour"))

    for s in stages:
        if s.get("kind") == "structured_interview" and not s.get("questions"):
            out.append(finding("needs-questions", "error", f"stage {s['id']}", "a structured interview needs written questions"))
        if s.get("kind") == "work_sample" and not s.get("criteria"):
            out.append(finding("needs-rubric", "error", f"stage {s['id']}", "a work sample needs rubric criteria"))
    return out


def eligible_scores(loop: dict[str, Any], sheet: dict[str, Any]) -> list[tuple[int, dict[str, Any]]]:
    """Scores that count: known item, right stage, asked, with evidence, recorded before the debrief started.

    Returns (position in sheet, score row) pairs so every figure can cite its rows.
    """
    index = item_index(loop)
    asked = {sid: set(ids) for sid, ids in (sheet.get("asked") or {}).items()}
    started = parse_time(sheet.get("debrief_started_at"))
    seen: set[tuple[str, str]] = set()
    out: list[tuple[int, dict[str, Any]]] = []
    for pos, r in enumerate(sheet.get("scores", [])):
        info = index.get(r.get("item"))
        submitted = parse_time(r.get("submitted_at"))
        key = (r.get("interviewer"), r.get("item"))
        if (
            info is None
            or info["stage"] != r.get("stage")
            or r.get("item") not in asked.get(r.get("stage"), set())
            or started is None
            or submitted is None
            or submitted >= started
            or len((r.get("evidence") or "").strip()) < MIN_EVIDENCE_CHARS
            or key in seen
        ):
            continue
        seen.add(key)
        out.append((pos, r))
    return out


def check_sheet(loop: dict[str, Any], sheet: dict[str, Any]) -> list[dict[str, str]]:
    """Rules one candidate's score sheet must pass before its scores are combined."""
    out: list[dict[str, str]] = []
    cand = sheet.get("candidate", "?")
    index = item_index(loop)
    required = stage_items(loop)
    asked = sheet.get("asked") or {}

    if sheet.get("loop_version") != loop.get("version"):
        out.append(
            finding(
                "loop-version",
                "error",
                cand,
                f"sheet is for loop version {sheet.get('loop_version')!r}, the loop is {loop.get('version')!r}; candidates in one pool get one loop",
            )
        )

    for sid, ids in required.items():
        got = asked.get(sid)
        if got is None:
            out.append(finding("same-questions", "error", f"{cand} stage {sid}", "no record of what this stage asked"))
            continue
        missing = [i for i in ids if i not in got]
        extra = [i for i in got if i not in ids]
        if missing:
            out.append(finding("same-questions", "error", f"{cand} stage {sid}", f"skipped {missing}; every candidate gets every question"))
        if extra:
            out.append(finding("same-questions", "error", f"{cand} stage {sid}", f"asked {extra}, which are not in the loop; every candidate gets the same questions"))
    for sid in sorted(set(asked) - set(required)):
        out.append(finding("same-questions", "error", f"{cand} stage {sid}", "stage is not in the loop"))

    started = parse_time(sheet.get("debrief_started_at"))
    seen: set[tuple[str, str]] = set()
    for pos, r in enumerate(sheet.get("scores", [])):
        where = f"{cand} scores[{pos}]"
        item = r.get("item")
        info = index.get(item)
        if info is None:
            out.append(finding("unknown-item", "error", where, f"item {item} is not in the loop"))
            continue
        if info["stage"] != r.get("stage"):
            out.append(finding("unknown-item", "error", where, f"item {item} belongs to stage {info['stage']}, not {r.get('stage')}"))
        if item not in asked.get(r.get("stage"), []):
            out.append(finding("item-not-asked", "error", where, f"item {item} was scored but not asked"))
        submitted = parse_time(r.get("submitted_at"))
        if started is not None and submitted is not None and submitted >= started:
            out.append(
                finding(
                    "scored-after-discussion",
                    "error",
                    where,
                    f"{r.get('interviewer')} recorded this score at {r.get('submitted_at')}, after the debrief started at {sheet.get('debrief_started_at')}; it does not count",
                )
            )
        if len((r.get("evidence") or "").strip()) < MIN_EVIDENCE_CHARS:
            out.append(finding("needs-evidence", "error", where, f"a score needs written evidence of at least {MIN_EVIDENCE_CHARS} characters"))
        key = (r.get("interviewer"), item)
        if key in seen:
            out.append(finding("duplicate-score", "error", where, f"{r.get('interviewer')} scored {item} twice"))
        seen.add(key)

    eligible = eligible_scores(loop, sheet)
    scored_items = {r["item"] for _, r in eligible}
    for sid, ids in required.items():
        for i in ids:
            if i in asked.get(sid, []) and i not in scored_items:
                out.append(finding("unscored-item", "error", f"{cand} item {i}", "asked but has no eligible score"))

    panel = {r["interviewer"] for _, r in eligible}
    panel_min = (loop.get("calibration") or {}).get("panel_min", 2)
    if len(panel) < panel_min:
        out.append(finding("panel-size", "error", cand, f"{len(panel)} interviewer(s) with eligible scores; the loop needs {panel_min}"))

    by_comp: dict[str, set[str]] = {}
    for _, r in eligible:
        by_comp.setdefault(index[r["item"]]["competency"], set()).add(r["interviewer"])
    for c in loop.get("competencies", []):
        n = len(by_comp.get(c["id"], set()))
        if 0 < n < 2:
            out.append(finding("single-rater", "warning", f"{cand} competency {c['id']}", "only one interviewer scored this competency"))
    return out


def check_pool(loop: dict[str, Any], sheets: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Rules across every candidate: one loop, unique candidates, the same question sets."""
    out: list[dict[str, str]] = []
    names = [s.get("candidate") for s in sheets]
    for name in sorted({n for n in names if names.count(n) > 1}):
        out.append(finding("duplicate-candidate", "error", str(name), "two score sheets for one candidate"))
    sets = {s.get("candidate"): {k: sorted(v) for k, v in (s.get("asked") or {}).items()} for s in sheets}
    if len({repr(sorted(v.items())) for v in sets.values()}) > 1:
        out.append(finding("same-questions", "error", "pool", "candidates in this pool were not asked the same questions"))
    return out


def errors(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    return [f for f in findings if f["level"] == "error"]
