# Hire for judgment, not AI enthusiasm

A free Claude skill that designs a hiring loop for an AI-fluent product, design or engineering role, then combines its scores in code with bias guardrails that block the packet.

**Why it matters:** anyone can say they use AI. This loop tests whether a candidate writes evals, weighs cost per task and knows when not to use a model, and every candidate is scored on the same questions before anyone talks.

**What you get:**

- **A role scorecard.** First-year outcomes, weighted competencies and anchors 1 to 4.
- **Work samples with rubrics.** Tasks that score evals, cost and restraint separately.
- **Structured questions.** Written once, asked of every candidate, in order.
- **A calibration packet.** Each candidate's band, what to discuss, and a ledger row for every figure.

**The guardrails:** a skipped or added question, a score recorded after the debrief starts, a score with no evidence, or "culture fit" anywhere in the loop stops the packet. A decision note that prints an uncomputed figure or claims a candidate "will succeed" is blocked too.

## Install: paste this into Claude Code

```text
Install the AI-native hiring loop skill from https://github.com/darrencard/ai-native-hiring-loop: copy the skills/ai-native-hiring-loop folder into my Claude skills folder, then run python3 -m unittest discover -s evals in the repository to check it. Then design a hiring loop for ROLE on my team. Ask me only for what you cannot infer: the outcomes for the first year, the competencies and their weights, and who scores each stage. Run check-design until it passes and give me the interview kit.
```

Replace `ROLE`, for example "a senior product manager for our AI assistant".

## How it works

1. `run.py check-design loop.json --kit kit.md` checks the design and writes the one kit every interviewer uses.
2. Each interviewer fills a score sheet before the debrief.
3. `run.py score loop.json scores/*.json --out out` runs every guardrail, then writes `results.json`, `ledger.csv` and `packet.md`.
4. `run.py check-note out/results.json note.md` checks the hiring manager's decision note.

Python 3.9 or later, standard library only, no network calls. The method is in [references/method.md](skills/ai-native-hiring-loop/references/method.md).

**Worked example:** [evals/fixtures/acme](evals/fixtures/acme), a senior PM for the AI assistant at Acme, an invented invoicing company for trades businesses. Every name, figure and score in it is illustrative.

**What it does not do:** screen CVs, rank people from public profiles, predict job performance or make the decision. A named hiring manager does that.

## Tests

```bash
python3 -m unittest discover -s evals -v
```

MIT licensed. Version 0.1.0. Made by [Dacard](https://www.dacard.ai).
