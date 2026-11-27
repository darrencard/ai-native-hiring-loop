"""The calibration packet as one self-contained HTML page, in the Leader Report style guide.

The page takes the report's whole stylesheet from its template (assets/vendor/template.html, vendored
byte-identical at a pinned commit, see VENDORED.json), so it is the same brand family as the deck. It follows the
report's references/design.md: mono capitals for labels, sans for sentences; hairlines, not boxes; brass only for
a person's call (the hiring manager and the decision date); grey for agent work and ink for the figure.
Selection and focus print in ink: the template paints them green, and green is did-it-land's colour.

A leader gets the point from the top: a one-line answer, five summary lines and the decision with its owner
and date. Everything else folds under one <details>.

A hiring packet has no bet status, so the page uses no status colour at all. A band (meets bar, below bar,
insufficient evidence) is this skill's own check word and prints as a plain mono chip.

It prints only what packet.view() holds, so it says exactly what the Markdown twin says. Nothing is loaded from
the network, nothing depends on the clock or the machine, and every piece of text from a file is escaped.

Standard library only. Python 3.11 or later.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from packet import view

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "vendor" / "template.html"
STYLE = re.compile(r"<style>(.*?)</style>", re.S)
SCALE = (1, 4)  # the score scale; the range line is drawn across it

# Layout for this page only. Everything else comes from the template's stylesheet.
PAGE_CSS = """
main.solo{margin-left:0}
.solo .slide{min-height:0}
.solo .slide.cover{padding-top:72px;padding-bottom:40px}
.solo .lede{margin-bottom:8px}
.head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:baseline;gap:10px 24px}
.head h2{margin-bottom:12px}
.rows{margin-top:8px}
.rows>div{display:grid;grid-template-columns:200px minmax(0,1fr);gap:6px 36px;border-top:1px solid var(--line);padding:14px 0}
.rows>div>span:first-child{font:400 10px/22px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t3)}
.rows>div>span:last-child{color:var(--t2);font-size:13.5px}
.solo .need{margin-top:24px}
.solo .need-r{margin-top:6px}
.solo .tablewrap{margin-top:20px}
.solo .sc-h,.solo .sc-r{grid-template-columns:minmax(0,1.2fr) minmax(0,1fr) 168px}
.sc-n .sc-d{max-width:46ch}
.solo ol.steps{display:block;margin:8px 0 0;padding-left:20px;color:var(--t2);font-size:13.5px;max-width:80ch}
.solo ol.steps li{display:list-item;padding:8px 0;border-top:1px solid var(--line)}
.ledger td{font-size:11.5px}
.ledger td.src{font-family:var(--mono);font-size:10.5px;color:var(--t3);word-break:break-word}
.answer{font-size:22px;line-height:30px;color:var(--t1);max-width:760px;margin:6px 0 14px}
.five{margin:0;padding-left:18px;color:var(--t2);font-size:14px;line-height:24px;max-width:820px}
details.more{margin:0}
details.more>summary{max-width:1120px;margin:0 auto;padding:22px 40px;cursor:pointer;border-top:1px solid var(--line)}
details.more>summary{font:400 11px/16px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--t1)}
::selection{background:var(--t1);color:var(--bg)}
:focus-visible{outline:2px solid var(--t1);outline-offset:3px;border-radius:3px}
.foot{max-width:1120px;margin:0 auto;padding:28px 40px 64px;color:var(--t3);font-size:12px}
@media (max-width:980px){.rows>div{grid-template-columns:1fr;gap:2px}.foot{padding:24px 16px 48px}details.more>summary{padding:18px 16px}.solo .slide.cover{padding-top:48px}
.solo .slide{padding:40px 16px 32px}.solo .sc{padding:6px 16px 14px}.solo .sc-h,.solo .sc-r{grid-template-columns:1fr;gap:8px}.sc-h span:last-child,.sc-s{text-align:left}}
"""

MARK = (
    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">'
    '<rect x="2" y="13" width="3" height="7" fill="var(--agent)"/><rect x="7" y="10" width="3" height="10" fill="var(--agent)"/>'
    '<rect x="12" y="2" width="1.5" height="20" fill="var(--brass)"/><rect x="16" y="4" width="4" height="16" fill="var(--t1)"/></svg>'
)


def e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def stylesheet() -> str:
    """The report template's whole stylesheet, fonts included."""
    try:
        found = STYLE.search(TEMPLATE.read_text(encoding="utf-8"))
    except OSError:
        found = None
    return found.group(1) if found else ""


def _x(value: str) -> str:
    lo, hi = SCALE
    v = max(lo, min(hi, float(value)))
    return f"{round((v - lo) / (hi - lo) * 100, 1):g}"


def range_line(overall: str | None, bar: str) -> str:
    """The score on the 1 to 4 scale, the bar as a tick. Grey track, ink dot, no status colour."""
    if overall is None:
        return ""
    return f'<span class="bl" aria-hidden="true"><i class="tr"></i><i class="goal" style="left:{_x(bar)}%"></i><i class="ac" style="left:{_x(overall)}%"></i></span>'


def band_chip(band: str) -> str:
    return f'<span class="chip">{e(band)}</span>'


def scorecard(v: dict[str, Any]) -> str:
    rows = []
    for r in v["candidates"]:
        ai = r["ai_judgment"]
        detail = f"Evals {ai['evals'] or 'none'} · Cost {ai['cost'] or 'none'} · Restraint {ai['restraint'] or 'none'}"
        rows.append(
            f'<div class="sc-r"><div class="sc-n"><span><a href="#{e(r["candidate"])}">{e(r["candidate"])}</a></span><span class="sc-d">{e(detail)}</span></div>'
            f'<div class="sc-v">{range_line(r["overall"], r["bar"])}<span class="sc-l"><b>{e(r["overall"] or "none")}</b> &middot; <em>Bar</em> {e(r["bar"])}</span></div>'
            f'<div class="sc-s">{band_chip(r["band"])}</div></div>'
        )
    head = '<div class="sc-h"><span>Candidate and AI judgment</span><span>Overall &middot; bar, 1 to 4</span><span>Band</span></div>'
    return f'<div class="tablewrap sc">{head}{"".join(rows)}</div>'


def candidate_section(r: dict[str, Any], n: int) -> str:
    meta = f'<div class="meta"><span>Candidate {n:02d}</span><span>{e(r["eligible"])} scores counted</span></div>'
    head = f'<div class="head"><h2 id="{e(r["candidate"])}">{e(r["candidate"])}</h2>{band_chip(r["band"])}</div>'
    body = "".join(
        f'<tr><td>{e(c["id"])} {e(c["name"])}</td><td class="num">{e(c["weight"])}</td><td class="num">{e(c["mean"] or "none")}</td>'
        f'<td class="num">{e(c["raters"])}</td><td class="num">{e(c["spread"] or "none")}</td></tr>'
        for c in r["competencies"]
    )
    table = (
        '<div class="tablewrap"><table><thead><tr><th>Competency</th><th class="num">Weight</th><th class="num">Mean</th>'
        f'<th class="num">Interviewers</th><th class="num">Spread</th></tr></thead><tbody>{body}</tbody></table></div>'
    )
    flags = "".join(f"<div><span>To discuss: {e(f['rule'])}</span><span>{e(f['message'])}</span></div>" for f in r["flags"])
    flags_html = f'<div class="rows">{flags}</div>' if flags else ""
    return f'<section class="slide">{meta}{head}<p class="lede">{e(r["why"])}</p>{table}{flags_html}</section>'


def ledger_table(ledger: list[dict[str, Any]]) -> str:
    rows = "".join(
        f'<tr><td>{e(r["id"])}</td><td>{e(r["figure"])}</td><td class="num">{e(r["display"])}</td><td>{e(r["unit"])}</td>'
        f'<td class="mo">{e(r["window"]["from"][:16])} to {e(r["window"]["to"][:16])}</td><td class="src">{e(r["source"])}</td></tr>'
        for r in ledger
    )
    return (
        f"<details><summary>Every figure, with its source ({e(len(ledger))} rows)</summary>"
        '<div class="tablewrap ledger"><table><thead><tr><th>ID</th><th>Figure</th><th class="num">Value</th><th>Unit</th><th>Window</th><th>Source</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div></details>"
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
    meta = [f"Debrief {v['as_of'][:10]}", f"Loop {v['version']}", "ai-native-hiring-loop"]
    meta_html = "".join(f"<span>{e(m)}</span>" for m in meta)
    if v["illustrative"]:
        meta_html += '<span class="ill">Illustrative</span>'
    by = f'<span class="mono" style="color:var(--brass);font-size:11px">by {e(v["by"])}</span>' if v["by"] else '<span class="mono t3" style="font-size:11px">no date set</span>'
    decision = (
        f'<div class="need"><b>Decision</b><div class="need-r"><p>{e(v["decision"])}</p>'
        f'<span class="mono" style="color:var(--brass);font-size:11px">{e(v["owner"])}</span>{by}</div></div>'
    )
    sections = "".join(candidate_section(r, i) for i, r in enumerate(v["candidates"], start=1))
    drift = ""
    if v["pool_flags"]:
        drift_rows = "".join(f"<div><span>Interviewer {e(f['where'])}</span><span>{e(f['message'])}</span></div>" for f in v["pool_flags"])
        drift = f'<section class="slide"><div class="meta"><span>Interviewers</span></div><h2>Interviewer calibration</h2><div class="rows">{drift_rows}</div></section>'
    guard_rows = "".join(f"<div><span>{e(k)}</span><span>{e(t)}</span></div>" for k, t in v["guardrails"])
    guard_rows += "".join(f"<div><span>Warning</span><span>{e(w)}</span></div>" for w in v["warnings"])
    steps = "".join(f"<li>{e(s)}</li>" for s in v["steps"])
    team = f"{v['level']}. {v['team']}"
    five = "".join(f"<li>{e(s)}</li>" for s in v["summary"])
    return (
        '<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{e(v["title"])}</title><style>{stylesheet()}{PAGE_CSS}</style></head><body><main class="solo">'
        f'<section class="slide cover"><div class="brand">{MARK}<span translate="no">DACARD</span></div><div class="meta">{meta_html}</div>'
        f'<h1>{e(v["title"])}</h1><p class="answer">{e(v["answer"])}</p><ul class="five">{five}</ul>{decision}</section>'
        '<details class="more"><summary>The full packet: the role, each candidate, fairness, the debrief steps and the evidence ledger</summary>'
        f'<section class="slide"><div class="meta"><span>Role</span></div><p class="lede">{e(v["lede"])}</p><p class="sub">{e(team)}</p></section>'
        f'<section class="slide"><div class="meta"><span>Scorecard</span></div><h2>Every candidate, against the bar</h2>{scorecard(v)}'
        '<p class="sub">The overall score summarises; it does not decide. Read the competency rows and the evidence first.</p></section>'
        f"{sections}{drift}"
        f'<section class="slide"><div class="meta"><span>Fairness</span></div><h2>Fairness guardrails</h2><div class="rows">{guard_rows}</div></section>'
        f'<section class="slide"><div class="meta"><span>Calibration</span></div><h2>How the debrief runs</h2><ol class="steps">{steps}</ol>'
        f'<div style="margin-top:28px">{ledger_table(ledger)}</div></section></details>'
        f'<p class="foot">{e(v["foot"])}</p></main></body></html>\n'
    )
