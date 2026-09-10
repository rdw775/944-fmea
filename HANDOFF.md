# 944 PFMEA — Project Handoff

Everything needed to rebuild, extend, and host the 944 track car PFMEA / data log / build
task tool. Hand this whole file to Claude Code and it can work without any other context.

**Scope note:** this file is car-only. It contains no employer, product, supplier, or process
data and is safe to put in a public repo. Keep any work-facing method reference in a
separate, private location.

---

## 1. What this is

One HTML page — `index.html`, hosted on GitHub Pages — with three sections that share one
Google Sheet as their system of record:

- **PFMEA** — the failure-mode rows, control plan, pre-grid checklist, and a built-in
  reference guide for the methodology.
- **Data log** — every score change, every checklist run, every comment, read back from
  the Sheet.
- **Task list** — the winter build punch list: tasks auto-suggested from FMEA rows that
  imply build work, plus freeform tasks.

Target: a 1:35 lap at Laguna Seca with car and driver intact. The car is on jacks; realistic
track-ready date is spring 2027 at best, so this doubles as the build tracker.

Relevant build facts:

- LS engine swap, Haltech Nexus Rebel-LS ECU (PN 220001446), Aeromotive fuel pressure regulator
- Dual master cylinder, hand-flared hard lines
- Not yet aligned; no tire selected
- Fuel pressure signal status is **unconfirmed**: a sensor and a wire heat-shrink labeled
  "FUEL PRESS" exist at the regulator, but nobody has yet confirmed in the Haltech tuning
  software (NSP) that either of the Rebel-LS's two user-definable AVI channels is assigned
  and reading it. It may be a software/AVI-assignment gap rather than a wiring gap. This is
  the first suggested task on the Task list.
- No fuel level signal into the ECU.
- **Sep 5, 2026** — a Porsche Sprint Challenge USA West car (different team, not this car)
  lost brakes entering the Zanardi Corkscrew at Laguna Seca and crashed hard through the
  catch fence; driver hospitalized, reported awake and treated. Logged as supporting
  evidence on the brake flare-joint row.

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

## 3. Architecture

```
index.html on GitHub Pages (public, any device)
   │  GET  ?sheet=<tab>          → reads, on load and on demand
   │  POST {sheet, rows}         → appends, fire-and-forget (no-cors), then re-read
   ▼
Google Apps Script web app  (sheets/Code.gs)
   ▼
Google Sheet — four tabs, each tab's header row is its schema
   ▼  (planned: fmea-sync on the Raspberry Pi, every few minutes)
BigQuery dataset `fmea`, alongside the existing `trading` dataset
```

The page holds only the **static row text** (function, failure mode, effect, controls…).
Everything a person enters — scores, reasons, checklist runs, comments, tasks — is an
appended row in the Sheet. On every load the page rebuilds its state from that log:
scores = built-in defaults + replay of `ScoreChanges` in time order; tasks = latest event
per `taskId`; sessions = `Sessions` rows grouped by their shared `ts`.

**Offline behavior.** Each tab read is cached in `localStorage`; if the Sheet is
unreachable the page shows the last copy and the header badge goes amber. Submissions made
while offline go into an outbox and are flushed on the next successful load. The badge is
green (`● live`) only when the network actually answered.

**"Signed in as."** One remembered name field in the header. Every submission requires it
and stamps it into the row's `who`/`name` column. There is no auth — this is a trust-based
tool for a small group, and the Sheet is the audit trail.

### Sheet tabs (the schema)

| Tab | Columns | Written by |
|---|---|---|
| `ScoreChanges` | ts, rowIndex, failureMode, fromS, fromO, fromD, toS, toO, toD, reason, who | Submit all changes |
| `Sessions` | ts, sessionDate, sessionNote, sys, characteristic, status, itemNote, who | Save session (one row per checklist item; all items in a run share `ts`) |
| `Comments` | ts, name, text | Post comment |
| `BuildTasks` | ts, taskId, title, source, status, notes, who | Any task add / status cycle / notes edit (append-only event log; latest per `taskId` wins) |

`ts` is milliseconds since epoch, set by the page. Adding a new data type later is a new
tab with a header row — the script needs no change (`setup()` in `Code.gs` creates tabs
idempotently; edit `TABS` there to add one).

### Endpoint

`https://script.google.com/macros/s/AKfycbx3E0ELFl6unOhV7hJ1dYmYKZYyzDw44C1uidczkppt4iW5-8NHYtiM-dp6fY-JdStI/exec`

Deployed as *Execute as: Me, Who has access: Anyone*. The URL is unguessable but it is in
this public repo and in the page source, so anyone who finds it can append rows. The
script only ever appends — it cannot read other data or delete anything. A shared write
token checked in `doPost` is the planned hardening; deferred for now.

If `Code.gs` is edited: **Deploy → Manage deployments → edit → New version.** Saving alone
does not update the live URL.

---

## 4. Behaviors worth knowing

- **Score changes require a reason and a single submit.** Editing any S/O/D shows a required
  "Reason for change" box; nothing is logged until the large blue **Submit all changes**
  button at the bottom of the FMEA list is clicked. It validates every dirty row has a
  reason (naming the ones that don't), then logs them all in one POST. Each row's change
  history renders inline under its score inputs. The confirmation message is deliberately
  sticky for ~5 s so a re-render can't race it away.
- **Severity gate** turns the RPN badge red and opens an explanatory note; **detection-only
  reductions** are flagged live against the last-committed score; the **chain-check banner**
  lists rows needing action with no control, open gates, pending detection-only cuts, and
  unranked rows.
- **Supporting evidence** (`evidence[]` on a row: date, text, url) renders as a red-bordered
  block between Effect and the score inputs, so a reviewer reads the precedent before
  touching the score. Curated in the row data, not a viewer form.
- **Task list** cycles todo → doing → done on click; notes save on blur. "Suggested from the
  FMEA" lists rows with a `task` string that have no `BuildTasks` event yet; "Add" posts the
  first event. `SEED_TASKS` in the code holds standalone suggestions.
- **Export JSON** (FMEA view) downloads the derived state — rows plus all four logs — for
  offline use. Not needed for backup; the Sheet is the backup.
- Light theme forced (`color-scheme: light only`) because host dark mode made headers
  invisible against the card background.
- Two-level nav: three section buttons, then sub-tabs. Done because a flat toolbar wrapped
  into ~9 identical buttons on a phone and the export button was reliably missed.

---

## 5. Current rows, ranked by RPN

Scores below are the built-in defaults. **No score has been changed through the submit
workflow yet** — the `ScoreChanges` tab is empty as of this writing.

| # | RPN | Sev | System | Failure mode | Notes |
|---|---|---|---|---|---|
| 1 | 432 | 9 | Fuel | Fuel pressure not monitored | wiring vs. AVI-assignment status unconfirmed, see §1 |
| 2 | 378 | 9 | Fuel | Pump uncovers | |
| 3 | 360 | 10 | Engine | Oil pickup uncovered under sustained lateral G | |
| 4 | 270 | 9 | Drivetrain | Rear CV joint loses internal geometry | |
| 5 | 252 | 9 | Cooling | Coolant temperature climbs past limit and keeps climbing | |
| 6 | 240 | 8 | Suspension | Suspension geometry not set to a defined spec | |
| 7 | 180 | 9 | Drivetrain | Flange bolt joint loses clamp load | |
| 8 | 160 | 10 | Brakes | Hard line flare joint leaks | **has supporting evidence** — Sep 5 Laguna Seca crash |
| 9 | 140 | 7 | Suspension | Tire not selected | |
| 10 | 108 | 9 | Drivetrain | Axle shaft fractures | |
| 11 | — | — | Driver safety | Harness webbing or mounting degrades | unranked, `todo: true` |

### Priority notes

- The brake flare leak ranks 8th by RPN but is **first by the severity gate** (Sev 10) — and
  it's the only row with a real-world precedent attached: a different car crashed from
  exactly this failure mode, at exactly this corner, on Sep 5.
- The top rows are mostly **absent information**, not broken parts: no confirmed pressure
  signal, no level signal, no alignment spec, no tire choice. Occurrence 10 on undefined
  items inflates RPN legitimately, and these collapse fast once closed out.
- Two rows are **blocked by other rows**: the alignment spec can't be written until a tire
  is chosen; the fuel pressure sensor is worth little until a Haltech limit is configured.
- One row is unranked: driver restraints.

---

## 6. Row data

The static text lives in `index.html`'s `ROWS` const — that is the source of truth for it.
Each row: `sys, fn, fm, eff, S, O, D, cause, prev, det, ch, spec, method, samp, rx`, plus
optional `task` (string → auto-suggested build task), `evidence[]` ({date, text, url}),
and `todo: true` for a placeholder row. Scores are overwritten at runtime by the Sheet log.

---

## 7. Backlog

1. **`fmea-sync` on the Pi** — Node job in `trade-nerve-center`, same pattern as the
   scanners: pull each tab via `?sheet=`, dedupe on (`ts` + key), create the `fmea` BigQuery
   dataset and tables on first run with the Pi's existing key, insert new rows. Systemd
   service + timer; add to `DIR_TO_SERVICE` so `auto-deploy` restarts it. Permission granted;
   not built yet.
2. **Write token** on the Apps Script endpoint (see §3). Deferred by decision.
3. **Custom HTML trading dashboard** to replace Grafana — reads `alpaca-proxy`'s existing
   JSON endpoints; needs the Pi reachable off-LAN (Tailscale) since GitHub Pages is HTTPS
   and can't fetch plain-http LAN addresses. Separate track; not started.
4. **Import JSON** / add-delete rows in the UI — still source-only.
5. **Occurrence informed by the session log** — a checklist fail could suggest a score
   change; nothing does that math yet.
6. **Viewer-proposed evidence** — currently curated in row data only.

---

## 8. Deployment

**Page:** GitHub Pages from `main` / root of this repo. Push to `main`; live within ~1 min
at `https://rdw775.github.io/944-fmea/`. Pages caches for 10 min — hard-refresh (⌘⇧R)
if it looks stale.

**Backend:** `sheets/SETUP.md` (one-time, ~5 min, from the owner's Google account). The
Apps Script is `sheets/Code.gs`.

Retired: a Claude Artifact copy with a private per-org database, and a standalone comment
test page. Both removed; the artifact's database was empty when retired.

---

## 9. Working prompts

- "Add a row for <observed issue>. Ask me the one question that separates the likely causes."
- "Review row N: is the failure mode a mechanism or a part name?"
- "What is the worst credible effect of this failure mode, not the observed one?"
- "Does every row above RPN 100 or severity 9 have a matching control plan line?"
- "Is any reaction plan missing its containment scope?"
- "Add supporting evidence to row N citing <incident>, with a source link."
- "Read the Sheet and tell me what's been submitted since <date>."
