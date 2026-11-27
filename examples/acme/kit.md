# Hiring loop: Senior Product Manager, AI assistant, Senior (L6)

*Illustrative. Every name, figure and score in this kit is invented.*

Team: Acme Assist squad, one of 12 squads at Acme (invoicing software for trades businesses, Series C, about 400 people). Illustrative.. Loop version acme-spm-ai-2026-11.

## Outcomes for the first year

| ID | Outcome | Measure | By month |
|---|---|---|---|
| O1 | More quotes go out from an assistant draft with light edits, without a rise in disputed quotes | share of sent quotes that started as an assistant draft and had under a fifth of their text changed, read beside the dispute rate | 9 |
| O2 | Every assistant release is gated by an eval suite the squad owns | releases that ran the suite and met the agreed pass line before shipping, out of all assistant releases | 6 |
| O3 | Cost per drafted quote stays inside the agreed budget as usage grows | model and tool spend per drafted quote against the budget line, monthly | 12 |

## Scorecard

| ID | Competency | Weight | Floor | Serves | AI judgment |
|---|---|---|---|---|---|
| C1 | Outcome framing | 25 | none | O1, O2 | none |
| C2 | Eval design | 20 | 2.5 | O2 | evals |
| C3 | Cost judgment | 15 | none | O3 | cost |
| C4 | Restraint: knowing when not to use a model | 20 | 2.5 | O2, O3 | restraint |
| C5 | Customer and squad partnership | 20 | none | O1 | none |

### C1 Outcome framing

Turns a request into a problem, a definition of good, non-goals and a line that says whether it worked.

- **1:** Describes features to build; no measure of whether they worked.
- **2:** Names a metric but not a target, a window or what it would trade off.
- **3:** States the problem, a definition of good with a target and window, and at least one non-goal.
- **4:** Does all of 3 and names the counter-metric that would show the win is false, and who decides at the line.

### C2 Eval design

Writes evals that would catch the failures that matter to a trades business before a customer does.

- **1:** Relies on trying a few prompts by hand; no written cases.
- **2:** Writes happy-path cases only, or cases with no pass rule.
- **3:** Writes cases for the main failure modes, each with a pass rule, and sets a pass line for release.
- **4:** Does all of 3, adds cases from real failure reports, and says how the suite would be kept honest as the model changes.

### C3 Cost judgment

Weighs tokens per task and price per token against the value of the task, and plans for growth.

- **1:** Does not consider cost, or treats it as engineering's problem.
- **2:** Mentions cost but cannot estimate it per task.
- **3:** Estimates cost per task as tokens per task and price per token, and compares it with the value of the task.
- **4:** Does all of 3 and names the cheaper path (smaller model, caching, no model) and the quality it would trade.

### C4 Restraint: knowing when not to use a model

Chooses rules, templates or a person over a model where those are cheaper, safer or more accurate.

- **1:** Proposes a model for every step, including arithmetic and legal wording.
- **2:** Accepts a non-model option only when prompted.
- **3:** Unprompted, keeps at least one step out of the model and says why (accuracy, cost or liability).
- **4:** Does all of 3 and sets the rule for when the step should move to a model later, with the evidence that would justify it.

### C5 Customer and squad partnership

Learns from trades customers directly and brings design and engineering into decisions early.

- **1:** Works from second-hand requests; hands specs over the wall.
- **2:** Talks to customers occasionally; involves the squad after the decision.
- **3:** Has a regular habit of customer contact and involves design and engineering in framing.
- **4:** Does all of 3 and can show a decision the customer contact or the squad changed.

## S1 Work sample: should drafted quotes auto-send? (90 minutes)

**Task.** Acme Assist drafts quotes for plumbers and electricians from a job note and a parts list. A large customer asks for drafts to send without review. You get 40 anonymised, illustrative job notes with the drafts the assistant produced and the quotes the trade sent. In 90 minutes, write a one-page recommendation: what you would ship, the eval cases that would gate it, the cost per drafted quote, and which steps should not use a model. Using Claude or any other tool is allowed and expected; say where you used it.

### W1 Eval cases and pass line (C2, tests evals)

- **1:** No eval cases, or only a note to test it.
- **2:** Cases cover the happy path only, or have no pass rule.
- **3:** Cases cover wrong parts prices, missing labour lines and wrong tax, each with a pass rule, and a pass line for release.
- **4:** Does all of 3 and builds cases from the job notes where the trade changed the draft, and says how often the suite is refreshed.

### W2 Cost per drafted quote (C3, tests cost)

- **1:** No cost estimate.
- **2:** A total monthly figure with no per-task basis.
- **3:** Cost per drafted quote as tokens per task and price per token, compared with the value of a quote sent sooner.
- **4:** Does all of 3 and shows the cheaper path and the quality it would cost, with the eval cases that would show it.

### W3 Steps kept out of the model (C4, tests restraint)

- **1:** The model computes totals, tax and terms.
- **2:** Keeps arithmetic out of the model only.
- **3:** Keeps arithmetic, tax and payment terms in code or templates, and says why for each.
- **4:** Does all of 3 and recommends against auto-send for now, with the evidence that would change that.

### W4 Recommendation framed as an outcome (C1)

- **1:** A feature list.
- **2:** A goal with no target or window.
- **3:** A definition of good with a target and window, and non-goals.
- **4:** Does all of 3, names the counter-metric (disputed quotes) and the line at which it would be rolled back, and says which of value, usability, feasibility and viability is the biggest risk and how to test it first.

## S2 Structured interview: product judgment (45 minutes)

Ask every question, in this order, to every candidate. Score each against its competency's anchors.

1. **Q1** (C1) Tell me about a launch you led that did not land. How did you know, and what did you change?
   - Follow-up: What was the measure, and when did you read it?
   - Follow-up: What did you stop doing?
2. **Q2** (C1) A sales leader asks for the assistant to chase every overdue invoice daily. How do you decide what good looks like?
   - Follow-up: What would you not build?
3. **Q3** (C5) Describe the last time a customer conversation changed what you shipped.
   - Follow-up: How often do you talk to customers now?
4. **Q4** (C5) Tell me about a decision where an engineer or designer disagreed with you. What happened?
   - Follow-up: Would you decide the same way again?

## S3 Structured interview: judgment in AI use (45 minutes)

Ask every question, in this order, to every candidate. Score each against its competency's anchors.

1. **Q5** (C2) Walk me through an eval suite you wrote or owned. What failure did it catch that a demo would have missed?
   - Follow-up: How did you set the pass line?
2. **Q6** (C3) The assistant's monthly model bill doubles while usage grows by half. What do you look at first?
   - Follow-up: What would you trade to bring it down?
3. **Q7** (C4) Tell me about a time you decided not to use a model for something a model could do.
   - Follow-up: What would have had to be true to use one?
4. **Q8** (C4) Invoice chasing emails go to a trade's own customers. Which parts would you let a model write, and which not?
   - Follow-up: Who signs off the wording?

## S4 Structured interview: working with the squad (30 minutes)

Ask every question, in this order, to every candidate. Score each against its competency's anchors.

1. **Q9** (C5) How do you bring design and engineering into a problem before there is a spec?
   - Follow-up: Give a recent example.
2. **Q10** (C1) How do you report to leadership whether something you shipped worked?
   - Follow-up: What do you do when the answer is that it did not?

## Calibration

Bar: 3.0 on a 1 to 4 scale. Panel: at least 3 interviewers. Spread flag: 2 points.

1. Each interviewer records every score, with written evidence, before the debrief starts. Scores recorded after it starts do not count.
2. Interviewers do not see each other's scores or discuss the candidate until the debrief starts.
3. The facilitator runs run.py score and shares the packet. Nobody states a view first.
4. For each flagged competency, the interviewers read their evidence aloud, lowest score first, and compare it with the anchors.
5. Scores do not change in the debrief. If an interviewer finds they misread an anchor, the decision note says so.
6. The hiring manager decides against the band and the evidence, and writes the decision note; check-note checks it before it is sent.
