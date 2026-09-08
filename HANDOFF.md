# 944 FMEA Tool — Project Handoff

Everything needed to rebuild, extend, and host the 944 track car FMEA / control plan tool.
Hand this whole file to Claude Code and it can work without any other context.

**Scope note:** this file is car-only. It contains no employer, product, supplier, or process
data and is safe to put in a public repo. Keep any work-facing method reference in a
separate, private location.

---

## 1. What this is

A small HTML tool that holds a Failure Mode and Effects Analysis and a matching
control plan for an LS-swapped Porsche 944 track car. Target: a 1:35 lap at Laguna Seca
with car and driver intact.

Relevant build facts:

- LS engine swap, Haltech Nexus Rebel-LS ECU (PN 220001446), Aeromotive fuel pressure regulator
- Dual master cylinder, hand-flared hard lines
- Not yet aligned; no tire selected
- Fuel pressure signal status is **unconfirmed, actively under investigation**: a wire
  heat-shrink labeled "FUEL PRESS" runs from the regulator area to a 3-pin connector,
  suggesting a sensor was wired in previously — but nobody has yet confirmed in the
  Haltech tuning software (NSP) that either of the Rebel-LS's 2 user-definable AVI
  (Analog Voltage Input) channels is actually assigned and reading a live value. Until
  that's confirmed, treat the row 7 cause text below ("no sensor fitted, or fitted but
  not wired") as still open — it may turn out to be a software/AVI-assignment gap
  rather than a wiring gap. No fuel level signal into the ECU either way.
- **Sep 5, 2026** — a Porsche Sprint Challenge USA West car (different team, not this
  car) lost brakes entering the Zanardi Corkscrew at Laguna Seca and crashed hard
  through the catch fence; driver hospitalized, reported awake and treated. Logged as
  supporting evidence on the brake flare-joint row (row 5) — see section 5.

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

There are **two parallel copies**, same data model and UI, different persistence:

| File | Hosted at | Persistence | Audience |
|---|---|---|---|
| `index.html` | GitHub Pages — `rdw775.github.io/944-fmea` | Browser `localStorage`, per device | Public — anyone with the link (Shane, etc.) |
| `artifact.html` | Claude Artifact — `claude.ai/code/artifact/23154a89-...` | Real shared backend (Claude `db` capability) | Private — org-internal only, signed-in viewers share one live dataset |

They must stay separate: `artifact.html` calls `claude.use("db")`, which does not exist
outside the Claude Artifact runtime, so it cannot be dropped onto GitHub Pages as-is.

### Views (nav bar)

1. **FMEA** — default. Ranked by RPN descending, numbered, or grouped by system. Rows
   expand to show effect, supporting evidence (if any), live S/O/D inputs, cause,
   prevention, detection, and the control plan block.
2. **Control plan** — AIAG-column table sorted by RPN. Special characteristics flagged.
   Missing specs and reaction plans called out in red.
3. **Pre-grid checklist** — generated from control plan rows, RPN order. Each item is a
   clickable pass/fail box; fail prompts for a note. **Save session** banks the run
   (with per-item notes) to the Session log.
4. **Session log** — every banked checklist run, most recent first, with pass/fail
   counts and per-item notes. Deletable. Exportable as JSON.
5. **Reference guide** — the methodology from section 2 above, built into the tool
   itself (core idea, row-writing rules, severity anchors, the two scoring rules and why
   they exist, how to justify a score change, common audit findings).

### Score-change workflow (the important behavioral change from the original design)

Editing S/O/D no longer auto-saves. Each edited row shows a **required "Reason for
change"** textarea. Nothing is logged until you hit the single, large, high-contrast
**Submit all changes** button at the bottom of the FMEA list — which validates that
*every* currently-dirty row has a reason filled in (naming which ones don't, if not),
then logs all of them in one action. Each accepted change appends an entry — timestamp,
old→new S/O/D, the reason — to that row's permanent **change history**, rendered inline
under the score inputs. This exists so score changes carry an audit trail of *why*, not
just *what changed to what*.

A confirmation message ("N changes submitted") shows after a successful submit and is
deliberately "sticky" for ~5 seconds — immune to the page's own re-renders or (in
`artifact.html`) the database's write-confirmation echo, both of which would otherwise
race it and overwrite it before it could be seen. A genuinely new edit clears it early.

### Supporting evidence

Rows can carry an `evidence` array — real-world incidents or precedents (date, text,
source URL) — rendered as a red-bordered block right after Effect, before the score
inputs, so a reviewer reads the evidence before deciding whether to change the score.
This is curated/added directly to the data (by whoever maintains the sheet), not a
viewer-facing form. See row 5 (brake flare joint) for the current example.

### Comment box

A bottom-of-page comment box ("Shane know's I'm a moron so input comments here" — keep
the title, it's a running joke, not a bug) for open feedback. In `artifact.html` this is
genuinely shared (everyone signed into the org sees the same comments, live); in
`index.html` it's per-browser only.

### `artifact.html`-specific behavior

- A **●Live / ○Offline** badge in the control bar shows whether `db` actually connected
  for this viewer. GitHub Pages has no equivalent — it never had a backend to be
  offline from.
- Falls back to the built-in default rows and disables all save actions (with a clear
  alert on any attempted save) if `db` is unavailable, rather than showing a blank page.
- Export buttons use the `downloads` capability (`window.claude.downloads.save`) — the
  artifact sandbox blocks the old `<a download>` blob-URL trick outright.
- The `state/rows` document, `sessions` collection, and `comments` collection make up
  the shared database. Query/seed them directly with the Artifact tool's `read_db` /
  `write_db` actions from a Claude Code session — never hardcode seed data into the
  page's own load logic.

### Other behaviors (both files)

- Severity gate turns the RPN badge red and opens an explanatory note.
- Detection-only improvements are flagged against `_synced` (the last-committed S/O/D)
  — a live warning, separate from the mandatory-reason requirement.
- Chain-check banner lists: rows needing action with no control, open severity gates,
  detection-only closes, and unranked rows.
- "Needs action only" filter shows rows at RPN >= 100 or severity >= 9.
- Print stylesheet expands all rows and hides controls.
- All three export buttons (rows / session log / comments) share a blue outline and a
  ⬇ icon — on a phone-width screen the toolbar wraps into ~9 near-identical buttons, and
  without a visual cue "Export JSON" reliably gets missed several rows down.
- Light theme forced (`color-scheme: light only`) because host dark mode made headers
  invisible against the card background.

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
  rx:     "...",          // control plan: reaction plan (must include containment scope)
  evidence: [              // optional — real-world precedents, curated not viewer-added
    { date: "YYYY-MM-DD", text: "...", url: "https://..." }
  ],
  history: [                // populated by the app once a score change is submitted
    { ts: 173..., reason: "...", from: {S,O,D}, to: {S,O,D} }
  ]
  // _synced: {S,O,D} is attached in-memory at runtime (last-committed baseline for the
  // dirty/detection-cheat checks) — never persisted; stripped before every save/write.
}
```

---

## 5. Current rows, ranked by RPN

| # | RPN | Sev | System | Failure mode | Control? | Notes |
|---|---|---|---|---|---|---|
| 1 | 432 | 9 | Fuel | Fuel pressure not monitored | yes | wiring status under active investigation, see §1 |
| 2 | 378 | 9 | Fuel | Pump uncovers | yes | |
| 3 | 360 | 10 | Engine | Oil pickup uncovered under sustained lateral G | yes | |
| 4 | 270 | 9 | Drivetrain | Rear CV joint loses internal geometry | yes | |
| 5 | 252 | 9 | Cooling | Coolant temperature climbs past limit and keeps climbing | yes | |
| 6 | 240 | 8 | Suspension | Suspension geometry not set to a defined spec | yes | |
| 7 | 180 | 9 | Drivetrain | Flange bolt joint loses clamp load | yes | |
| 8 | 160 | 10 | Brakes | Hard line flare joint leaks | yes | **has supporting evidence** — Sep 5 Laguna Seca crash |
| 9 | 140 | 7 | Suspension | Tire not selected | yes | |
| 10 | 108 | 9 | Drivetrain | Axle shaft fractures | yes | |
| 11 | — | — | Driver safety | Harness webbing or mounting degrades | **NO** | unranked, `todo: true` |

### Priority notes

- The brake flare leak ranks 8th by RPN but is **first by the severity gate** (Sev 10).
  This is rule 1 earning its keep - RPN alone would send you to fuel wiring while the car
  leaks brake fluid. It's now also the only row with a real-world precedent attached —
  a different car crashed from exactly this failure mode, at exactly this corner, four
  days before this doc was last updated.
- The top rows are mostly **absent information**, not broken parts: no confirmed pressure
  signal, no level signal, no alignment spec, no tire choice. Occurrence 10 on undefined
  items inflates RPN legitimately, and these collapse fast once closed out.
- Two rows are **blocked by other rows**: the alignment spec cannot be written until a
  tire is chosen; the fuel pressure sensor is worth little until a Haltech limit is
  configured.
- One row is unranked: driver restraints. Needs S/O/D.
- **None of these scores have actually been changed yet** through the Submit-all-changes
  workflow — every S/O/D value below still matches the original build-time estimate.

---

## 6. Full row data

Paste this into the tool's `ROWS` array, or load it as JSON. This is the live data as of
the last update to this file — pull a fresh copy from either `index.html`'s `ROWS` const
or (for `artifact.html`) via `read_db` on `state/rows` if you suspect it has drifted.

```json
[
  {
    "sys": "Drivetrain",
    "fn": "Transmit torque to the left rear wheel through suspension travel and steering-free articulation",
    "fm": "Rear CV joint loses internal geometry — balls brinell the races, cage cracks, joint will not reassemble",
    "eff": "Loss of drive. Joint can bind or separate; a separated shaft flails into brake lines, fuel lines or bodywork",
    "S": 9, "O": 6, "D": 5,
    "cause": "Operating angle at lowered ride height exceeds joint rating; grease overheats and sheds; unknown-supplier joint with no cert",
    "prev": "Known-brand joint of adequate rating. Measure static CV angle at ride height and compare to the joint's rated angle before install",
    "det": "Boot condition and grease colour checked each session — a split boot precedes the failure by a long margin",
    "ch": "CV boot integrity and grease condition",
    "spec": "Boot uncut and unsplit; grease light-coloured, not dark or gritty",
    "method": "Visual, wheel off or through the wheel",
    "samp": "100%, every session",
    "rx": "Split boot or dark gritty grease → do not grid. Pull the joint, inspect races for indentation, repack or replace"
  },
  {
    "sys": "Drivetrain",
    "fn": "Maintain clamp load at the axle-to-hub flange joint",
    "fm": "Flange bolt joint loses clamp load",
    "eff": "Micro-motion at the joint face → fretting at the bolt holes → fatigue crack that presents later as a 'snapped' shaft",
    "S": 9, "O": 5, "D": 4,
    "cause": "Joint separated at the flange instead of dropping the trailing arm, so it is opened and re-closed often. No re-torque interval, no thread retention, dirty joint faces",
    "prev": "New hardware or fresh threadlocker each assembly. Clean and dry both faces. Torque to spec with a calibrated wrench",
    "det": "Paint witness stripe across each bolt head onto the flange — a five-second visual on a joint you can't easily reach",
    "ch": "CV flange bolt torque",
    "spec": "Manufacturer torque spec for the flange hardware",
    "method": "Calibrated torque wrench at assembly; paint stripe check thereafter",
    "samp": "100% at assembly, visual every session",
    "rx": "Any broken stripe → pull the wheel, inspect the joint and bolt holes for fretting, replace hardware and re-torque before grid"
  },
  {
    "sys": "Drivetrain",
    "fn": "Carry peak driveline torque including transient shock loads",
    "fm": "Axle shaft fractures",
    "eff": "Immediate loss of drive; shaft end flails. Under power on corner exit this can take out a brake line or induce sudden yaw",
    "S": 9, "O": 4, "D": 3,
    "cause": "Shock loading — inside rear unloads over a curb and re-plants, wheel hop under trail braking — multiplies engine torque well past the 944's original ~217 hp design case",
    "prev": "Upgraded shaft rated for the LS torque case, or a deliberately chosen weak link you can replace cheaply",
    "det": "Fracture face reading after any failure: beach marks = fatigue, flat and crystalline = brittle overload, cup-and-cone with twist = ductile overload",
    "ch": "Shaft rating vs. applied torque case",
    "spec": "Shaft rated above peak shock load, not above peak flywheel torque",
    "method": "Documented at build; visual inspection for twist or surface damage at each corner service",
    "samp": "Every corner service",
    "rx": "Visible twist, galling or spline damage → replace both sides, keep the failed part and read the fracture face before binning it"
  },
  {
    "sys": "Engine",
    "fn": "Maintain oil pressure through sustained lateral load",
    "fm": "Oil pickup uncovered under sustained lateral G",
    "eff": "Bearing starvation → spun bearing → engine out and oil on track. At Laguna this is the Corkscrew and everyone behind you",
    "S": 10, "O": 6, "D": 6,
    "cause": "Stock LS pan baffling designed for straight-line duty. Turn 6 is a long sustained left; the Corkscrew unloads the car completely",
    "prev": "Baffled or kickout pan, windage tray, or accusump. This is a design control — fix it once, in the build",
    "det": "Logged oil pressure trace reviewed after every session. The dash light tells you the motor is already gone",
    "ch": "Oil level, cold, on level ground",
    "spec": "Your pan's measured full mark — not the factory dipstick",
    "method": "Dipstick plus review of last session's logged pressure trace",
    "samp": "100%, every session",
    "rx": "Any pressure dip in the trace → no-go. Do not grid until the cause is found"
  },
  {
    "sys": "Brakes",
    "fn": "Contain hydraulic pressure from the dual master to each corner without loss",
    "fm": "Hard line flare joint leaks — seat does not seal against the fitting",
    "eff": "Progressive fluid loss, then a long or bottomed pedal. Worst case is the end of the front straight into Turn 2, with a circuit already down and no reserve travel",
    "S": 10, "O": 8, "D": 2,
    "cause": "Flare profile does not match the seat. A 944's native lines are metric ISO/bubble flare; most US masters take SAE 45° inverted double flare. Mixing the two never seals at any torque. Second candidate: a single flare where a double is required — it cracks. Third: cheap clamp-style flaring tool producing off-centre or split flares",
    "prev": "Confirm the port standard on the master before cutting a single line, then flare to match. Double flare for SAE 45°, never single. Use a hydraulic or turret-style flaring tool, not a clamp-and-cone kit. Adapters where standards genuinely change, not a torque wrench",
    "det": "Pressure hold test with a pedal depressor and dry paper towel wrapped at each joint. Visual alone misses a weep",
    "ch": "Every flare joint — seal integrity under pressure (special characteristic — safety)",
    "spec": "Zero loss. Pedal holds firm under sustained load, no dampness at any joint",
    "method": "Pedal depressor at working pressure held 15+ minutes, paper towel witness at each fitting; reservoir level marked and re-checked",
    "samp": "100% of joints at build, every joint visually each session",
    "rx": "Any dampness → car does not move. Do not re-torque to chase a leak — an over-torqued seat is deformed permanently. Cut the flare off, verify the profile against the port, re-flare, re-test",
    "evidence": [
      {
        "date": "2026-09-05",
        "text": "Porsche Sprint Challenge USA West race at Laguna Seca — driver lost brakes entering the Zanardi Corkscrew, went airborne, cleared the tire pack, and tore through the catch fence into the trees. Front suspension separated from the chassis on impact; driver airlifted to hospital, reported awake and being treated. Not this car or team, but the exact failure mode and exact corner this row already flags at severity 10.",
        "url": "https://racingnews.co/2026/09/05/laguna-seca-driver-jumps-corkscrew-turn-lands-in-trees-video/"
      }
    ]
  },
  {
    "sys": "Cooling",
    "fn": "Reject enough heat to hold coolant and oil temperature over a full 20-minute session",
    "fm": "Coolant temperature climbs past limit and keeps climbing — no plateau",
    "eff": "Detonation, then head gasket or worse. On an untuned LS this arrives faster than on a stock engine, and the first sign may be damage rather than a gauge reading",
    "S": 9, "O": 7, "D": 4,
    "cause": "LS heat rejection exceeds what the 944 core and duct path were sized for. Usual mechanisms: air not actually passing through the core (recirculation around an unsealed shroud), trapped air from an incomplete fill on a system with high points, or fan control that never commands on at track duty cycle",
    "prev": "Seal the perimeter so air must pass through the core, not around it. Bleed to a documented procedure. Set fan-on threshold for track use, not street",
    "det": "Log coolant in and out plus oil temp for a full session. The number that matters is the delta across the radiator and whether temperature plateaus or keeps climbing",
    "ch": "Coolant temperature rise across a session, and delta across the radiator",
    "spec": "Temperature reaches a plateau and holds. A steady climb with no plateau fails regardless of the peak number",
    "method": "Logged inlet and outlet temps over a full 20-minute session at pace, reviewed after",
    "samp": "Every session until three consecutive sessions plateau, then every event",
    "rx": "No plateau → session over, cool down on track before pitting. Do not validate a cooling change on a short session — a system that fails at minute 18 passes a 6-minute test"
  },
  {
    "sys": "Fuel",
    "fn": "Report fuel pressure to the ECU so a drop can be acted on before damage",
    "fm": "Fuel pressure not monitored — no signal to the Haltech",
    "eff": "A pressure drop goes undetected. On an untuned LS that is lean-out under sustained load, detonation, and a melted piston. With nothing logged, the post-mortem cannot separate a fuel problem from a tune problem",
    "S": 9, "O": 6, "D": 8,
    "cause": "Pressure is read only on the mechanical gauge at the Aeromotive regulator. No sensor fitted, or fitted but not wired to an analog input",
    "prev": "The sensor alone is not the fix — configure a low-pressure safety cut in the Haltech so the ECU pulls timing or cuts before damage. That converts a detection-only control into real prevention",
    "det": "Logged pressure trace reviewed after every session. A mechanical gauge you cannot see at speed is barely a control, which is what the detection score reflects",
    "ch": "Fuel pressure, logged, across the full session",
    "spec": "Holds regulator target under sustained load; no dips under lateral G or braking",
    "method": "Pressure sensor on an ECU analog input, logged, with a configured low-pressure limit",
    "samp": "Continuous logging, reviewed 100% of sessions",
    "rx": "Any dip below limit → session over. Do not re-run until the cause is found — a repeat is a spun bearing away from an engine"
  },
  {
    "sys": "Fuel",
    "fn": "Deliver fuel without interruption under sustained lateral and braking load",
    "fm": "Pump uncovers — starvation with a low tank",
    "eff": "Momentary lean event under load. Same damage path as above, and it arrives at the worst possible moment because it takes sustained cornering to trigger",
    "S": 9, "O": 6, "D": 7,
    "cause": "No fuel level signal to the Haltech, so tank level is a guess. Stock pickup with no surge tank or baffle to keep the pump submerged under lateral load",
    "prev": "Surge tank or baffled pickup. Level sender wired to the ECU so remaining fuel is a number, not an estimate",
    "det": "Until a sender is fitted: fuel used per session logged by hand, with a hard minimum tank level rule",
    "ch": "Minimum tank level at grid",
    "spec": "Documented minimum — set above the level where the pickup uncovers under sustained G, not above empty",
    "method": "Measured fill and logged consumption per session; level sender once fitted",
    "samp": "100%, every session",
    "rx": "Below minimum → do not grid, add fuel. Never run a session down to reserve to save a splash of fuel"
  },
  {
    "sys": "Suspension",
    "fn": "Maintain intended tire contact patch and consistent handling balance through the corner",
    "fm": "Suspension geometry not set to a defined spec",
    "eff": "Unpredictable balance under load. On a car being learned at pace, a snap you did not expect is a wall, not just a slow lap",
    "S": 8, "O": 10, "D": 3,
    "cause": "Not aligned since the swap and suspension work. Underneath that: no target spec exists to align to, so 'aligned' has no definition yet",
    "prev": "Write a target sheet first — camber, toe, caster chosen for the tire and for Laguna. Set ride height before alignment or it gets done twice",
    "det": "Alignment measured on a rack at target ride height with driver weight or ballast in the seat",
    "ch": "Corner alignment — camber, toe, caster, and corner weights",
    "spec": "Documented target sheet. Not 'factory', not 'straight'",
    "method": "Alignment rack at target ride height, driver weight or ballast in seat",
    "samp": "After any suspension change, and after any off",
    "rx": "No defined spec → do not align yet, write the spec first. Out of spec → no track use until corrected"
  },
  {
    "sys": "Suspension",
    "fn": "Provide known, repeatable grip so the car and the driver can be developed against a baseline",
    "fm": "Tire not selected — grip level and target geometry both unknown",
    "eff": "No baseline. Every change gets evaluated against a moving reference, so nothing learned this season carries forward",
    "S": 7, "O": 10, "D": 2,
    "cause": "Tire choice not made. Camber target depends on tire construction more than on anything else, so the alignment spec cannot be written until this is settled",
    "prev": "Choose the tire before writing the alignment spec — this row blocks the row above it",
    "det": "Obvious on inspection; the detection score is low because nothing is hidden here",
    "ch": "Tire spec and pressures",
    "spec": "Selected compound and size, with hot pressure targets recorded",
    "method": "Documented at selection; hot pressures taken after each session",
    "samp": "Every session once running",
    "rx": "Wear pattern away from target → revisit camber before changing anything else"
  },
  {
    "sys": "Driver safety",
    "fn": "Restrain the driver in an impact",
    "fm": "Harness webbing or mounting degrades",
    "eff": "", "S": null, "O": null, "D": null,
    "cause": "", "prev": "", "det": "",
    "ch": "", "spec": "", "method": "", "samp": "", "rx": "",
    "todo": true
  }
]
```

---

## 7. Backlog

Roughly in order of value. Items struck through are done; kept for history.

1. ~~Persistence~~ — done. `index.html` uses `localStorage`; `artifact.html` uses the
   Claude `db` capability (real shared backend).
2. ~~Session log linking observed issues back to rows~~ — done (Pre-grid checklist →
   Session log).
3. ~~Revision history~~ — done, as row-level `history[]` with mandatory reasons, not just
   a changed-on date.
4. **Import JSON** to pair with the existing export — not built yet.
5. **Add/delete rows in the UI** — still source-only.
6. **Action tracking per row** — owner, due date, status. `history[]` records *that* a
   change happened and *why*; it doesn't yet track an open action through to closure
   against a specific person/date.
7. **Turn Occurrence into something informed by the session log automatically** —
   right now a fail in the checklist and a score change are two independent actions; a
   fail could suggest bumping Occurrence, but nothing does that math for you yet.
8. **Comments/evidence cross-linking** — the Sep 5 evidence entry on row 5 was added
   by hand via `write_db`/direct edit. There's no UI for a viewer to propose evidence;
   only whoever maintains the sheet can add it.
9. **Split the data** out of the HTML into a separate JSON file, per file, once hosting
   allows it for both variants.
10. **Mirror `artifact.html` features back to `index.html` (or vice versa) automatically**
    — right now every feature (Reference guide, mandatory reasons, evidence, export
    button styling) has to be hand-ported between the two files. They will drift if one
    is edited without the other.

---

## 8. Deployment

### GitHub Pages (`index.html`) — public, no sign-in

```bash
mkdir 944-fmea && cd 944-fmea
cp /path/to/index.html index.html
git init && git add . && git commit -m "944 FMEA and control plan"
gh repo create <user>/944-fmea --public --source=. --push
```

Then Settings -> Pages -> Deploy from a branch -> `main` / root.

Notes:
- Public repo Pages is free. Private repo Pages needs a paid plan; Cloudflare Pages
  hosts private for free.
- SharePoint does not work - it serves .html as a download and blocks custom scripts.
- This is the localStorage-only variant; nothing here syncs between viewers.

### Claude Artifact (`artifact.html`) — private, real shared backend

Publish via the Artifact tool with `capabilities: {db: {}, downloads: true}`. Then seed
`state/rows` once via `write_db` (never have the page seed itself on load — that's the
platform's own rule, not a style choice). Sharing is organization-internal only: every
reader/writer must be signed into the same Claude account/org as the owner. There is no
way to make this variant publicly viewable — that's what `index.html` is for.

Current live URL: `https://claude.ai/code/artifact/23154a89-5480-458a-8074-1a16b6c35672`

To inspect or fix the live data without opening the page: `read_db`/`write_db` against
collections `state` (doc `rows`), `sessions`, `comments`.

---

## 9. Working prompts

- "Add a row for <observed issue>. Ask me the one question that separates the likely causes."
- "Review row N: is the failure mode a mechanism or a part name?"
- "What is the worst credible effect of this failure mode, not the observed one?"
- "Does every row above RPN 100 or severity 9 have a matching control plan line?"
- "Is any reaction plan missing its containment scope?"
- "Add supporting evidence to row N citing <incident>, with a source link."
- "Query the artifact db and tell me if anyone's actually submitted anything since I last checked."
