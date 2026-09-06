# FMEA & Control Plan — Working Method

A portable reference for running PFMEAs and control plans. Contains methodology only:
no company, program, product, supplier, or process data. Safe to paste into a work
assistant, a project instruction file, or a team wiki.

---

## 1. The core idea

Process Flow → FMEA → Control Plan is **one chain, three views of the same row.**

| View | Question it answers |
|---|---|
| Process flow | What are the steps? |
| FMEA | How does each step fail, how bad, how likely, will we catch it? |
| Control plan | What do we check, to what spec, how often, and what do we do when it fails? |

Every step in the flow becomes a row in the FMEA. Every failure mode that ranks high
enough generates a control that lands in the control plan.

**The traceability test — run this before anyone else does:**
- A control in the plan that no FMEA row justifies → where did it come from?
- A high-ranked failure mode with no matching control → the chain is broken.

Most audit findings are here, not in the arithmetic.

---

## 2. Writing rows that hold up

### Function
What the step must accomplish, stated as a requirement. Not the equipment name.

### Failure mode
How the function is not met. This is where most weak FMEAs die.

- **Not** a part name: "bad axle," "cheap sensor"
- **Not** a purchase decision: "we bought the low bidder"
- **Yes** a mechanism: "joint loses clamp load," "fastener under-torqued,"
  "seal extrudes under pressure"

If a row can be fixed by "buy a better one," it isn't a failure mode yet. Keep asking
*how* until you reach something physical.

### Effect and severity

**Rank the worst credible outcome, not the outcome you happened to get.**

This is the single most common error carried in from hands-on experience. If a failure
happened once and nothing bad came of it, that was luck. Luck is not a control. Ask what
that same failure does at the worst moment in the cycle, then rank that.

Severity scale anchors:
- **9–10** — safety consequence, regulatory noncompliance, or harm to a person
- **7–8** — loss of primary function; the unit stops, gets scrapped, or a line goes down
- **4–6** — degraded function, rework, customer-visible defect
- **1–3** — minor, cosmetic, or noticed only internally

Severity is a property of the effect. **It does not change because you added an
inspection.** Only a design change that alters the consequence lowers it.

### Cause
The mechanism that produces the failure mode. One row per cause — if two causes need
two different fixes, they are two rows. A row with a vague cause produces a vague action.

### Prevention vs. detection controls

- **Prevention** acts on occurrence. Design change, poka-yoke, spec change, tooling.
- **Detection** acts on detection only. Inspection, gauging, test, audit.

Prevention beats detection every time. Detection tells you the failure already happened.

---

## 3. Scoring — RPN with two rules

### Baseline
**RPN = Severity × Occurrence × Detection.** Action threshold: **RPN ≥ 100.**

RPN is what most teams and suppliers speak, and it sorts a long list acceptably fast.
It has two known holes. Patch them with explicit rules rather than judgment calls.

### Rule 1 — Severity gate

> Any severity 9 or 10 gets an action regardless of RPN.

Multiplication lets a low factor cancel a high one. Severity 10 × occurrence 2 ×
detection 2 = RPN 40 and reads as trivial — but the effect is still a safety event.
The gate stops that.

### Rule 2 — Detection never closes a row

> Only a reduction in severity or occurrence closes an action. A detection improvement
> is logged, and the row stays open.

Improving detection from 8 to 3 cuts RPN by more than half while changing nothing about
the process. The failure is exactly as likely and exactly as bad — you just got better at
watching it happen. Closing actions this way is a classic audit finding and it hollows out
the document.

### Why these two rules exist

AIAG-VDA 2019 removed RPN and replaced it with **Action Priority (AP)** — a lookup table
returning High / Medium / Low instead of a product. In the table, severity dominates and
detection cannot rescue a high-severity, high-occurrence row. The two rules above reproduce
AP's protection while keeping RPN's familiar language.

**Know both.** Any supplier operating under IATF 16949 is likely working to AIAG-VDA and
will send AP-scored FMEAs. Read theirs in AP; run yours however your customer requirement
specifies.

### Which standard requires what

- **ISO 9001** — requires that risk be addressed (cl. 6.1). Names no method. FMEA is not mandatory.
- **IATF 16949** — requires FMEA and binds it to customer-specific requirements.
- The obligation to use AP arrives through **customer-specific requirements**, not through
  the standard text. Check the applicable CSR before choosing a format for anything audited.

---

## 4. Control plan columns

For every failure mode that clears the threshold or the severity gate:

| Column | Content |
|---|---|
| Characteristic | The thing measured. Flag safety/regulatory ones as special characteristics. |
| Specification | The number and tolerance. Cite the source. Never "per print" alone. |
| Method | How it is measured, with what, at what calibration state. |
| Sample size / frequency | 100%, n per lot, first-off/last-off, per shift. |
| Reaction plan | What the operator does *right now* when it fails, including containment of everything made since the last good check. |

**The reaction plan is the column that gets skipped and the column that matters.**
A control that detects a problem with no defined response is a record, not a control.
It must name: stop or continue, who is notified, what gets quarantined, and how far back.

**Make hard-to-verify things visually verifiable.** Where a characteristic is buried or
awkward to re-check — a fastened joint behind other assembly, a setting inside a guard —
convert it to a visual: witness/torque stripe across the joint, a marked indicator, a
tamper seal. This turns a teardown into a five-second look and makes 100% frequency
realistic instead of aspirational.

---

## 5. Common findings, in order of frequency

1. Control in the plan with no FMEA row behind it, or a high-risk row with no control
2. Actions closed by improving detection
3. Severity lowered because an inspection was added
4. Failure modes written as part names or purchasing decisions
5. Reaction plan missing, vague, or with no containment scope
6. Document not updated after a process change, deviation, or a real failure
7. Special characteristics not flagged consistently across flow, FMEA, and plan

---

## 6. Worked example — a fastened joint

Generic illustration of one row in all three views.

**Process step:** Torque fastener at a structural joint

**FMEA**
- Failure mode: joint loses clamp load
- Effect: micro-motion → fretting at the fastener holes → fatigue crack initiating away
  from the joint, presenting later as a component fracture. **Sev 9**
- Cause: incorrect torque value applied for the fastener size, or an out-of-calibration tool
- Prevention: torque value on the work instruction at the point of use; calibrated tool
  with enforced calibration interval
- Detection: witness mark across fastener and flange, plus independent verification
- Occurrence 4, Detection 4 → **RPN 144**, above threshold. Sev 9 also opens the gate.

**Control plan**
- Characteristic: fastener torque (special characteristic — safety)
- Specification: per engineering spec for the fastener size and joint
- Method: calibrated torque tool; witness stripe applied after torque
- Sample: 100%
- Reaction plan: re-torque; quarantine the unit; verify tool calibration; **contain every
  unit built with that tool since its last verified calibration**

Note the containment scope. If the tool was wrong, the defect is not confined to the unit
where it was found. That backward reach is what makes it a reaction plan rather than a note.

---

## 7. Quick prompts for a work assistant

- "Review this FMEA row: is the failure mode a mechanism or a part name?"
- "What's the worst credible effect of this failure mode, not the observed one?"
- "Does every row above RPN 100 or severity 9 have a matching control plan line?"
- "Does this control plan have any line with no FMEA row behind it?"
- "Is this action closed on a detection improvement? Flag it if so."
- "Is the reaction plan's containment scope defined — how far back does it reach?"
