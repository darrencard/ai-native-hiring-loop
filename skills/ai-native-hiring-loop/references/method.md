# How the figures are computed

`scripts/aggregate.py` computes every figure. The model never does. This page says how, so any figure can be explained and checked by hand.

## Which scores count

A score counts (is "eligible") only if all of these hold:

- its item (criterion or question) is in the loop, in the stage the row names;
- the sheet records that stage as having asked it;
- it was recorded strictly before `debrief_started_at` (timestamps are compared as instants, so offsets are honoured);
- it has written evidence of at least 20 characters;
- it is the first score that interviewer gave that item.

Each item also needs at least its stage's `min_scorers` distinct interviewers with eligible scores (2 for every work sample), or the sheet is blocked.

Any score that fails one of these is also a guardrail error, so a packet with such a score does not render. The rule is applied twice on purpose: the figures never include a late score, even in code paths that skip the guardrails.

## Figures

| Figure | Method |
|---|---|
| Competency mean | Mean of every eligible item score on that competency, across interviewers |
| Interviewers scoring | Count of distinct interviewers with an eligible score on that competency |
| Spread | Highest interviewer mean minus lowest interviewer mean on that competency |
| Overall | Sum of (weight x competency mean) divided by the sum of weights |
| AI judgment (evals, cost, restraint) | Mean of eligible work-sample criterion scores tagged with that kind |
| Drift (pool) | An interviewer's mean minus the mean of all eligible scores on the same candidate and item, shown only for interviewers who scored at least 2 candidates |

Means are exact fractions. They are rounded half-up to 2 decimals only when printed.

## Band

| Band | When |
|---|---|
| `insufficient evidence` | Any competency has no eligible score |
| `below bar` | Overall is under the bar, or any competency mean is under its floor |
| `meets bar` | Otherwise |

## Flags for calibration

| Flag | When |
|---|---|
| `spread` | Spread on a competency is at least the loop's `spread_flag` |
| `near-bar` | Overall is strictly within 0.25 of the bar |
| `floor` | A competency mean is under its floor |
| `drift` | An interviewer's drift is at least 0.75 either way |

With two scorers on a stage, drift shows on both. The flag says whose anchors to compare, not who is wrong.

## Ledger

Every figure has a row in `ledger.csv`: an ID (`K-01.C2.mean`), the figure, the printed value, the source rows (`K-01.json#scores[4]`) and the method. `check-note` allows a number in a note only if it equals a ledger value, a design value (weight, floor, bar, minutes) or a method threshold.

## Timestamps

"Scores before discussion" is checked against `submitted_at`. A sheet says where those times came from in `timestamps_from`: `ats` or `form` (a system clock) or `self-reported` (typed). Typed or missing provenance prints a warning in the packet, because a typed time can be wrong or back-dated.
