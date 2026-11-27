"""The calibration packet as one self-contained HTML page, on the Leader Report's template and the Landing Loop's one
visual family.

The page takes the report's whole stylesheet from its template (assets/vendor/template.html, vendored byte-identical
at a pinned commit, see VENDORED.json) and draws its picture with svgkit (scripts/vendor/svgkit.py, vendored
byte-identical from landing-loop). Only a few rules for this page's layout are added.

It reads top down for someone who has never run a hiring loop: the shared header, the answer as the heading, each
candidate's verdict, the picture as scorecard rows (svgkit 1.2.0): one row per candidate, the overall score against the
target on one scale for the frame, the figure line `3.23 · TARGET 3.00 · RESTRAINT 1.75 < FLOOR 2.50` with any skill
area under its floor kept on it, and MEETS TARGET or BELOW TARGET as a check word; the person who decides is in brass,
once, in the frame head. Geist Mono 12px for labels and figures, Geist 14px for names, no text inside a picture, no
box inside the frame. Then one thing to do next, owned by the hiring manager. Each candidate's reason and what to
discuss first follow in two columns. The skill area tables, the debrief steps, the evidence ledger and everything
technical sit in folds. Public copy uses plain words: target, skill area, scoring guide. results.json keeps its words.

A hiring packet has no project status, so the page uses no status colour. Verdicts print as text, never boxed chips.
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

VERSION = "0.3.2"
TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "template.html"
STYLE = re.compile(r"<style>(.*?)</style>", re.S)

# Layout for this page only. Everything else comes from the template's stylesheet and svgkit.CSS.
# The smallest text the page prints, at every width. The vendored template and svgkit keep their own sizes on disk
# (both are hash-pinned); the page raises any smaller size to this one as it inlines their rules.
FONT_FLOOR = 11
FONT_SIZE = re.compile(r"(font-size:\s*|font:[^;{}]*?)(\d+(?:\.\d+)?)px")


def floor_fonts(css: str) -> str:
    """Every font size below FONT_FLOOR, raised to it: font-size and the size in a font shorthand."""
    return FONT_SIZE.sub(lambda m: m.group(1) + (str(FONT_FLOOR) if float(m.group(2)) < FONT_FLOOR else m.group(2)) + "px", css)


PAGE_CSS = """
.nw{white-space:nowrap}
main.solo{margin-left:0}
.solo .slide{min-height:0}
.solo .slide.cover{min-height:0;padding-top:40px;padding-bottom:48px;justify-content:flex-start}
.solo h1{font-size:clamp(34px,4.6vw,60px);line-height:1;letter-spacing:-.04em;max-width:20ch;margin-bottom:20px}
.solo .lede{margin-bottom:24px}
.status{display:inline-block;font:400 12px/16px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--t1);white-space:nowrap}
.verdict{margin:0 0 20px;display:flex;flex-wrap:wrap;gap:8px 28px}
.next{margin-top:28px;display:grid;grid-template-columns:200px minmax(0,1fr);gap:8px 32px;align-items:baseline}
.next{border:1px solid var(--brass);border-radius:12px;padding:20px 24px;background:var(--brass-bg)}
.next>b{font:400 11px/22px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--brass)}
.next p{margin:0;font-size:16px;line-height:1.5;color:var(--t1)}
.next .who{display:flex;flex-wrap:wrap;gap:4px 24px;margin-top:10px;font:400 11.5px/16px var(--mono);color:var(--brass)}
.next .who span::before{font-size:11px;letter-spacing:.1em;color:var(--t3);margin-right:8px}
.next .who .o::before{content:"DECIDES"}.next .who .d::before{content:"BY"}
.cols{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:24px 56px;align-items:start}
.cols h3{margin-bottom:8px}
.cands,.disc,.fair{margin:0;padding:0;list-style:none}
.cands li,.disc li,.fair li{border-top:1px solid var(--line);padding:12px 0;font-size:13.5px;line-height:1.5;color:var(--t2)}
.cands li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 16px;align-items:baseline}
.cands li b{font-weight:500;color:var(--t1);font-size:14.5px}
.cands li p{grid-column:1/-1;margin:0}
.disc li span,.fair li span{display:block;font:400 11px/18px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}
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
@media (max-width:980px){.foot{padding:24px 16px 48px}.solo .slide.cover{padding-top:24px}.cols,.next{grid-template-columns:1fr}
.stack table,.stack tbody,.stack tr,.stack td{display:block}.stack tr:first-child{display:none}.stack tr{padding:10px 16px;border-bottom:1px solid var(--line)}
.stack td{border:0;padding:3px 0;display:grid;grid-template-columns:118px 1fr;gap:12px}.stack td.num{text-align:left;white-space:normal}
.stack td::before{content:attr(data-l);font:400 11px/20px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}}
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


# The signature picture: scorecard rows (svgkit 1.2.0)


def short_area(r: dict[str, Any], cid: str) -> str:
    return next(c["short"] for c in r["competencies"] if c["id"] == cid)


def under_floor(r: dict[str, Any]) -> list[str]:
    return [short_area(r, f["where"]) for f in r["flags"] if f["rule"] == "floor"]


def floor_tail(r: dict[str, Any]) -> str:
    """Each skill area under its floor, as the figure line prints it: `RESTRAINT 2.33 < FLOOR 2.50`."""
    return " · ".join(
        f"{c['short'].upper()} {c['mean']} < FLOOR {c['floor']}"
        for c in r["competencies"]
        if c["floor"] is not None and c["mean"] is not None and float(c["mean"]) < float(c["floor"])
    )


def candidate_rows(v: dict[str, Any]) -> str:
    """One row per candidate: the code, the overall score against the target on one scale for the frame (a range
    line in one unit, so relative=False), the figure line with the failing skill area kept on it, and the verdict as a
    check word: MEETS TARGET muted, BELOW TARGET in ink. The person who decides is in brass, once, in the frame head."""
    scored = [r for r in v["candidates"] if r["overall"] is not None]
    domain = sk.frame_domain([(None, float(r["overall"]), float(r["bar"])) for r in scored], relative=False)
    rows = []
    for r in v["candidates"]:
        if r["overall"] is None:
            rows.append(sk.sc_row(r["candidate"], figure=sk.figure_line("no overall score"), word=sk.check_word("not enough evidence", ink=True)))
            continue
        picture = sk.range_line(actual=float(r["overall"]), target=float(r["bar"]), domain=domain)
        figure = sk.figure_line(r["overall"], target=r["bar"], tail=floor_tail(r))
        word = sk.check_word("meets target") if r["band"] == "meets bar" else sk.check_word("below target", ink=True)
        rows.append(sk.sc_row(r["candidate"], picture=picture, figure=figure, word=word))
    when = f"by {v['by']}" if v["by"] else "no date set"
    return sk.sc_frame(
        rows,
        label=aria(v),
        title="Overall score",
        head=["Candidate", "", "Overall · target · under floor", "Verdict"],
        legend=sk.legend("target", f"target {v['bar']}") + sk.person_call(f"{v['owner']} decides", due=when),
        caption=(
            f"One row per candidate, on one scale. The dot is the overall score, the tick the target of {v['bar']}. "
            "A skill area under its floor prints on the figure line and puts the candidate below the target, whatever the overall score."
        ),
        illustrative=bool(v["illustrative"]),
    )


def keep_ids(text: str) -> str:
    """Escaped text with each candidate id (K-01) kept on one line, so a phone never breaks it at the hyphen."""
    return re.sub(r"\b([A-Z]+-\d+)\b", r'<span class="nw">\1</span>', text)


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
    return f"{v['answer'][:-1]} of {v['bar']}; " + "; ".join(says) + f". {v['owner']} decides{when}."


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
        f"<p>Skill: <code>ai-native-hiring-loop</code> {e(VERSION)}.</p>"
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
    header = sk.page_header("AI-native hiring loop", date=v["as_of"][:10], version=f"v{VERSION}", illustrative=ill)
    chips = "".join(f'<span class="status">{e(r["candidate"])}: {e(r["verdict"])}</span>' for r in v["candidates"])
    who = f'<span class="o">{e(v["owner"])}</span>'
    by = f'<span class="d">{e(v["by"])}</span>' if v["by"] else ""
    step = f'<div class="next"><b>What to do next</b><div><p>{e(v["decision"])}</p><span class="who">{who}{by}</span></div></div>'
    lede = f"{v['level']} role: {v['title'].removeprefix('Hiring loop: ')}. {v['lede']}"
    cover = (
        f'<section class="slide cover">{header}<h1>{keep_ids(e(v["answer"]))}</h1><p class="lede">{e(lede)}</p><p class="verdict">{chips}</p>{candidate_rows(v)}{step}</section>'
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
        f'<title>{e(v["title"])}</title><style>{floor_fonts(stylesheet() + sk.CSS + sk.SCORECARD_CSS + PAGE_CSS)}</style></head><body><main class="solo">{cover}{detail}{more}'
        f'<p class="foot">{e(v["foot"])}</p></main></body></html>\n'
    )
