"""House rules for the v0.3.0 shape: the sample, every figure's provenance, status words, fairness guardrails,
wording, versions and the vendored template. Standard library only; runs under unittest or pytest."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ai-native-hiring-loop"
FIX = SKILL / "assets" / "example" / "acme"
SAMPLE = ROOT / "examples" / "acme"
sys.path.insert(0, str(SKILL / "scripts"))

import guardrails  # noqa: E402
import importer  # noqa: E402
import render_html  # noqa: E402
import run  # noqa: E402
import svgkit  # noqa: E402

CANDIDATES = ("K-01", "K-02", "K-03")
SAMPLE_FILES = ("ai-native-hiring-loop.html", "ai-native-hiring-loop.md", "kit.md", "ledger.csv")
STATUS = re.compile(r"\b(landed|watch|stalled)\b", re.I)
TEXT = [
    p
    for p in ROOT.rglob("*")
    if p.is_file()
    and p.suffix in {".md", ".py", ".json", ".toml", ".yml", ".csv", ".html"}
    and not {".git", ".ruff_cache", "vendor", "__pycache__", ".pytest_cache"} & set(p.parts)
]
BANNED = re.compile(r"\b(AI-powered|unlock\w*|supercharge\w*|seamless\w*|robust\w*|get started|sign up|leverag(e|es|ed|ing))\b", re.I)
AMERICAN = re.compile(r"\b(behavior\w*|organiz\w*|prioritiz\w*|analyz\w*|optimiz\w*|colors?)\b", re.I)


def visible(html: str) -> str:
    """The page text a reader sees: no stylesheet, no tags."""
    return re.sub(r"<[^>]+>", " ", re.sub(r"<style>.*?</style>", " ", html, flags=re.S))


def build():
    return run.build(json.loads((FIX / "loop.json").read_text(encoding="utf-8")), [str(FIX / "scores" / f"{c}.json") for c in CANDIDATES])


def sheet(cand: str) -> dict:
    return json.loads((FIX / "scores" / f"{cand}.json").read_text(encoding="utf-8"))


class Sample(unittest.TestCase):
    def test_the_readme_command_reproduces_the_committed_sample(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("python3 examples/acme/sample.py", readme)
        with tempfile.TemporaryDirectory() as d:
            done = subprocess.run([sys.executable, str(SAMPLE / "sample.py"), "--into", d], capture_output=True, text=True, check=False)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), sorted(SAMPLE_FILES))
            for name in SAMPLE_FILES:
                self.assertEqual((Path(d) / name).read_bytes(), (SAMPLE / name).read_bytes(), name)

    def test_writes_no_landing_record(self):
        # Outside the loop: a team-level skill writes no key in any landing/<bet>.json.
        self.assertFalse((SAMPLE / "landing").exists())
        self.assertFalse(list(ROOT.rglob("landing/*.json")))
        for p in (SKILL / "scripts").glob("*.py"):
            self.assertNotIn("landing/", p.read_text(encoding="utf-8"), p)

    def test_page_is_self_contained_and_marked_illustrative(self):
        html = (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")
        self.assertNotRegex(html, r"""(src|href)=["']https?://""")
        self.assertNotIn("@import", html)
        self.assertIn('<span class="sk-ill">Illustrative</span>', html)
        self.assertIn(":root{--ill:#74A5DA}", html, "the Illustrative tag is blue")
        self.assertIn("Illustrative", (SAMPLE / "ai-native-hiring-loop.md").read_text(encoding="utf-8"))

    def test_brass_marks_only_the_hiring_managers_call(self):
        html = (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")
        css = html.split("</style>", 1)[0].split(render_html.floor_fonts(svgkit.CSS + svgkit.SCORECARD_CSS), 1)[1]
        rules = re.findall(r"[^}]*var\(--brass[^}]*}", css)
        self.assertTrue(rules and all(r.lstrip().startswith((".next", "}.next")) for r in rules), "brass is only the hiring manager's box")
        body = re.sub(r"<svg.*?</svg>", "", html.split("</style>", 1)[1], flags=re.S)
        self.assertNotIn("--brass", body)
        self.assertEqual(re.findall(r'class="o">([^<]*)<', body), ["Head of Product, Quoting squad"])
        self.assertEqual(re.findall(r'class="d"><span class="nw">([^<]*)<', body), ["2026-11-23"])
        self.assertEqual(body.count('class="next"'), 1)
        # In the rows, brass is the person who decides, once, in the frame head: never in a row.
        frame = svgkit.frames_in(html)[0]
        self.assertEqual(re.findall(r'<span class="sc-o">.*?</svg>([^<]+)</span>', frame), ["Head of Product, Quoting squad decides"])
        head = frame.split('<div class="sc-b">', 1)[0]
        self.assertIn('class="sc-o"', head)
        self.assertIn('<span class="sc-w">by <span class="nw">2026-11-23</span></span>', head)

    def test_no_status_colour_or_word_on_the_page(self):
        html = (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")
        body = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
        for colour in ("--landed", "--watch", "--stalled", 'class="st ', "ac landed", "rd "):
            self.assertNotIn(colour, body)
        self.assertIsNone(STATUS.search(visible(html)))
        self.assertNotRegex(svgkit.frames_in(html)[0], r'class="ac (landed|watch|stalled)"')


class Figures(unittest.TestCase):
    def test_every_figure_carries_value_unit_source_window_and_as_of(self):
        out = build()
        self.assertGreater(len(out["ledger"]), 50)
        for r in out["ledger"]:
            self.assertTrue(r["value"] is None or isinstance(r["value"], (int, float)), r["id"])
            self.assertNotIsInstance(r["value"], bool, r["id"])
            for key in ("display", "unit", "source", "as_of"):
                self.assertTrue(r[key], f"{r['id']} {key}")
            self.assertTrue(r["window"]["from"] and r["window"]["to"], r["id"])
            self.assertLessEqual(r["window"]["from"], r["window"]["to"], r["id"])
            self.assertEqual(r["as_of"], r["window"]["to"], r["id"])

    def test_committed_ledger_has_the_same_columns(self):
        rows = list(csv.DictReader(io.StringIO((SAMPLE / "ledger.csv").read_text(encoding="utf-8"))))
        for r in rows:
            for key in ("value", "unit", "source", "window_from", "window_to", "as_of"):
                self.assertTrue(r[key], f"{r['id']} {key}")

    def test_every_number_on_the_page_is_a_ledger_value_or_a_design_fact(self):
        out = build()
        loop = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        import packet

        html = re.sub(r"<style>.*?</style>", " ", (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8"), flags=re.S)
        text = re.sub(r"<[^>]+>", "\n", html)  # one line per element, so a table row is not read as one sentence
        text = text.split("Every figure, with its source", 1)[0]  # the ledger table itself holds sources, not claims
        self.assertEqual(packet.check_note(text, loop, out["results"], out["ledger"]), [])

    def test_band_words_are_the_only_verdicts(self):
        out = build()
        self.assertEqual({r["band"] for r in out["results"]} - {"meets bar", "below bar", "insufficient evidence"}, set())
        for name in ("ai-native-hiring-loop.md", "kit.md"):
            self.assertIsNone(STATUS.search((SAMPLE / name).read_text(encoding="utf-8")), name)


class Fairness(unittest.TestCase):
    def test_a_name_instead_of_a_code_blocks(self):
        s = sheet("K-01")
        s["candidate"] = "Alex Example"
        self.assertIn("candidate-code", {f["rule"] for f in guardrails.check_sheet(json.loads((FIX / "loop.json").read_text()), s)})

    def test_a_protected_field_blocks(self):
        lp = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        for key in ("age", "school", "photo"):
            s = sheet("K-01")
            s[key] = "x"
            self.assertIn("protected-attribute", {f["rule"] for f in guardrails.check_sheet(lp, s)}, key)
        s = sheet("K-01")
        s["scores"][0]["notes"] = "x"
        self.assertIn("unexpected-field", {f["rule"] for f in guardrails.check_sheet(lp, s)})

    def test_evidence_about_the_person_blocks(self):
        lp = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        for text in (
            "Strong evals but she is pregnant, so timing is hard.",
            "Seems too young for a senior role, though the cases were good.",
            "Great energy, a real culture fit for the squad.",
        ):
            s = sheet("K-02")
            s["scores"][0]["evidence"] = text
            rules = {f["rule"] for f in guardrails.check_sheet(lp, s)}
            self.assertTrue(rules & {"protected-attribute", "banned-criterion"}, text)

    def test_work_words_are_not_mistaken_for_protected_ones(self):
        self.assertEqual(guardrails.protected_terms("Disabled the flag, used the accent colour, attached a job photo, handled a race in the queue."), [])

    def test_no_named_hiring_manager_blocks_the_packet(self):
        lp = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        del lp["decision"]
        out = run.build(lp, [str(FIX / "scores" / f"{c}.json") for c in CANDIDATES])
        self.assertTrue(out["blocked"])
        self.assertEqual([f["rule"] for f in out["findings"] if f["level"] == "error"], ["decision-owner"])

    def test_same_questions_figure_counts_every_candidate(self):
        g = {r["id"]: r["value"] for r in build()["guardrails"]}
        self.assertEqual((g["pool.candidates"], g["pool.same_questions"], g["pool.items"], g["pool.after_debrief"]), (3, 3, 14, 0))


class DataIn(unittest.TestCase):
    def test_map_reads_an_export_with_its_own_column_names(self):
        src = (FIX / "form-export.csv").read_text(encoding="utf-8")
        header, rest = src.split("\n", 1)
        renamed = header.replace("candidate", "Candidate ID").replace("submitted_at", "Submitted At")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "export.csv"
            p.write_text(renamed + "\n" + rest, encoding="utf-8")
            rows = importer.read_rows(p, {"candidate": "Candidate ID", "submitted_at": "Submitted At"})
            self.assertEqual(rows, importer.read_rows(FIX / "form-export.csv"))
            with self.assertRaises(importer.SchemaError) as e:
                importer.read_rows(p)
            self.assertIn("--map candidate=", str(e.exception))


class Wording(unittest.TestCase):
    def test_no_em_or_en_dashes(self):
        for p in TEXT:
            text = p.read_text(encoding="utf-8")
            self.assertNotIn(chr(0x2014), text, p)
            self.assertNotIn(chr(0x2013), text, p)

    def test_no_banned_words(self):
        for p in TEXT:
            if p.name == "test_house.py":
                continue
            text = p.read_text(encoding="utf-8")
            text = visible(text) if p.suffix == ".html" else text
            m = BANNED.search(text)
            self.assertIsNone(m, f"{p}: {m and m.group(0)}")

    def test_british_spelling_in_copy(self):
        for p in [*ROOT.glob("*.md"), *SKILL.rglob("*.md"), SAMPLE / "ai-native-hiring-loop.md", SAMPLE / "kit.md"]:
            m = AMERICAN.search(p.read_text(encoding="utf-8"))
            self.assertIsNone(m, f"{p}: {m and m.group(0)}")
        m = AMERICAN.search(visible((SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")))
        self.assertIsNone(m, m and m.group(0))

    def test_no_status_word_in_copy(self):
        for p in TEXT:
            if p.name == "test_house.py" or p.suffix == ".html":
                continue
            m = STATUS.search(p.read_text(encoding="utf-8"))
            self.assertIsNone(m, f"{p}: {m and m.group(0)}")


class Versions(unittest.TestCase):
    def test_versions_agree(self):
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
        skill = re.search(r'version: "([^"]+)"', (SKILL / "SKILL.md").read_text(encoding="utf-8")).group(1)
        self.assertEqual({plugin, project, skill, render_html.VERSION}, {"0.3.4"})
        self.assertTrue((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("\n## ", 2)[1].startswith("0.3.4, 2026-11-27"))

    def test_vendored_files_match_their_pins(self):
        pins = json.loads((SKILL / "VENDORED.json").read_text(encoding="utf-8"))
        svgkit_pin = pins["landing-loop"]
        self.assertEqual(svgkit_pin["commit"], "78784efd2ecd5282f6ec264e545ce2075e459be2")
        for path, pin in {**pins["files"], **svgkit_pin["files"]}.items():
            self.assertEqual(hashlib.sha256((SKILL / path).read_bytes()).hexdigest(), pin["sha256"], f"{path} changed. Copy it again from its pinned commit.")
        self.assertEqual(sorted(p.name for p in (SKILL / "scripts" / "vendor").glob("*.py")), ["svgkit.py"])
        self.assertEqual(svgkit_pin["files"]["scripts/vendor/svgkit.py"]["sha256"], "ceb6a0b094d4d5291f22d62ed6d9f528f955ec4599478306a0c2187152febf6d")

    def test_old_python_is_refused_with_a_message(self):
        text = (SKILL / "scripts" / "run.py").read_text(encoding="utf-8")
        self.assertIn("sys.version_info < (3, 11)", text)


ORG_CHART = {"Head of Product, Quoting squad", "Lead, Quoting squad", "Tech lead, Quoting squad", "Product manager, Quoting squad"}


class FixRound(unittest.TestCase):
    """The independent review: scannable page, org-chart roles, the Quoting squad, numbers as numbers, the Python floor."""

    @classmethod
    def setUpClass(cls):
        cls.page = (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")

    def test_the_page_follows_the_sample_anatomy(self):
        body = self.page.split('<main class="solo">', 1)[1]
        order = [
            'class="sk-hdr"',
            '<h1>One of three candidates, <span class="nw">K-01</span>, meets the hiring target.</h1>',
            '<span class="status">K-01: meets the target</span>',
            'class="sc scg"',
            "What to do next",
            'class="cols"',
            "<details><summary>Each candidate in full</summary>",
            "<details><summary>Every figure, with its source</summary>",
            "<details><summary>For your engineers</summary>",
        ]
        at = [body.index(x) for x in order]
        self.assertEqual(at, sorted(at))
        self.assertNotIn("<table", body.split("<details>", 1)[0], "every table is folded")
        top = body.split('<section class="slide">', 1)[0]
        self.assertLess(len(svgkit.page_text(top).split()), 250, "the unfolded top must read in 30 seconds")

    def test_owner_is_one_org_chart_role_and_no_invented_person(self):
        loop = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        self.assertIn(loop["decision"]["owner"], ORG_CHART)
        self.assertNotIn("role", loop["decision"])
        for p in TEXT:
            text = p.read_text(encoding="utf-8")
            if p.name == "test_house.py":
                continue
            for word in ("Jordan", "Vale", "Acme Assist", "quote-drafting assistant"):
                self.assertNotIn(word, text, p)

    def test_the_team_is_the_quoting_squad_on_the_page_and_in_the_readme(self):
        self.assertIn("Quoting squad, one of 12 squads at Acme", visible(self.page))
        self.assertIn("Quoting squad", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_results_json_stores_numbers_as_numbers(self):
        with tempfile.TemporaryDirectory() as d, redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(["demo", "--out", d]), 0)
            payload = json.loads((Path(d) / "results.json").read_text(encoding="utf-8"))
        k01 = next(r for r in payload["results"] if r["candidate"] == "K-01")
        self.assertEqual((k01["overall"], k01["bar"]), (3.33, 3.0))
        self.assertTrue(all(isinstance(c["mean"], float) for c in k01["competencies"]))
        row = next(r for r in payload["ledger"] if r["id"] == "K-01.overall")
        self.assertEqual((row["value"], row["display"]), (3.33, "3.33"))
        for r in payload["ledger"]:
            self.assertTrue(r["value"] is None or type(r["value"]) in (int, float), r["id"])
        self.assertIn('"value": 3.33,', (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_selection_and_focus_print_in_ink(self):
        css = self.page.split("</style>", 1)[0]
        self.assertLess(css.find("::selection{background:var(--landed)"), css.rfind("::selection{background:var(--t1)"))
        self.assertIn(":focus-visible{outline:2px solid var(--t1)", css.rsplit("::selection", 1)[1])

    def test_a_figure_at_the_end_of_a_sentence_is_still_checked(self):
        import packet

        out = build()
        loop = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        found = packet.check_note("K-01 scored 3.9.", loop, out["results"], out["ledger"])
        self.assertEqual([f["rule"] for f in found], ["figure-not-computed"])
        self.assertEqual(packet.check_note("K-01 scored 3.33.\n5. Next step.", loop, out["results"], out["ledger"]), [])

    def test_entry_scripts_check_the_version_before_any_other_import(self):
        import ast

        for path in (SKILL / "scripts" / "run.py", SAMPLE / "sample.py"):
            body = [n for n in ast.parse(path.read_text(encoding="utf-8")).body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            self.assertEqual([type(n).__name__ for n in body[:3]], ["ImportFrom", "Import", "If"], path.name)
            self.assertEqual([a.name for a in body[1].names], ["sys"], path.name)
            self.assertIn("version_info", ast.unparse(body[2].test), path.name)

    def test_an_old_python_gets_the_plain_message(self):
        old = next((p for p in ("/usr/bin/python3", "/usr/bin/python3.9") if Path(p).exists()), None)
        if not old:
            self.skipTest("no system Python on this machine")
        probe = subprocess.run([old, "-c", "import sys; print(sys.version_info >= (3, 11))"], capture_output=True, text=True, check=False)
        if probe.stdout.strip() != "False":
            self.skipTest("the system python3 is 3.11 or later")
        for path in (SKILL / "scripts" / "run.py", SAMPLE / "sample.py"):
            r = subprocess.run([old, str(path), "--help"], capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 1, path.name)
            self.assertIn("needs Python 3.11 or later; try python3.12", r.stderr)
            self.assertNotIn("Traceback", r.stderr)


class Visual(unittest.TestCase):
    """One row per candidate on one scale, the failing skill area on the figure line, the person who decides in brass."""

    @classmethod
    def setUpClass(cls):
        cls.page = (SAMPLE / "ai-native-hiring-loop.html").read_text(encoding="utf-8")
        cls.frames = svgkit.frames_in(cls.page)

    def css(self) -> str:
        return self.page.split("<style>", 1)[1].split("</style>", 1)[0]

    def test_the_visual_draws_only_figures_the_page_prints(self):
        self.assertEqual(svgkit.unprinted(self.page), [])

    def test_one_frame_one_row_per_candidate_and_the_failing_area_on_the_figure_line(self):
        self.assertEqual(len(self.frames), 1)
        frame = self.frames[0]
        self.assertEqual(re.findall(r'<span class="sc-n">([^<]+)</span>', frame), list(CANDIDATES))
        lines = [re.sub(r"<[^>]+>", "", x).replace("&lt;", "<") for x in re.findall(r'<span class="sc-l">(.*?)</span>', frame)]
        self.assertEqual(
            lines,
            ["3.33 · TARGET 3.00", "3.23 · TARGET 3.00 · RESTRAINT 1.75 < FLOOR 2.50", "2.75 · TARGET 3.00 · EVAL DESIGN 2.33 < FLOOR 2.50"],
        )
        words = re.findall(r'<span class="sc-s">(.*?)</span></div>', frame)
        self.assertEqual(words, ['<span class="sc-w">meets target</span>', '<span class="sc-w ink">below target</span>', '<span class="sc-w ink">below target</span>'])

    def test_one_scale_for_the_frame_so_every_target_tick_lines_up(self):
        ticks = set(re.findall(r'class="tg" x="([^"]+)"', self.frames[0]))
        self.assertEqual(len(ticks), 1, ticks)
        self.assertEqual(self.frames[0].count('<svg class="sc-rl"'), len(CANDIDATES))

    def test_the_visual_states_the_answer(self):
        labels = [html_unescape(x) for x in re.findall(r'role="img" aria-label="([^"]+)"', self.page)]
        self.assertEqual(
            labels,
            [
                "One of three candidates, K-01, meets the hiring target of 3.00; K-01 scores 3.33 overall, meets the target; "
                "K-02 scores 3.23 overall, below the target, under its floor on Restraint; "
                "K-03 scores 2.75 overall, below the target, under its floor on Eval design. "
                "Head of Product, Quoting squad decides by 2026-11-23."
            ],
        )

    # The scorecard grammar (landing-loop tools/SCORECARD-ROLLOUT.md, svgkit 1.2.0)

    def test_no_text_inside_a_picture_and_no_picture_scales(self):
        self.assertEqual(svgkit.svgs_with_text(self.page), [], "text inside an SVG")
        self.assertEqual(svgkit.scaled_svgs_in(self.page), [], "a picture with a viewBox would scale")

    def test_labels_render_12px_and_names_14px(self):
        css = self.css()
        self.assertEqual(set(svgkit.font_sizes(css)), {"var(--sc-m)", "var(--sc-n)"})
        self.assertIn("--sc-m:calc(12px / var(--sc-z))", css)
        self.assertIn("--sc-n:calc(14px / var(--sc-z))", css)
        self.assertIn(".scg{--sc-z:1;", css, "a sample page has no zoom")

    def test_no_box_inside_the_frame_and_no_overlap(self):
        self.assertEqual(svgkit.boxes_in_frames(self.page, self.css()), [])
        self.assertNotIn('class="chip', self.page.split("<details><summary>For your engineers", 1)[0])
        self.assertNotIn("position:absolute", svgkit.SCORECARD_CSS)
        self.assertNotIn("border", re.search(r"\.status\{[^}]*\}", render_html.PAGE_CSS).group(0), "verdicts are text, never boxed chips")

    def test_no_legacy_svgkit_primitive_draws_on_the_page(self):
        import warnings

        self.assertEqual(svgkit.legacy_in(self.page), [])
        loop = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        out = build()
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            page = render_html.page(loop, out["results"], out["findings"], out["pool_flags"], out["ledger"], out["guardrails"])
        self.assertEqual(svgkit.legacy_in(page), [])

    def test_public_copy_uses_the_plain_words(self):
        # The ledger and the engineers fold print the stored words; everything before them is public copy.
        public = svgkit.page_text(self.page.split("<details><summary>Every figure, with its source", 1)[0]).lower()
        md = (SAMPLE / "ai-native-hiring-loop.md").read_text(encoding="utf-8").lower()
        for text in (public, md):
            for word in (" bar", "band", "competenc", "rubric", "anchor", "insufficient evidence", " items", "bet ", "record key", "landing/"):
                self.assertNotIn(word, text)
            # The words a reader outside the loop does not know, as whole words.
            self.assertEqual(re.findall(r"\b(records?|bets?|the bar|prds?|arr|tokens?)\b", text), [])

    def test_no_text_smaller_than_12px_at_any_width(self):
        css = " ".join(re.findall(r"<style>(.*?)</style>", self.page, re.S) + re.findall(r'style="([^"]*)"', self.page))
        sizes = [float(m) for m in re.findall(r"(?:font-size:\s*|font:[^;{}]*?)(\d+(?:\.\d+)?)px", css)]
        sizes += [float(m) for m in re.findall(r'font-size="(\d+(?:\.\d+)?)"', self.page)]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 12)
        # The vendored template is untouched on disk: the page raises its small sizes as it inlines them.
        template = ROOT / "skills/ai-native-hiring-loop/assets/vendor/template.html"
        self.assertIn("font:400 10px/16px", template.read_text(encoding="utf-8"))

    def test_header_prints_the_plain_name_and_the_fold_the_code_name(self):
        header = re.search(r'<header class="sk-hdr">.*?</header>', self.page, re.S).group(0)
        self.assertIn("<span>AI-native hiring loop</span>", header)
        self.assertNotIn("ai-native-hiring-loop", header)
        self.assertIn("<code>ai-native-hiring-loop</code>", self.page.split("<details><summary>For your engineers", 1)[1])

    def test_the_heading_names_the_count_in_words(self):
        import packet

        self.assertEqual(packet.verdict_line(["K-01"], 3), "One of three candidates, K-01, meets the hiring target.")
        self.assertEqual(packet.verdict_line(["K-01", "K-02"], 3), "Two of three candidates, K-01 and K-02, meet the hiring target.")
        self.assertEqual(packet.verdict_line(["K-01", "K-02"], 2), "Both candidates, K-01 and K-02, meet the hiring target.")
        self.assertEqual(packet.verdict_line([], 3), "None of the three candidates meets the hiring target.")

    def test_check_note_reads_the_plain_band_words(self):
        import packet

        out = build()
        loop = json.loads((FIX / "loop.json").read_text(encoding="utf-8"))
        self.assertEqual(packet.check_note("K-01 meets the target.", loop, out["results"], out["ledger"]), [])
        self.assertEqual(packet.check_note("K-01 meets the hiring target.", loop, out["results"], out["ledger"]), [])
        found = packet.check_note("K-03 meets the hiring target.", loop, out["results"], out["ledger"])
        self.assertEqual([f["rule"] for f in found], ["band-mismatch"])
        found = packet.check_note("K-02 meets the target.", loop, out["results"], out["ledger"])
        self.assertEqual([f["rule"] for f in found], ["band-mismatch"])


def html_unescape(text: str) -> str:
    import html

    return html.unescape(text)


class Readme(unittest.TestCase):
    def test_sections_in_the_house_order(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        order = ["```text", "## Try it on Acme", "## Install", "## Reads and writes", "## Key in the project file", "## Limits", "Not yet run on a real team's data.", "## Licence"]
        at = [readme.find(s) for s in order]
        self.assertNotIn(-1, at, dict(zip(order, at, strict=True)))
        self.assertEqual(at, sorted(at))
        self.assertIn("/plugin marketplace add darrencard/landing-loop", readme)
        self.assertIn("/plugin install ai-native-hiring-loop@landing-loop", readme)
        self.assertIn("hires the people who run the projects", readme)


class Cli(unittest.TestCase):
    def test_demo_writes_the_page(self):
        with tempfile.TemporaryDirectory() as d:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = run.main(["demo", "--out", d])
            self.assertEqual(code, 0, out.getvalue() + err.getvalue())
            self.assertTrue((Path(d) / "packet.html").read_text(encoding="utf-8").startswith("<!doctype html>"))


if __name__ == "__main__":
    unittest.main()
