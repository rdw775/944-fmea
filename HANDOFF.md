# 944 FMEA Tool — Project Handoff

Everything needed to rebuild, extend, and host the 944 track car FMEA / control plan tool.
Hand this whole file to Claude Code in VS Code and it can work without any other context.

**Scope note:** this file is car-only. It contains no employer, product, supplier, or process
data and is safe to put in a public repo. Keep any work-facing method reference in a
separate, private location.

---

## 1. What this is

A single-file HTML tool that holds a Failure Mode and Effects Analysis and a matching
control plan for an LS-swapped Porsche 944 track car. Target: a 1:35 lap at Laguna Seca
with car and driver intact.

Relevant build facts:

- LS engine swap, Haltech ECU, Aeromotive fuel pressure regulator
- Dual master cylinder, hand-flared hard lines
- Not yet aligned; no tire selected
- No fuel pressure or fuel level signal into the ECU

---

## 2. Methodology the tool implements

Process Flow -> FMEA -> Control Plan is one chain, three views of the same row. Every
failure mode that clears the threshold generates a control. Every control traces back to
a failure mode. Breaks in that chain are the thing to detect.

### Scoring

**RPN = Severity x Occurrence x Detection.** Action threshold: **RPN >= 100.**

RPN is used because it is the language most teams and suppliers speak. It has two known
holes, patched with explicit rules rather than judgment:

**Rule 1 - severity gate.** Any severity 9 or 10 gets an action regardless of RPN.
Multiplication hides these: severity 10 x occurrence 2 x detection 2 = RPN 40 reads as
trivial but the effect is still a safety event.

**Rule 2 - detection never closes a row.** Only a reduction in severity or occurrence
closes an action. Improving detection from 8 to 3 halves RPN while changing nothing about
the process - the failure is exactly as likely and exactly as bad.

### Action Priority

AIAG-VDA 2019 replaced RPN with Action Priority (H/M/L), a lookup where severity dominates
and detection cannot rescue a high-severity, high-occurrence row. The tool shows AP small
under each RPN for reference. The two rules above reproduce AP's protection in RPN's
language.

The AP function in the code is a **simplified** form of the published table. Do not treat
it as authoritative for anything audited.

### Severity anchors

| Score | Effect |
|---|---|
| 10 | Safety consequence without warning |
| 9 | Safety consequence with warning |
| 7-8 | Loss of primary function - DNF |
| 4-6 | Degraded function - costs lap time |
| 1-3 | Minor or annoying |

Severity is a property of the effect. It does not change because an inspection was added.

### Row-writing rules

- Failure mode is a **mechanism**, never a part name or a purchase decision.
  Not "cheap eBay axle" - that is a purchasing decision. Yes "joint loses clamp load".
- Effect is the **worst credible outcome**, not the one that happened. Luck is not a control.
- Prevention acts on occurrence; detection acts on detection only. Prevention wins.
- Reaction plan must define containment scope - how far back the suspect population reaches.
- Where a characteristic is hard to re-check, convert it to a visual (witness/torque stripe).

---

## 3. Current state of the tool

Single file, no build step, no dependencies. Fonts load from Google Fonts with system
fallbacks. No localStorage (artifact sandbox restriction - see backlog).

### Views

1. **FMEA** - default. Flat list ranked by RPN descending, numbered. Toggle to group by
   system. Rows expand to show effect, live S/O/D inputs, cause, prevention, detection,
   and the control plan block.
2. **Control plan** - AIAG-column table sorted by RPN. Special characteristics flagged.
   Missing specs and reaction plans called out in red.
3. **Pre-grid checklist** - generated from control plan rows, RPN order, printable.

### Behaviours

- S/O/D inputs recompute RPN, AP, and rank live
- Severity gate turns the RPN badge red and opens an explanatory note
- Detection-only improvements are detected against a baseline captured at load and flagged
- Chain-check banner lists: rows needing action with no control, open severity gates,
  detection-only closes, and unranked rows
- "Needs action only" filter shows rows at RPN >= 100 or severity >= 9
- Print stylesheet expands all rows and hides controls
- Export JSON dumps the row array
- Light theme forced (`color-scheme: light only`) because host dark mode made headers
  invisible against the card background

---

## 4. Data model

```js
{
  sys:    "Drivetrain",   // system grouping
  fn:     "...",          // function - what the step must accomplish
  fm:     "...",          // failure mode - mechanism
  eff:    "...",          // effect - worst credible outcome
  S: 9, O: 6, D: 5,       // severity, occurrence, detection (1-10, null if unranked)
  cause:  "...",          // mechanism producing the failure mode
  prev:   "...",          // prevention control (acts on occurrence)
  det:    "...",          // detection control
  ch:     "...",          // control plan: characteristic
  spec:   "...",          // control plan: specification
  method: "...",          // control plan: measurement method
  samp:   "...",          // control plan: sample size / frequency
  rx:     "..."           // control plan: reaction plan (must include containment scope)
}
```

---

## 5. Current rows, ranked by RPN

| # | RPN | Sev | System | Failure mode | Control? |
|---|---|---|---|---|---|
| 1 | 432 | 9 | Fuel | Fuel pressure not monitored | yes |
| 2 | 378 | 9 | Fuel | Pump uncovers | yes |
| 3 | 360 | 10 | Engine | Oil pickup uncovered under sustained lateral G | yes |
| 4 | 270 | 9 | Drivetrain | Rear CV joint loses internal geometry | yes |
| 5 | 252 | 9 | Cooling | Coolant temperature climbs past limit and keeps climbing | yes |
| 6 | 240 | 8 | Suspension | Suspension geometry not set to a defined spec | yes |
| 7 | 180 | 9 | Drivetrain | Flange bolt joint loses clamp load | yes |
| 8 | 160 | 10 | Brakes | Hard line flare joint leaks | yes |
| 9 | 140 | 7 | Suspension | Tire not selected | yes |
| 10 | 108 | 9 | Drivetrain | Axle shaft fractures | yes |
| 11 | — | — | Driver safety | Harness webbing or mounting degrades | **NO** |

### Priority notes

- The brake flare leak ranks 8th by RPN but is **first by the severity gate** (Sev 10).
  This is rule 1 earning its keep - RPN alone would send you to fuel wiring while the car
  leaks brake fluid.
- The top rows are mostly **absent information**, not broken parts: no pressure signal,
  no level signal, no alignment spec, no tire choice. Occurrence 10 on undefined items
  inflates RPN legitimately, and these collapse fast once closed out.
- Two rows are **blocked by other rows**: the alignment spec cannot be written until a
  tire is chosen; the fuel pressure sensor is worth little until a Haltech limit is
  configured.
- One row is unranked: driver restraints. Needs S/O/D.

---

## 6. Full row data

Paste this into the tool's `ROWS` array, or load it as JSON.

```json
[
  {
    "sys": "Drivetrain",
    "fn": "Transmit torque to the left rear wheel through suspension travel and steering-free articulation",
    "fm": "Rear CV joint loses internal geometry \u2014 balls brinell the races, cage cracks, joint will not reassemble",
    "eff": "Loss of drive. Joint can bind or separate; a separated shaft flails into brake lines, fuel lines or bodywork",
    "S": 9,
    "cause": "Operating angle at lowered ride height exceeds joint rating; grease overheats and sheds; unknown-supplier joint with no cert",
    "O": 6,
    "D": 5,
    "prev": "Known-brand joint of adequate rating. Measure static CV angle at ride height and compare to the joint's rated angle before install",
    "det": "Boot condition and grease colour checked each session \u2014 a split boot precedes the failure by a long margin",
    "ch": "CV boot integrity and grease condition",
    "spec": "Boot uncut and unsplit; grease light-coloured, not dark or gritty",
    "method": "Visual, wheel off or through the wheel",
    "samp": "100%, every session",
    "rx": "Split boot or dark gritty grease \u2192 do not grid. Pull the joint, inspect races for indentation, repack or replace"
  },
  {
    "sys": "Drivetrain",
    "fn": "Maintain clamp load at the axle-to-hub flange joint",
    "fm": "Flange bolt joint loses clamp load",
    "eff": "Micro-motion at the joint face \u2192 fretting at the bolt holes \u2192 fatigue crack that presents later as a 'snapped' shaft",
    "S": 9,
    "cause": "Joint separated at the flange instead of dropping the trailing arm, so it is opened and re-closed often. No re-torque interval, no thread retention, dirty joint faces",
    "O": 5,
    "D": 4,
    "prev": "New hardware or fresh threadlocker each assembly. Clean and dry both faces. Torque to spec with a calibrated wrench",
    "det": "Paint witness stripe across each bolt head onto the flange \u2014 a five-second visual on a joint you can't easily reach",
    "ch": "CV flange bolt torque",
    "spec": "Manufacturer torque spec for the flange hardware",
    "method": "Calibrated torque wrench at assembly; paint stripe check thereafter",
    "samp": "100% at assembly, visual every session",
    "rx": "Any broken stripe \u2192 pull the wheel, inspect the joint and bolt holes for fretting, replace hardware and re-torque before grid"
  },
  {
    "sys": "Drivetrain",
    "fn": "Carry peak driveline torque including transient shock loads",
    "fm": "Axle shaft fractures",
    "eff": "Immediate loss of drive; shaft end flails. Under power on corner exit this can take out a brake line or induce sudden yaw",
    "S": 9,
    "cause": "Shock loading \u2014 inside rear unloads over a curb and re-plants, wheel hop under trail braking \u2014 multiplies engine torque well past the 944's original ~217 hp design case",
    "O": 4,
    "D": 3,
    "prev": "Upgraded shaft rated for the LS torque case, or a deliberately chosen weak link you can replace cheaply",
    "det": "Fracture face reading after any failure: beach marks = fatigue, flat and crystalline = brittle overload, cup-and-cone with twist = ductile overload",
    "ch": "Shaft rating vs. applied torque case",
    "spec": "Shaft rated above peak shock load, not above peak flywheel torque",
    "method": "Documented at build; visual inspection for twist or surface damage at each corner service",
    "samp": "Every corner service",
    "rx": "Visible twist, galling or spline damage \u2192 replace both sides, keep the failed part and read the fracture face before binning it"
  },
  {
    "sys": "Engine",
    "fn": "Maintain oil pressure through sustained lateral load",
    "fm": "Oil pickup uncovered under sustained lateral G",
    "eff": "Bearing starvation \u2192 spun bearing \u2192 engine out and oil on track. At Laguna this is the Corkscrew and everyone behind you",
    "S": 10,
    "cause": "Stock LS pan baffling designed for straight-line duty. Turn 6 is a long sustained left; the Corkscrew unloads the car completely",
    "O": 6,
    "D": 6,
    "prev": "Baffled or kickout pan, windage tray, or accusump. This is a design control \u2014 fix it once, in the build",
    "det": "Logged oil pressure trace reviewed after every session. The dash light tells you the motor is already gone",
    "ch": "Oil level, cold, on level ground",
    "spec": "Your pan's measured full mark \u2014 not the factory dipstick",
    "method": "Dipstick plus review of last session's logged pressure trace",
    "samp": "100%, every session",
    "rx": "Any pressure dip in the trace \u2192 no-go. Do not grid until the cause is found"
  },
  {
    "sys": "Brakes",
    "fn": "Contain hydraulic pressure from the dual master to each corner without loss",
    "fm": "Hard line flare joint leaks \u2014 seat does not seal against the fitting",
    "eff": "Progressive fluid loss, then a long or bottomed pedal. Worst case is the end of the front straight into Turn 2, with a circuit already down and no reserve travel",
    "S": 10,
    "cause": "Flare profile does not match the seat. A 944's native lines are metric ISO/bubble flare; most US masters take SAE 45\u00b0 inverted double flare. Mixing the two never seals at any torque. Second candidate: a single flare where a double is required \u2014 it cracks. Third: cheap clamp-style flaring tool producing off-centre or split flares",
    "O": 8,
    "D": 2,
    "prev": "Confirm the port standard on the master before cutting a single line, then flare to match. Double flare for SAE 45\u00b0, never single. Use a hydraulic or turret-style flaring tool, not a clamp-and-cone kit. Adapters where standards genuinely change, not a torque wrench",
    "det": "Pressure hold test with a pedal depressor and dry paper towel wrapped at each joint. Visual alone misses a weep",
    "ch": "Every flare joint \u2014 seal integrity under pressure (special characteristic \u2014 safety)",
    "spec": "Zero loss. Pedal holds firm under sustained load, no dampness at any joint",
    "method": "Pedal depressor at working pressure held 15+ minutes, paper towel witness at each fitting; reservoir level marked and re-checked",
    "samp": "100% of joints at build, every joint visually each session",
    "rx": "Any dampness \u2192 car does not move. Do not re-torque to chase a leak \u2014 an over-torqued seat is deformed permanently. Cut the flare off, verify the profile against the port, re-flare, re-test"
  },
  {
    "sys": "Cooling",
    "fn": "Reject enough heat to hold coolant and oil temperature over a full 20-minute session",
    "fm": "Coolant temperature climbs past limit and keeps climbing \u2014 no plateau",
    "eff": "Detonation, then head gasket or worse. On an untuned LS this arrives faster than on a stock engine, and the first sign may be damage rather than a gauge reading",
    "S": 9,
    "cause": "LS heat rejection exceeds what the 944 core and duct path were sized for. Usual mechanisms: air not actually passing through the core (recirculation around an unsealed shroud), trapped air from an incomplete fill on a system with high points, or fan control that never commands on at track duty cycle",
    "O": 7,
    "D": 4,
    "prev": "Seal the perimeter so air must pass through the core, not around it. Bleed to a documented procedure. Set fan-on threshold for track use, not street",
    "det": "Log coolant in and out plus oil temp for a full session. The number that matters is the delta across the radiator and whether temperature plateaus or keeps climbing",
    "ch": "Coolant temperature rise across a session, and delta across the radiator",
    "spec": "Temperature reaches a plateau and holds. A steady climb with no plateau fails regardless of the peak number",
    "method": "Logged inlet and outlet temps over a full 20-minute session at pace, reviewed after",
    "samp": "Every session until three consecutive sessions plateau, then every event",
    "rx": "No plateau \u2192 session over, cool down on track before pitting. Do not validate a cooling change on a short session \u2014 a system that fails at minute 18 passes a 6-minute test"
  },
  {
    "sys": "Fuel",
    "fn": "Report fuel pressure to the ECU so a drop can be acted on before damage",
    "fm": "Fuel pressure not monitored \u2014 no signal to the Haltech",
    "eff": "A pressure drop goes undetected. On an untuned LS that is lean-out under sustained load, detonation, and a melted piston. With nothing logged, the post-mortem cannot separate a fuel problem from a tune problem",
    "S": 9,
    "O": 6,
    "D": 8,
    "cause": "Pressure is read only on the mechanical gauge at the Aeromotive regulator. No sensor fitted, or fitted but not wired to an analog input",
    "prev": "The sensor alone is not the fix \u2014 configure a low-pressure safety cut in the Haltech so the ECU pulls timing or cuts before damage. That converts a detection-only control into real prevention",
    "det": "Logged pressure trace reviewed after every session. A mechanical gauge you cannot see at speed is barely a control, which is what the detection score reflects",
    "ch": "Fuel pressure, logged, across the full session",
    "spec": "Holds regulator target under sustained load; no dips under lateral G or braking",
    "method": "Pressure sensor on an ECU analog input, logged, with a configured low-pressure limit",
    "samp": "Continuous logging, reviewed 100% of sessions",
    "rx": "Any dip below limit \u2192 session over. Do not re-run until the cause is found \u2014 a repeat is a spun bearing away from an engine"
  },
  {
    "sys": "Fuel",
    "fn": "Deliver fuel without interruption under sustained lateral and braking load",
    "fm": "Pump uncovers \u2014 starvation with a low tank",
    "eff": "Momentary lean event under load. Same damage path as above, and it arrives at the worst possible moment because it takes sustained cornering to trigger",
    "S": 9,
    "O": 6,
    "D": 7,
    "cause": "No fuel level signal to the Haltech, so tank level is a guess. Stock pickup with no surge tank or baffle to keep the pump submerged under lateral load",
    "prev": "Surge tank or baffled pickup. Level sender wired to the ECU so remaining fuel is a number, not an estimate",
    "det": "Until a sender is fitted: fuel used per session logged by hand, with a hard minimum tank level rule",
    "ch": "Minimum tank level at grid",
    "spec": "Documented minimum \u2014 set above the level where the pickup uncovers under sustained G, not above empty",
    "method": "Measured fill and logged consumption per session; level sender once fitted",
    "samp": "100%, every session",
    "rx": "Below minimum \u2192 do not grid, add fuel. Never run a session down to reserve to save a splash of fuel"
  },
  {
    "sys": "Suspension",
    "fn": "Maintain intended tire contact patch and consistent handling balance through the corner",
    "fm": "Suspension geometry not set to a defined spec",
    "eff": "Unpredictable balance under load. On a car being learned at pace, a snap you did not expect is a wall, not just a slow lap",
    "S": 8,
    "O": 10,
    "D": 3,
    "cause": "Not aligned since the swap and suspension work. Underneath that: no target spec exists to align to, so 'aligned' has no definition yet",
    "prev": "Write a target sheet first \u2014 camber, toe, caster chosen for the tire and for Laguna. Set ride height before alignment or it gets done twice",
    "det": "Alignment measured on a rack at target ride height with driver weight or ballast in the seat",
    "ch": "Corner alignment \u2014 camber, toe, caster, and corner weights",
    "spec": "Documented target sheet. Not 'factory', not 'straight'",
    "method": "Alignment rack at target ride height, driver weight or ballast in seat",
    "samp": "After any suspension change, and after any off",
    "rx": "No defined spec \u2192 do not align yet, write the spec first. Out of spec \u2192 no track use until corrected"
  },
  {
    "sys": "Suspension",
    "fn": "Provide known, repeatable grip so the car and the driver can be developed against a baseline",
    "fm": "Tire not selected \u2014 grip level and target geometry both unknown",
    "eff": "No baseline. Every change gets evaluated against a moving reference, so nothing learned this season carries forward",
    "S": 7,
    "O": 10,
    "D": 2,
    "cause": "Tire choice not made. Camber target depends on tire construction more than on anything else, so the alignment spec cannot be written until this is settled",
    "prev": "Choose the tire before writing the alignment spec \u2014 this row blocks the row above it",
    "det": "Obvious on inspection; the detection score is low because nothing is hidden here",
    "ch": "Tire spec and pressures",
    "spec": "Selected compound and size, with hot pressure targets recorded",
    "method": "Documented at selection; hot pressures taken after each session",
    "samp": "Every session once running",
    "rx": "Wear pattern away from target \u2192 revisit camber before changing anything else"
  },
  {
    "sys": "Driver safety",
    "fn": "Restrain the driver in an impact",
    "fm": "Harness webbing or mounting degrades",
    "eff": "",
    "S": null,
    "O": null,
    "D": null,
    "cause": "",
    "prev": "",
    "det": "",
    "ch": "",
    "spec": "",
    "method": "",
    "samp": "",
    "rx": ""
  }
]
```

---

## 7. Backlog

Roughly in order of value.

1. **Persistence.** localStorage was omitted because artifact sandboxes block it. Once
   self-hosted this works - save the `ROWS` array on every change, restore on load, with
   an explicit reset. This is the single biggest usability gap.
2. **Add / edit / delete rows in the UI.** Currently rows are only editable in source.
3. **Import JSON** to pair with the existing export.
4. **Action tracking per row** - owner, due date, status, and evidence of what actually
   changed. Rule 2 says only S or O reductions close a row; the tool flags violations but
   does not yet track closure.
5. **Revision history** - FMEAs are living documents; a changed-on date per row matters
   for showing the document was updated after a real failure.
6. **Session log** linking observed issues back to rows, so occurrence scores are informed
   by events rather than guesses.
7. **Split the data** out of the HTML into a separate JSON file once hosting allows it.

---

## 8. Deployment

Public GitHub Pages:

```bash
mkdir 944-fmea && cd 944-fmea
cp /path/to/944-fmea.html index.html
git init && git add . && git commit -m "944 FMEA and control plan"
gh repo create <user>/944-fmea --public --source=. --push
```

Then Settings -> Pages -> Deploy from a branch -> `main` / root.

Notes:
- Public repo Pages is free. Private repo Pages needs a paid plan; Cloudflare Pages
  hosts private for free.
- SharePoint does not work - it serves .html as a download and blocks custom scripts.
- Self-hosting is also what unlocks localStorage (backlog item 1).

---

## 9. Working prompts

- "Add a row for <observed issue>. Ask me the one question that separates the likely causes."
- "Review row N: is the failure mode a mechanism or a part name?"
- "What is the worst credible effect of this failure mode, not the observed one?"
- "Does every row above RPN 100 or severity 9 have a matching control plan line?"
- "Is any reaction plan missing its containment scope?"
- "Add localStorage persistence with an explicit reset control."
