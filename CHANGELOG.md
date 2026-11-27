# Changelog

## 0.3.3, 2026-11-27

- Full column: the heading, the intro, the next step, section text and captions run the full width of the content column, the same width as the scorecard frame (the site's rule since 2026-11-25). The page's own CSS drops its caps on text (the heading's 20ch and the folds' 80ch) and overrides the vendored template's 62ch intro and svgkit's 76ch caption after their rules, so neither hash-pinned file changes. The heading balances its lines; text breaks with `text-wrap: pretty`. A test checks the page CSS caps no text and the sample carries the override.

## 0.3.2, 2026-11-27

- The picture is scorecard rows in the grammar of the outcome scorecard on dacard.ai/update (svgkit 1.2.0, landing-loop 78784ef): one row per candidate, the overall score against the target as a range line on one scale for the frame (every target tick lines up), the figure line with any skill area under its floor kept on it (`3.23 · TARGET 3.00 · RESTRAINT 1.75 < FLOOR 2.50`), MEETS TARGET muted or BELOW TARGET in ink, and the hiring manager in brass once in the frame head. Geist Mono 12px for labels and figures, Geist 14px for names, no text inside a picture, no box inside the frame. The candidate blocks, their panel and the boxed verdict chips are gone; verdicts print as text.
- README and SKILL.md in plain words: project, target, the project file. Stored values (`meets bar`, `bar`), keys, file names and flags are unchanged. SKILL.md uses the user's own word if they say bet.
- Tests from the rollout recipe: no text inside an SVG, no scaled SVG, labels 12px and names 14px, no box inside the frame, no legacy svgkit primitive (rendered with DeprecationWarning as an error), one frame with one row per candidate and each figure line exact, one scale so every target tick lines up, brass only in the frame head, and the aria-label states the answer.

## 0.3.1, 2026-11-27

- The packet page follows the Landing Loop sample anatomy: the shared header (mark, DACARD, skill, date, version, blue Illustrative tag), the answer as the heading ("One of three candidates, K-01, meets the hiring target."), a verdict chip per candidate, the signature picture, one next step with the hiring manager in brass and the decision date, then each candidate's reason beside what to discuss first and the fairness checks. Each candidate in full, how the debrief runs, every figure with its source, and "For your engineers" (stored verdicts, commands, exit codes, project file key) are folded.
- The signature picture: one block per candidate, the overall score against the dashed target, each skill area against its floor, the shortfall hatched, and the person who decides in brass. A 720 wide variant for desktop (candidates side by side) and a 340 wide one for phones (one under another); the aria-label states the answer. Drawn with svgkit, vendored byte-identical from landing-loop 5d01756 into `scripts/vendor/` and pinned in `VENDORED.json` under `landing-loop`.
- Plain words on the page and in the Markdown twin: target for bar, skill area for competency, scoring guide for rubric and anchors, questions and tasks for items, and the bands as meets the target, below the target, not enough evidence. The Markdown tables add each skill area's floor. `results.json`, `ledger.csv` and the kit keep their words.
- `check-note` reads "meets the target", "below the target" and "under the target" as band claims, like the bar forms.
- Tests: the picture draws only printed figures, one block per candidate, a floor mark per floored skill area, brass only for the decider, no status colour, an aria-label that states the answer, plain words in public copy, and the svgkit pin.
- Design fix round 2: the heading reads "One of three candidates, K-01, meets the hiring target." (the target's figure stays in the picture and its aria-label; a candidate id never breaks at its hyphen); no text below 11px at any width (the page raises the vendored template's and svgkit's smaller sizes as it inlines them; the files on disk are unchanged); the header prints the plain name, AI-native hiring loop, and the code name moves to the engineers' fold; public copy drops record, bet, the bar, PRD, ARR and tokens, and the interview kit says Target and prints the debrief steps in the packet's plain words. `check-note` reads "meets the hiring target" as the meets verdict.
- On phones up to 440px the picture's panel gives it its full 340px, so its 11px labels render at 11px at 390 and 375 wide.

## 0.3.0, 2026-11-26

- Same shape as the Landing Loop skills. A team-level skill beside the loop: it hires the people who run the bets and writes no key in any `landing/<bet>.json`.
- `score` now writes `packet.html`, one self-contained page in the Product & Technology Leader Report style (its template vendored byte-identical at a pinned commit, `VENDORED.json`), beside its Markdown twin. Brass marks only the hiring manager's call; the page uses no status colour.
- Sample: `python3 examples/acme/sample.py` renders `examples/acme/ai-native-hiring-loop.html`, its twin, the kit and the ledger. A test checks the command reproduces the committed files byte for byte.
- Every figure carries value, unit, source, window (from, to) and as_of. Uncounted scores cite their rows. The packet prints the fairness checks as counted figures.
- Fairness: a candidate must be a code, not a name; a sheet field for a name, age, photo or school, or evidence that mentions a protected attribute or a banned criterion, blocks the packet.
- A named hiring manager (`decision.owner`) is required to score; the starters ask for one.
- `import-csv --map` reads an export whose columns are named differently.
- Python 3.11 or later; CI runs 3.11 and 3.13. Version 0.2.0 was skipped so the version matches the other loop skills.
- The page and its Markdown twin open with a one-line answer, five summary lines and the decision; the rest folds under one `<details>`.
- The Acme hiring manager is a role from the Acme org chart, Head of Product, Quoting squad, not an invented person, and the team is the Quoting squad everywhere.
- `results.json` stores every figure as a number (`value`, null when there is no eligible score) with the printed form beside it (`display`).
- `check-note` now catches a figure at the end of a sentence ("scored 3.9.") and reads a numbered-list marker as a position, not a figure.
- `run.py` and `sample.py` check for Python 3.11 before any other import. Selection and focus print in ink, not the template's green.

## 0.1.0, 2026-11-26

- First version: loop design checks, starters for PM, designer and engineer, structured questions, work samples with two independent scorers, scores before discussion, interviewer drift, CSV import, the calibration packet and the decision-note check.
