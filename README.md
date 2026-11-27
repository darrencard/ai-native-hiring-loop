# Hire for judgment, not AI enthusiasm

```text
Install the ai-native-hiring-loop skill from https://github.com/darrencard/ai-native-hiring-loop: clone it, find a Python 3.11 or later on this machine (macOS python3 is often 3.9), run the tests with it (python -m unittest discover -s evals), and copy skills/ai-native-hiring-loop into ~/.claude/skills/ai-native-hiring-loop. Show me the Acme sample page from examples/acme/sample.py. Then start a hiring loop for ROLE with run.py new --role pm, designer or engineer. Ask me only for what you cannot infer: our first-year outcomes, any weight changes, who scores each stage, and the hiring manager who decides. Run check-design until it passes and give me the interview kit.
```

Replace `ROLE`, for example "a senior product manager for our AI assistant".

A free Claude skill that designs a structured hiring loop for an AI-fluent product, design or engineering role, then scores every interview sheet against the rubric in code.

**Why it matters:** anyone can say they use AI. This loop tests, in a work sample, whether a candidate writes evals, weighs cost per task and knows when not to use a model. Every candidate gets the same questions, and every score is recorded before anyone talks.

**Who decides:** a named hiring manager. Code sets each candidate's band (meets bar, below bar or insufficient evidence) against the bar the loop set. It never says hire.

**How it relates to the Landing Loop:** it sits beside the loop, not in it. It hires the people who run the bets.

## Try it on Acme

Acme is invented: invoicing software for trades businesses. The role is a Senior Product Manager for its quote-drafting assistant, with three invented candidates and five invented interviewers. Every figure is illustrative.

```bash
python3 examples/acme/sample.py
```

It renders [examples/acme/ai-native-hiring-loop.html](examples/acme/ai-native-hiring-loop.html) (one self-contained page in the Product & Technology Leader Report style), its Markdown twin, the interview kit and the evidence ledger, in under a second. A test checks the command reproduces the committed files byte for byte.

| Candidate | Overall | Bar | Band | Evals | Cost | Restraint |
|---|---|---|---|---|---|---|
| K-01 | 3.33 | 3.00 | meets bar | 3.50 | 3.00 | 4.00 |
| K-02 | 3.23 | 3.00 | below bar | 4.00 | 3.00 | 1.50 |
| K-03 | 2.75 | 3.00 | below bar | 2.00 | 3.00 | 3.00 |

K-02 clears the overall bar but is below bar: restraint sits under its floor. K-03's interviewers differ by 2 points on eval design, so the packet puts that first in the debrief. The decision, by 2026-11-23, is Jordan Vale's (Head of Product, invented).

## Install

As a plugin, from the Landing Loop marketplace:

```text
/plugin marketplace add darrencard/landing-loop
/plugin install ai-native-hiring-loop@landing-loop
```

Standalone: copy `skills/ai-native-hiring-loop` into `~/.claude/skills/`. You need Python 3.11 or later; the scripts say so and stop on anything older. Standard library only, nothing else to install, no network calls.

## How it works

1. `run.py new --role pm|designer|engineer --out loop.json` copies a starter. Replace the outcomes, name the hiring manager in `decision.owner`, then run `run.py check-design loop.json --kit kit.md`.
2. Interviewers score in your form or applicant tracking system. `run.py import-csv` reads its export (`--map candidate="Candidate ID"` when your columns are named differently), or fill `run.py blank` sheets.
3. `run.py score loop.json scores/*.json --out out` runs every guardrail, then writes `packet.html`, `packet.md`, `results.json` and `ledger.csv`.
4. `run.py check-note out/results.json note.md` checks the hiring manager's decision note.

## Fairness guardrails

Any one of these blocks the packet: a skipped or added question; a score recorded at or after the debrief started; a score with no written evidence; a work sample with fewer than two independent scorers; a candidate named instead of coded; a sheet field for a name, age, photo or school; evidence that mentions a protected attribute; a criterion that judges the person, not the work; no named hiring manager. A decision note that prints an uncomputed figure, states the wrong band or claims a candidate "will succeed" is blocked too.

## Reads and writes

| Reads | Writes |
|---|---|
| `loop.json` (the design), one score sheet per candidate, or a CSV export from your form or applicant tracking system | `packet.html`, `packet.md`, `results.json`, `ledger.csv`, `kit.md` |

Live first means the export from the tool that holds the system clock: your applicant tracking system or form tool. No Product & Technology Leader Report collector reads interview scores, so the CSV export is the input. The report's template is vendored at a pinned commit for the page style.

## Record key

None. This is a team-level skill, outside the bet loop: it reads the team's hiring loop, not a bet, and writes no key in any `landing/<bet>.json`. Each figure in `results.json` has the same shape the loop uses:

```json
{
  "id": "K-01.overall",
  "figure": "Overall weighted score (1 to 4)",
  "value": "3.33",
  "unit": "score, 1 to 4",
  "source": "K-01.json#scores[0]; K-01.json#scores[1]; ...",
  "window": {"from": "2026-11-16T16:00:00+00:00", "to": "2026-11-20T17:00:00+00:00"},
  "as_of": "2026-11-20T17:00:00+00:00",
  "method": "weight-averaged mean of competency scores"
}
```

## Limits

- "Scores before discussion" is only as good as the timestamps. Take them from a system clock; typed times print a warning.
- The protected-attribute check reads fields and fixed phrases. It catches the common cases, not every way bias can be written.
- With two scorers on a stage, interviewer drift shows on both and cannot say who is off. Three or more per stage fixes that, at a cost the team chooses.
- It does not screen CVs, rank people from public profiles, predict job performance or decide. A named hiring manager decides.

Not yet run on a real team's data.

More: [SKILL.md](skills/ai-native-hiring-loop/SKILL.md) for the workflow, [references/method.md](skills/ai-native-hiring-loop/references/method.md) for how each figure is computed.

## Tests

```bash
python3 -m unittest discover -s evals -v
```

## Licence

MIT. See [LICENSE](LICENSE). Version 0.3.0. Made by [Dacard](https://www.dacard.ai).

Claude is a trademark of Anthropic, PBC. This skill is made by Dacard, not by Anthropic.
