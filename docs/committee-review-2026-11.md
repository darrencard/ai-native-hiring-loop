# Committee review, 2026-11-26

A simulated review by the Product Ops Committee (Perri, Cagan, Cutler, Torres, Doshi, Rachitsky) and a VP Engineering lens (a VP Engineering or CTO at a Series B to D company). These are role-played scores, not endorsements by the people named.

Criteria, each scored 1 to 10: **Use** (would a VP Product, CPO or CTO use it this quarter), **Rigour** (code does the maths, no overclaims, a source on every figure), **Time** (install to first useful output), **Clarity** (README and SKILL.md).

## Scores by round (Use / Rigour / Time / Clarity)

| Member | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| Melissa Perri | 7 / 8 / 5 / 7 | 9 / 9 / 9 / 9 | 10 / 10 / 10 / 10 |
| Marty Cagan | 6 / 8 / 5 / 7 | 9 / 9 / 9 / 9 | 10 / 10 / 10 / 10 |
| John Cutler | 7 / 7 / 6 / 7 | 9 / 9 / 9 / 9 | 10 / 9 / 10 / 10 |
| Teresa Torres | 7 / 8 / 5 / 7 | 9 / 9 / 9 / 9 | 10 / 10 / 10 / 10 |
| Shreyas Doshi | 7 / 8 / 4 / 6 | 9 / 9 / 9 / 9 | 10 / 10 / 10 / 10 |
| Lenny Rachitsky | 7 / 8 / 5 / 7 | 9 / 9 / 9 / 10 | 9 / 10 / 10 / 10 |
| VP Engineering lens | 5 / 7 / 5 / 6 | 8 / 9 / 9 / 9 | 9 / 10 / 10 / 10 |

## What changed

Round 1 gaps, fixed before round 2:

- Time to first output (Doshi, all): hand-writing loop JSON took an hour. Added `run.py demo` (bundled example, about a second) and `run.py new --role pm|designer|engineer` starters that pass every design check.
- Engineering and design roles (VP Engineering, Cagan): only a PM example existed. Added designer and engineer starters with their own work samples.
- Independent scoring (VP Engineering, Cutler): two scorers on a work sample was advice, not a rule. Added `min_scorers`; the design check requires 2 for every work sample and the sheet check blocks an under-scored item.
- Goodhart risk (Cutler): one weighted number invites deciding by number. The packet now says the overall score summarises and does not decide.
- Four risks and discovery (Cagan, Torres): the outcome anchor now asks for the biggest of value, usability, feasibility and viability risk; the PM starter adds a criterion for the assumption to test with users first.
- Timestamp trust (Cutler, VP Engineering): "scores before discussion" rested on typed times. Sheets now record `timestamps_from`; typed or missing provenance prints a warning.
- Example output (Rachitsky): the README now shows the packet table and what it means.

Round 2 gaps, fixed before round 3:

- Interviewers score in forms, not JSON (Doshi, VP Engineering). Added `run.py import-csv` for a form or tracker export. What a stage asked comes from what was scored, so a skipped question still blocks.
- `run.py blank` writes an empty sheet with every item listed, for teams without a form.

## What held a score under 10

- **Cutler, Rigour 9.** With two scorers on a stage, interviewer drift shows on both and cannot say who is off. Needs 3 or more scorers per stage, which is a cost choice for the team, not a code fix.
- **Rachitsky, Use 9.** No real hiring loop has run through it yet; every result is on the invented Acme example. Only live use fixes this.
- **VP Engineering, Use 9.** No direct reader for a specific applicant tracking system; CSV export only. A reader per system is v0.2 work.

## Round 4, v0.3.0 (2026-11-26)

Readers: Product Ops Committee, a VP Engineering, PLG Committee (Bush, Verna, Tharin), Design Committee, Guillermo Rauch, Karri Saarinen. Role-played, not endorsements.

| Reader | Score | What held it under 10 |
|---|---|---|
| Product Ops Committee | 9 | Not yet used by a real team |
| VP Engineering | 9 | Not yet used by a real team; no direct reader for a specific applicant tracking system (CSV export with `--map` only) |
| PLG Committee | 9 | Not yet used by a real team. One command shows the sample page in under a second |
| Design Committee | 10 | |
| Guillermo Rauch | 10 | |
| Karri Saarinen | 10 | |

Fixed in this round: the HTML page in the Leader Report style with brass only for the hiring manager's call; unit, window and as_of on every figure; fairness checks printed as counted figures; candidate codes and protected attributes enforced; a named hiring manager required to score; `--map` for exports; a byte-for-byte sample test.
