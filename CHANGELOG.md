# Changelog

## 0.3.0, 2026-11-26

- Same shape as the Landing Loop skills. A team-level skill beside the loop: it hires the people who run the bets and writes no key in any `landing/<bet>.json`.
- `score` now writes `packet.html`, one self-contained page in the Product & Technology Leader Report style (its template vendored byte-identical at a pinned commit, `VENDORED.json`), beside its Markdown twin. Brass marks only the hiring manager's call; the page uses no status colour.
- Sample: `python3 examples/acme/sample.py` renders `examples/acme/ai-native-hiring-loop.html`, its twin, the kit and the ledger. A test checks the command reproduces the committed files byte for byte.
- Every figure carries value, unit, source, window (from, to) and as_of. Uncounted scores cite their rows. The packet prints the fairness checks as counted figures.
- Fairness: a candidate must be a code, not a name; a sheet field for a name, age, photo or school, or evidence that mentions a protected attribute or a banned criterion, blocks the packet.
- A named hiring manager (`decision.owner`) is required to score; the starters ask for one.
- `import-csv --map` reads an export whose columns are named differently.
- Python 3.11 or later; CI runs 3.11 and 3.13. Version 0.2.0 was skipped so the version matches the other loop skills.

## 0.1.0, 2026-11-26

- First version: loop design checks, starters for PM, designer and engineer, structured questions, work samples with two independent scorers, scores before discussion, interviewer drift, CSV import, the calibration packet and the decision-note check.
