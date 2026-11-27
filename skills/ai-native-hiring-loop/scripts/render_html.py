"""The calibration packet as one self-contained HTML page, on the Leader Report's template and the Landing Loop's one
visual family.

The page takes the report's whole stylesheet from its template (assets/vendor/template.html, vendored byte-identical
at a pinned commit, see VENDORED.json) and draws its picture with svgkit (scripts/vendor/svgkit.py, vendored
byte-identical from landing-loop). Only a few rules for this page's layout are added.

It reads top down for someone who has never run a hiring loop: the shared header, the answer as the heading, each
candidate's verdict, the picture (each candidate against the target, each skill area against its floor, the person who
decides in brass), then one thing to do next, owned by the hiring manager. Each candidate's reason and what to discuss
first follow in two columns. The skill area tables, the debrief steps, the evidence ledger and everything technical
sit in folds. Public copy uses plain words: target, skill area, scoring guide. results.json keeps its words.

A hiring packet has no project status, so the page uses no status colour. The verdict prints as a plain mono chip.
Brass is only the hiring manager's call. It prints only what packet.view() holds, so it says what the Markdown twin
says. Nothing is loaded from the network, nothing depends on the clock or the machine, and every piece of text from a
file is escaped.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import svgkit as sk  # noqa: E402  (vendored, unchanged; see VENDORED.json)
from packet import view  # noqa: E402

VERSION = "0.3.1"
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "template.html"
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
SCALE = (1, 4)  # the score scale; every line in the picture runs across it

# Layout for this page only. Everything else comes from the template's stylesheet and svgkit.CSS.
PAGE_CSS = """
main.solo{margin-left:0}
.solo .slide{min-height:0}
.solo .slide.cover{min-height:0;padding-top:40px;padding-bottom:48px;justify-content:flex-start}
.solo h1{font-size:clamp(34px,4.6vw,60px);line-height:1;letter-spacing:-.04em;max-width:20ch;margin-bottom:20px}
.solo .lede{margin-bottom:24px}
.status{display:inline-block;font:400 10px/16px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t1)}
.status{border:1px solid var(--line3);border-radius:3px;padding:1px 6px;white-space:nowrap}
.verdict{margin:0 0 20px;display:flex;flex-wrap:wrap;gap:8px}
.panel{border:1px solid var(--line);border-radius:12px;background:var(--s1);padding:24px 28px 20px}
@media (min-width:1100px){.panel .sk{display:grid;grid-template-columns:720px minmax(0,1fr);gap:16px 40px;align-items:start}
.panel .sk figcaption{margin-top:0;flex-direction:column;align-items:flex-start}}
.next{margin-top:28px;display:grid;grid-template-columns:200px minmax(0,1fr);gap:8px 32px;align-items:baseline}
.next{border:1px solid var(--brass);border-radius:12px;padding:20px 24px;background:var(--brass-bg)}
.next>b{font:400 10px/22px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--brass)}
.next p{margin:0;font-size:16px;line-height:1.5;color:var(--t1)}
.next .who{display:flex;flex-wrap:wrap;gap:4px 24px;margin-top:10px;font:400 11.5px/16px var(--mono);color:var(--brass)}
.next .who span::before{font-size:10px;letter-spacing:.1em;color:var(--t3);margin-right:8px}
.next .who .o::before{content:"DECIDES"}.next .who .d::before{content:"BY"}
.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px 56px;align-items:start}
.cols h3{margin-bottom:8px}
.cands,.disc,.fair{margin:0;padding:0;list-style:none}
.cands li,.disc li,.fair li{border-top:1px solid var(--line);padding:12px 0;font-size:13.5px;line-height:1.5;color:var(--t2)}
.cands li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 16px;align-items:baseline}
.cands li b{font-weight:500;color:var(--t1);font-size:14.5px}
.cands li p{grid-column:1/-1;margin:0}
.disc li span,.fair li span{display:block;font:400 10px/18px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}
.solo details{margin-top:4px}
.solo details>*:not(summary){margin-top:12px}
.solo details p,.solo details li{margin:0 0 10px;font-size:13px;color:var(--t2);max-width:80ch}
.solo details ul,.solo details ol{padding-left:18px}
.solo details h3{margin:22px 0 6px}
.tablewrap td,.tablewrap th{overflow-wrap:anywhere}
.tablewrap .ex{font-size:12px;color:var(--t3)}
::selection{background:var(--t1);color:var(--bg)}
:focus-visible{outline:2px solid var(--t1);outline-offset:3px;border-radius:3px}
.foot{max-width:1120px;margin:0 auto;padding:28px 40px 64px;color:var(--t3);font-size:12px}
@media (max-width:980px){.foot{padding:24px 16px 48px}.solo .slide.cover{padding-top:24px}.cols,.next{grid-template-columns:1fr}.panel{padding:18px 16px 16px}
.stack table,.stack tbody,.stack tr,.stack td{display:block}.stack tr:first-child{display:none}.stack tr{padding:10px 16px;border-bottom:1px solid var(--line)}
.stack td{border:0;padding:3px 0;display:grid;grid-template-columns:118px 1fr;gap:12px}.stack td.num{text-align:left;white-space:normal}
.stack td::before{content:attr(data-l);font:400 10px/20px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}}
"""


def e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def stylesheet() -> str:
    """The report template's whole stylesheet, fonts included."""
    try:
        found = STYLE.search(TEMPLATE.read_text(encoding="utf-8"))
    except OSError:
        found = None
    return found.group(1) if found else ""


def fold(title: str, body: str) -> str:
    return f"<details><summary>{e(title)}</summary>{body}</details>"


class Table:
    """A table whose cells carry their column name, so a phone shows each row as labelled lines."""

    def __init__(self, heads: tuple[str, ...]) -> None:
        self.heads = heads
        self.rows: list[str] = []

    def row(self, *cells: tuple[str, str]) -> None:
        tds = []
        for head, (cls, body) in zip(self.heads, cells, strict=True):
            attr = f' class="{cls}"' if cls else ""
            tds.append(f'<td{attr} data-l="{e(head)}">{body}</td>')
        self.rows.append("<tr>" + "".join(tds) + "</tr>")

    def html(self) -> str:
        head = "<tr>" + "".join(f"<th>{e(h)}</th>" for h in self.heads) + "</tr>"
        return f'<div class="tablewrap stack"><table>{head}{"".join(self.rows)}</table></div>'


# The signature picture: each candidate against the target, each skill area against its floor


def short_area(r: dict[str, Any], cid: str) -> str:
    return next(c["short"] for c in r["competencies"] if c["id"] == cid)


def under_floor(r: dict[str, Any]) -> list[str]:
    return [short_area(r, f["where"]) for f in r["flags"] if f["rule"] == "floor"]


def scale_row(x: float, y: float, w: float, *, score: str | None, mark: str | None, target: bool, hid: str, size: float) -> str:
    """One line on the 1 to 4 scale: the track, the target or floor mark, the score as a dot with its value at the
    right, and the gap hatched when the score falls short of the mark."""
    lo, hi = SCALE
    at = sk.scale((lo, hi), (x, x + w - 52))
    parts = [sk.rule(x, y, x + w - 52, y, tone=sk.LINE2)]
    if mark is not None:
        mx = at(float(mark))
        if score is not None and float(score) < float(mark):
            parts.append(sk.hatched(at(float(score)), y - 4, mx - at(float(score)), 8, pattern_id=hid, rx=1))
        if target:
            parts.append(sk.target_tick(mx, y - 9, y + 9))
        else:
            parts.append(sk.rule(mx, y - 7, mx, y + 7, tone=sk.INK2, width=sk.STROKE))
    if score is None:
        parts.append(sk.label(x + w, y + 4, "none", anchor="end"))
    else:
        parts.append(sk.point(at(float(score)), y, r=5 if target else 4))
        parts.append(sk.value(x + w, y + 5, score, anchor="end", size=size))
    return "".join(parts)


def candidate_block(x: float, y: float, w: float, r: dict[str, Any], hid: str) -> tuple[str, float]:
    """One candidate: the code and verdict, the overall score against the target, then each skill area against its
    floor. Returns the drawing and its height."""
    parts = [sk.value(x, y + 16, r["candidate"], size=18), sk.label(x + w, y + 15, r["verdict"], anchor="end", tone=sk.INK)]
    parts.append(sk.label(x, y + 44, "Overall"))
    lo, hi = SCALE
    at = sk.scale((lo, hi), (x, x + w - 52))
    parts.append(sk.label(at(float(r["bar"])), y + 44, f"Target {r['bar']}", anchor="middle", tone=sk.INK2))
    parts.append(scale_row(x, y + 62, w, score=r["overall"], mark=r["bar"], target=True, hid=hid, size=16))
    yy = y + 96
    parts.append(sk.rule(x, yy - 14, x + w, yy - 14, tone=sk.LINE))
    for c in r["competencies"]:
        parts.append(sk.value(x, yy, c["short"], size=12.5, tone=sk.INK2))
        if c["floor"] is not None:
            parts.append(sk.label(x + w - 52, yy, f"Floor {c['floor']}", anchor="end"))
        parts.append(scale_row(x, yy + 14, w, score=c["mean"], mark=c["floor"], target=False, hid=hid, size=12.5))
        yy += 40
    return "".join(parts), yy - y - 14


def decider(x: float, y: float, owner: str, by: str, stacked: bool) -> str:
    """The person who decides, in brass: a person's call, not the agent's."""
    when = f"by {by}" if by else "no date set"
    parts = [sk.person(x + 7, y + 4, size=14)]
    if stacked:
        parts += [sk.label(x + 22, y - 4, owner, tone=sk.BRASS), sk.label(x + 22, y + 12, f"Decides {when}", tone=sk.BRASS)]
    else:
        parts.append(sk.label(x + 22, y + 3, f"{owner} decides {when}", tone=sk.BRASS))
    return "".join(parts)


def candidates_chart(v: dict[str, Any], variant: str) -> str:
    """Wide: the candidates side by side, three to a row. Tall: one under another."""
    wide = variant == "wide"
    hid = f"sk-hl-hatch-{variant}"
    parts = [sk.defs(sk.hatch_pattern(hid))]
    cands = v["candidates"]
    if wide:
        per, gap = 3, 30.0
        w = (sk.WIDE - gap * (per - 1)) / per
        y, row_h = 0.0, 0.0
        for i, r in enumerate(cands):
            if i and i % per == 0:
                y += row_h + 28
            body, h = candidate_block((i % per) * (w + gap), y, w, r, hid)
            parts.append(body)
            row_h = max(row_h, h)
            if i % per:
                parts.append(sk.rule((i % per) * (w + gap) - gap / 2, y, (i % per) * (w + gap) - gap / 2, y + h, tone=sk.LINE))
        y += row_h + 24
        width = sk.WIDE
    else:
        width, y = sk.TALL, 0.0
        for i, r in enumerate(cands):
            if i:
                parts.append(sk.rule(0, y - 14, width, y - 14, tone=sk.LINE2))
            body, h = candidate_block(0, y, width, r, hid)
            parts.append(body)
            y += h + 30
    parts.append(sk.rule(0, y, width, y, tone=sk.LINE))
    parts.append(decider(0, y + 24, v["owner"], v["by"], stacked=not wide))
    height = y + (40 if wide else 48)
    return sk.frame("".join(parts), label=aria(v), height=height, width=width, variant=variant)


def aria(v: dict[str, Any]) -> str:
    """The answer the picture gives, in one sentence."""
    says = []
    for r in v["candidates"]:
        if r["overall"] is None:
            says.append(f"{r['candidate']} has not enough evidence for an overall score")
            continue
        floors = under_floor(r)
        under = f", under its floor on {' and '.join(floors)}" if floors else ""
        says.append(f"{r['candidate']} scores {r['overall']} overall, {r['verdict']}{under}")
    when = f" by {v['by']}" if v["by"] else ""
    return f"{v['answer'][:-1]}; " + "; ".join(says) + f". {v['owner']} decides{when}."


# The page


def candidates_list(v: dict[str, Any]) -> str:
    items = "".join(f'<li><b>{e(r["candidate"])}</b><span class="status">{e(r["verdict"])}</span><p>{e(r["why"])}</p></li>' for r in v["candidates"])
    return f'<ul class="cands">{items}</ul>'


def to_discuss(v: dict[str, Any]) -> str:
    items = [f"<li><span>{e(r['candidate'])}</span>{e(f['message'][:1].upper() + f['message'][1:])}.</li>" for r in v["candidates"] for f in r["flags"]]
    items += [f"<li><span>Interviewer {e(f['where'])}</span>{e(f['message'])}.</li>" for f in v["pool_flags"]]
    return f'<ul class="disc">{"".join(items)}</ul>' if items else "<p>Nothing is flagged.</p>"


def fairness(v: dict[str, Any]) -> str:
    rows = "".join(f"<li><span>{e(k)}</span>{e(t)}</li>" for k, t in v["guardrails"])
    rows += "".join(f"<li><span>Warning</span>{e(w)}</li>" for w in v["warnings"])
    return f'<ul class="fair">{rows}</ul>'


def candidate_tables(v: dict[str, Any]) -> str:
    out = []
    for r in v["candidates"]:
        tab = Table(("Skill area", "Weight", "Mean", "Floor", "Interviewers", "Spread"))
        for c in r["competencies"]:
            tab.row(
                ("", f"{e(c['id'])} {e(c['name'])}"),
                ("num", e(c["weight"])),
                ("num", e(c["mean"] or "none")),
                ("num", e(c["floor"] or "none")),
                ("num", e(c["raters"])),
                ("num", e(c["spread"] or "none")),
            )
        counted = f"{r['eligible']} scores counted, {r['excluded']} not counted."
        out.append(f'<h3 id="{e(r["candidate"])}">{e(r["candidate"])}: {e(r["verdict"])}</h3><p>{e(r["why"])} {e(counted)}</p>{tab.html()}')
    ai = v["ai_areas"]
    tab = Table(("Candidate", *(f"{ai.get(k, k)}, work sample" for k in ("evals", "cost", "restraint"))))
    for r in v["candidates"]:
        tab.row(("", e(r["candidate"])), *(("num", e(r["ai_judgment"][k] or "none")) for k in ("evals", "cost", "restraint")))
    out.append(f"<h3>Judgment in AI use, from the work sample alone</h3>{tab.html()}")
    return "".join(out)


def ledger_table(ledger: list[dict[str, Any]]) -> str:
    tab = Table(("ID", "Figure", "Value", "Unit", "Window", "Source"))
    for r in ledger:
        w = f"{r['window']['from'][:16]} to {r['window']['to'][:16]}"
        tab.row(("", e(r["id"])), ("", e(r["figure"])), ("num", e(r["display"])), ("ex", e(r["unit"])), ("ex", e(w)), ("ex", e(r["source"])))
    return f"<p>{len(ledger)} rows. Code computed each one from the score sheets named.</p>{tab.html()}"


def engineers(v: dict[str, Any]) -> str:
    bands = ", ".join(f"{r['candidate']} <code>{e(r['band'])}</code>" for r in v["candidates"])
    return (
        f"<p>Verdicts as results.json stores them: {bands}. The page prints bar as target, competency as skill area and rubric as scoring guide.</p>"
        "<p>Run: <code>python3 scripts/run.py score LOOP.json SHEET.json [SHEET.json ...] --out DIR</code> writes results.json, ledger.csv, "
        "packet.md and packet.html. Any guardrail error stops it before anything is written (exit code 1); a file that cannot be read exits 2. "
        "<code>run.py check-note DIR/results.json NOTE.md</code> blocks a decision note with an uncomputed figure, a wrong verdict, an overclaim "
        "or a banned criterion.</p>"
        f"<p>Loop version {e(v['version'])}. Project file key: none. A hiring loop is about the team, not a project, so it writes nothing "
        "into a Landing Loop project file.</p>"
    )


def page(
    loop: dict[str, Any],
    results: list[dict[str, Any]],
    findings: list[dict[str, str]],
    pool_flags: list[dict[str, str]],
    ledger: list[dict[str, Any]],
    guards: list[dict[str, Any]],
) -> str:
    v = view(loop, results, findings, pool_flags, guards)
    ill = v["illustrative"]
    header = sk.page_header("ai-native-hiring-loop", date=v["as_of"][:10], version=f"v{VERSION}", illustrative=ill)
    pic = sk.figure(
        candidates_chart(v, "wide"),
        candidates_chart(v, "tall"),
        caption=f"Each line runs from 1 to 4, the scoring guide's scale; the dot is the score. The dashed mark is the target of {v['bar']} for the "
        "overall score. The short upright marks are the floors: a skill area under its floor puts the candidate below the target, whatever the "
        "overall score. Hatched: how far a score falls short. The person in brass decides.",
        illustrative=ill,
    )
    chips = "".join(f'<span class="status">{e(r["candidate"])}: {e(r["verdict"])}</span>' for r in v["candidates"])
    who = f'<span class="o">{e(v["owner"])}</span>'
    by = f'<span class="d">{e(v["by"])}</span>' if v["by"] else ""
    step = f'<div class="next"><b>What to do next</b><div><p>{e(v["decision"])}</p><span class="who">{who}{by}</span></div></div>'
    lede = f"{v['level']} role: {v['title'].removeprefix('Hiring loop: ')}. {v['lede']}"
    cover = (
        f'<section class="slide cover">{header}<h1>{e(v["answer"])}</h1><p class="lede">{e(lede)}</p><p class="verdict">{chips}</p><div class="panel">{pic}</div>{step}</section>'
    )
    detail = (
        '<section class="slide"><div class="meta"><span>What the scores say</span></div><div class="cols">'
        f"<div><h3>Each candidate</h3>{candidates_list(v)}"
        '<p class="sub" style="margin-top:12px">The overall score summarises; it does not decide. Read the skill area rows and the evidence first.</p></div>'
        f'<div><h3>To discuss first</h3>{to_discuss(v)}<h3 style="margin-top:28px">Fairness checks</h3>{fairness(v)}</div>'
        "</div></section>"
    )
    steps = "".join(f"<li>{e(s)}</li>" for s in v["steps"])
    folds = [
        fold("Each candidate in full", candidate_tables(v)),
        fold("How the debrief runs", f"<p>{e(v['team'])}</p><ol>{steps}</ol>"),
        fold("Every figure, with its source", ledger_table(ledger)),
        fold("For your engineers", engineers(v)),
    ]
    more = f'<section class="slide"><div class="meta"><span>Detail</span></div>{"".join(folds)}</section>'
    return (
        '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(v["title"])}</title><style>{stylesheet()}{sk.CSS}{PAGE_CSS}</style></head><body><main class="solo">{cover}{detail}{more}'
        f'<p class="foot">{e(v["foot"])}</p></main></body></html>\n'
    )
