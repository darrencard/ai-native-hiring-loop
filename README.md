# Hire for judgment, not AI enthusiasm

A free Claude skill that designs a hiring loop for an AI-fluent product, design or engineering role, then combines its scores in code with bias guardrails that block the packet.

**Why it matters:** anyone can say they use AI. This loop tests whether a candidate writes evals, weighs cost per task and knows when not to use a model, and every candidate is scored on the same questions before anyone talks.

**What you get:**

- **A role scorecard.** First-year outcomes, weighted competencies and anchors 1 to 4. Starters for PM, designer and engineer.
- **Work samples with rubrics.** Tasks that score evals, cost and restraint separately, each scored by two people who do not confer.
- **Structured questions.** Written once, asked of every candidate, in order.
- **A calibration packet.** Each candidate's band, what to discuss, and a ledger row for every figure.

**The guardrails:** a skipped or added question, a score recorded after the debrief starts, a score with no evidence, a work sample with one scorer, or "culture fit" anywhere in the loop stops the packet. A decision note that prints an uncomputed figure or claims a candidate "will succeed" is blocked too.

## Install: paste this into Claude Code

```text
Install the AI-native hiring loop skill from https://github.com/darrencard/ai-native-hiring-loop: copy the skills/ai-native-hiring-loop folder into my Claude skills folder, run python3 -m unittest discover -s evals in the repository to check it, and show me the packet from run.py demo. Then start a hiring loop for ROLE with run.py new --role pm, designer or engineer. Ask me only for what you cannot infer: our outcomes for the first year, any weight changes, and who scores each stage. Run check-design until it passes and give me the interview kit.
```

Replace `ROLE`, for example "a senior product manager for our AI assistant".

## What the packet looks like

From the bundled example (Acme is invented; every figure is illustrative):

| Candidate | Overall | Band | Evals | Cost | Restraint |
|---|---|---|---|---|---|
| K-01 | 3.33 | meets bar | 3.50 | 3.00 | 4.00 |
| K-02 | 3.23 | below bar | 4.00 | 3.00 | 1.50 |
| K-03 | 2.75 | below bar | 2.00 | 3.00 | 3.00 |

K-02 clears the overall bar but is below bar: restraint sits under its floor. K-03's interviewers differ by 2 points on eval design, so the packet puts that first in the debrief. Every figure traces to the score rows behind it in `ledger.csv`.

## How it works

1. `run.py demo --out out` runs the example end to end in about a second.
2. `run.py new --role engineer --out loop.json`, edit it, then `run.py check-design loop.json --kit kit.md`.
3. Collect scores before the debrief: export your form or tracker to CSV and run `run.py import-csv`, or fill `run.py blank` sheets.
4. `run.py score loop.json scores/*.json --out out` runs every guardrail, then writes `results.json`, `ledger.csv` and `packet.md`.
5. `run.py check-note out/results.json note.md` checks the hiring manager's decision note.

Python 3.9 or later, standard library only, no network calls. The method is in [references/method.md](skills/ai-native-hiring-loop/references/method.md).

**Limits:** "scores before discussion" is only as good as the timestamps. Export them from your applicant tracking system or form tool; typed times print a warning. The skill does not screen CVs, rank people from public profiles, predict job performance or make the decision. A named hiring manager does that.

## Tests

```bash
python3 -m unittest discover -s evals -v
```

MIT licensed. Version 0.1.0. Made by [Dacard](https://www.dacard.ai).
