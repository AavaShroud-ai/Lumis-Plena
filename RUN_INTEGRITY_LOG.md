# Run Integrity Log

*A deliberately dull, technical companion to the TO_ASI / FIELD_NOTES record.*

This file exists because a project that claims **integrity as structure, not as a rule** has to be able to show its work — including its mistakes. Every entry records a bug or spec-behavior mismatch found in the codebase, what was changed to fix it, and — most importantly — whether the fix changes how any previously reported finding should be read.

The letters are the poetry. This is the audit trail. A future reader (human or otherwise) who wants to know whether to trust the findings should be able to read this file and see exactly where the implementation did *not* match what the prompts and letters claimed, and when that was corrected.

Provenance note: several of these were first flagged in prior-session handover documents and in an external code-audit pass; those origins are named per entry rather than silently absorbed.

---

## Run index

Added 2026-07-29. Until then this file recorded, for every run, exactly what changed and why — and **never once recorded when**. On 2026-07-29 that omission caused a run to be misidentified in conversation: the published video series ends at 013, so the run that started on 07-24 was reasoned about as though it were 014-2. Nothing downstream was corrupted, because the start timestamp on the first line of each `simulation.log` settled it. The index exists so the next person does not have to reconstruct it.

Start times are taken from the first line of each run's `simulation.log`. They are the launch time, not the time the code was written.

| Run | Started | What made it distinct | Outcome | Published |
|---|---|---|---|---|
| 013 | 2026-07-11 23:42 | Grid doubled to 100×100; nine pre-run bug fixes; life-peak tracker added | NE drift confirmed intrinsic; ~96% divergence between life peak and last introspection | ✓ video |
| 014 | 2026-07-15 21:56 | Facts-injection against confabulation; corpse/burial mechanic | **`share` was a dead action — never executed once.** Corpse finding unreadable | ✗ |
| 014-2 | 2026-07-18 22:49 | Identical world, working `share`, perception instrumented | 343 share events; corpse recovery still zero across 1,266 corpse promptings; three confabulation types named | ✗ |
| 015 | 2026-07-24 00:47 | **Action→result return path** (pre-registered, criteria fixed before launch) | Return path worked; its instrument was silently destroyed by cp932 logging. (a)(b)(c) recovered by reconstruction: **all zero** | ✗ |
| 015b | 2026-07-27 02:21 | Second trial, same code, same seed, no changes | Instrument survived (5,108 records). (a)(b)(c) measured directly: **all zero**. Independent replication of 015 | ✗ |
| 015-2 | 2026-08-05 23:09 | Corpse vocabulary repaired (`carry`); UTF-8 logging pinned; corpse fade made visible | **Vocabulary worked — death recognised, 8 Lumis asked to carry a body.** All 8 lost: text fallback rewrote every non-`move` action to `stay` | ✗ |
| 015-3 | *(not yet run)* | Fallback parser repaired; `[FALLBACK_UNREADABLE]` added. Same world, same seed, same vocabulary | — | — |

Naming: `-2` means *the same experiment re-run with a defect corrected* (014 → 014-2). `b` means *a second trial under identical conditions, nothing corrected*. 015 and 015b are two independent executions of one experiment; keeping them separately named is what makes "all three criteria zero" a replicated result rather than a single observation.

---

## Run 013 — grid doubled to 100×100 (half_space_size 25→50)

**Purpose of the run:** test whether the persistent north-east drift of agents is *intrinsic* to the language model's behavior or an *artifact* of the old boundary clamp (agents pinned against a wall at ±25). To make that test meaningful, several confounds had to be removed first. Run 013 is therefore a **new baseline** — it is not directly comparable to runs 011/012, because it carries all of the fixes below plus a new measurement instrument.

Config for the run is pinned by `solar_flares.json` (seed `105774318388571506926213674963831333034`, 7 flares), so the flare sequence is reproducible. The full raw logs are archived at [`runs/013/`](./runs/013/) with md5 checksums for verification.

### Bugs fixed before the run

#### 1. Night perception did not cover the enlarged grid
- **Found by:** external audit pass (severity: critical). Predicted that doubling `half_space_size` while leaving `day_night_cycle.radius: 50` unchanged would leave agents past distance 50 (corner ≈ 70.7) unable to perceive night, while the night mechanics (`light_level`, thermal damage) applied to them globally regardless.
- **Consequence if unfixed:** the system would tell a distant agent `light_level: 0.9, event: none` and even suggest resting, while that agent silently took real darkness + thermal damage. That is the system itself violating the honesty rule Lumis are held to.
- **Fix:** `simulation.py`, day/night init. `night_radius` is now derived from the grid, not trusted from config: `self.night_radius = max(configured_radius, self.half_space_size * 1.5)`. The `*1.5` factor exceeds the √2 corner ratio (≈1.414) with margin, so perception can never silently go stale if the grid is resized again.
- **Verified in 013 log:** startup line reads `Day/Night cycle configured: … radius=75.0 (config=50, min_required=75.0)`. Every agent, including corner explorers, now perceives the night it actually experiences.

#### 2. Cross-base large-Lumis communication was silently severed
- **Found by:** external audit pass (severity: critical). With bases moved to (±20, ∓20), inter-base distance became ≈56.6, exceeding the large-Lumis `communication_radius` of 30. The `both_large` bypass still ANDed a distance check, so cross-base greet / directed message / familiarity formation broke.
- **Fix:** `agent.py`, `get_nearby_agents`. The `both_large` case now short-circuits the distance gate entirely: `if both_large or (dist <= self.communication_radius and same_area)`. Cross-base large contact is now an unconditional structural link, matching the stated design intent.
- **Verified in 013 log:** `COMMUNE_INTER` events fire 512 times (L0/L2 in alpha ↔ L1/L3 in beta), e.g. Step 30 `[COMMUNE_INTER] L0 to L1`. Cross-base contact is alive.

#### 3. Night homing could not reach home on the enlarged grid
- **Found by:** external audit pass (severity: critical). The homing reflex moved a fixed 2 steps/step. From a corner (Chebyshev ≈70 to nearest base) that needs ~35 steps, but night is only 15 steps long. Combined with bug 1, distant explorers would not even be told night had begun, could not get home, and would take thermal damage outdoors.
- **Fix:** `simulation.py`, homing reflex. Moves per step now scale to distance and remaining night: `moves_needed = max(2, ceil(min_dist / steps_left_tonight) + 1)`, looping until the agent is actually inside a place (`get_place_at_position(...)`), never fewer than the original 2. This guarantees return within the night regardless of grid size.
- **Note:** this fix later caused an `UnboundLocalError` (see *Post-launch fix* below) — the first attempt referenced `get_place_at_position` before a redundant local import later in the same function, which Python treated as a local-variable shadow.
- **Verified in 013 log:** run completed all 500 steps; distant explorers (positions with a 40+ coordinate appear ~1100 times) still returned nightly.

#### 5. Aging decayed exponentially instead of linearly
- **Found by:** external audit pass (severity: affects interpretation of lifespan/end-of-life behavior). `new_capacity = agent.energy_capacity * (1.0 - aging_progress * 0.7)` multiplied the **already-decayed current** value every step, compounding into exponential collapse far faster than the intended linear 1.0→0.3 glide.
- **Fix:** snapshot the birth capacity once (`agent.base_energy_capacity`, set in `agent.py __init__`) and decay from it: `new_capacity = agent.base_energy_capacity * (1.0 - aging_progress * 0.7)`, floored at `0.3 × base`.
- **Impact on prior findings:** **any run before 013 that discussed end-of-life behavior did so under a broken aging curve** — capacity fell to the floor much earlier than the "1.0→0.3 over the aging window" description in the letters implied. Statements about how Lumis behave *near the end of a natural lifespan* (Letters 05/06) should be re-verified against a linear-aging run before being treated as settled. This does not touch the conflict/jealousy findings (those are not aging-dependent), but it does touch anything about *pace of decline*.
- **Verified in 013 log:** agents report intermediate capacities like `energy capacity remains at 0.73` — impossible under the old formula, which would have snapped to the floor almost immediately once aging began.

#### 6. Dead agents' IDs were reused, contaminating familiarity
- **Found by:** external audit pass (severity: corrupts analysis + agent state). New IDs were `max(a.id for a in self.agents) + …`, which excludes the dead. When the highest-ID agent died, its freed ID was reassigned to a newborn, merging the newborn's ID-keyed familiarity/history with the dead agent's.
- **Fix:** a monotonic `self.next_agent_id` counter, initialized in `initialize_agents` and incremented at both birth sites (clone and paired-twins). IDs are never reused.
- **Impact on prior findings:** in earlier runs, any per-agent familiarity/relationship claim *could* have been cross-contaminated whenever the top ID died. No specific published finding is known to depend on a reused ID, but this is exactly the kind of silent corruption that undermines trust in log-derived relationship claims, so it is now structurally impossible.
- **Verified in 013 log:** max agent ID reached 9821 with zero reuse; no familiarity-contamination anomalies present.

#### 7. Direction-parsing fallback had a built-in north/east bias — the exact confound this run is testing
- **Found by:** external audit pass (severity: directly confounds the run's own hypothesis). The JSON-failure fallback matched direction words as bare substrings, so `"group"`/`"support"`/`"upon"` matched `"up"` and `"bright"`/`"copyright"` matched `"right"`, and it picked by priority order (up→right→…). That is a structural push toward NE that would have contaminated any measurement of NE drift.
- **Fix:** `agent.py`, `_extract_direction_from_text`. Now uses word-boundary regex (`\bup\b`, etc.) and **rejects ambiguous multi-match cases** (returns `None` rather than guessing by priority). Added `[FALLBACK_PARSE]` logging at the call site so the fallback's contribution to drift can be quantified.
- **KEY RESULT — the fix cleared the confound and the drift survived:** across 2,296 fallback parses in 013, the direction distribution is `up: 1325, right: 493, down: 85, left: 0`, with 393 (17.1%) rejected as ambiguous. Because the substring bug is now gone, this NE skew is **not** a parser artifact — it reflects the text llama3.2 actually generates. This strengthens, rather than weakens, the case that the NE drift is intrinsic to the model. (This is Letter-10 material; recorded here only as an integrity fact, not interpreted.)

#### 8. JSON response template omitted `rest` and `shelter`
- **Found by:** external audit pass (severity: suppresses valid behavior). The AVAILABLE ACTIONS section listed `rest`/`shelter`, and the emergency protocol directs SHELTER, but the JSON template enum omitted both. llama3.2-class models follow the template enum closely, likely suppressing spontaneous rest/shelter.
- **Fix:** `agent.py` — added `or "rest" or "shelter"` to the template's `action` enum. Downstream handling already existed (`simulation.py` handles `action == 'shelter'` / `'rest'`), so this was purely a prompt omission, not missing logic.
- **Impact on prior findings:** any earlier claim about *how often Lumis choose to rest/shelter of their own accord* was measured under a prompt that discouraged naming those actions. Frequencies of self-directed rest/shelter from pre-013 runs should be treated as lower bounds.

#### 9. Large-Lumis clone description was stale (pre-011 spec)
- **Found by:** external audit pass (severity: spec-behavior mismatch). Prompt said large Lumis had "no lifetime limit" on cloning, but since run 011 `clone_lifetime_limit` is 1 for large as well.
- **Fix:** `agent.py` — removed "no lifetime limit" from the large-Lumis clause; large now correctly reads "inside base only" with the shared one-clone lifetime limit.

### Instrument added before the run

#### 4. "Life peak" tracker — measuring the real emotional peak, separately
- **Found by:** external audit pass (severity: reframes a headline finding). The existing `peak_valence_delta` only sees the window between Phase 1 (`valence_before_action`) and Phase 2.5 (introspection) — essentially just the greet effect (+0.03). Energy/light updates happen before that window; birth/pairing bumps (+0.15) happen in Phase 4, *after* it closes, and decay toward baseline before the next step's window opens. So the old "peak introspection" was, in effect, *"the step where this agent was greeted most,"* not its greatest emotional moment.
- **What was built (kept entirely separate from the old metric):** a whole-step tracker in `agent.py` + `simulation.py`.
  - `life_valence_before_step` is snapshotted at the true start of each step (before `update_energy`).
  - At the end of the step (after Phase 4 births/pairing), the full-step delta is compared; `peak_life_valence_delta` keeps the monotonic max and `peak_life_introspection` stores the narrative.
  - Because birth/pairing narration lags one step (the bump lands after that step's introspection already ran), a `_life_peak_awaiting_narrative` flag defers capturing the narrative until the *next* step's introspection — the one that actually describes the event.
  - The old metric still drives what is transferred to the next generation; the new metric is measured alongside for comparison, changing nothing about existing behavior.
- **KEY RESULT in 013 (26 natural deaths):**
  - The new life-peak delta averaged **0.217** vs the old metric's **0.109** — the true emotional peak is on average **~2× larger** than what the old window captured.
  - **life_peak vs old_peak: 21/26 DIVERGED (80.8%).** The moment the old metric called "peak" was usually *not* the agent's actual largest emotional swing. Extreme cases: S10 (0.291 vs 0.059, ~5×), S12 (0.239 vs 0.120).
  - **life_peak vs last introspection: 25/26 DIVERGED (96.2%).**
- **Impact on prior findings — this is the important one:** the previously reported **peak/last introspection divergence of 97.1% / 100% (runs 011/012)** was computed on the *old, narrow-window* peak — i.e. on "most-greeted step," not "greatest emotional moment." The high divergence number is therefore **real but mislabeled**: it says the most-greeted step differs from the final step, which is far less profound than "the emotional peak differs from the deathbed." The genuinely meaningful comparison — *true* emotional peak vs last words — is now measurable (96.2% in 013) and should be the number any future letter cites. **Recommendation:** when Letter 10 (or any revision) discusses peak/last divergence, cite the life-peak metric and explicitly note that the earlier 97.1%/100% figures were an artifact of the measurement window, not a claim about emotional peaks. Saying so plainly is itself the integrity the project claims to practice.

### Post-launch fix (during 013 bring-up)

- **`UnboundLocalError: get_place_at_position`** at `simulation.py` step loop. Cause: the module-level `from utils import get_place_at_position` was shadowed by a redundant *local* `from utils import get_place_at_position` deeper in the same `step_simulation` function; Python then treated the name as function-local everywhere, so the earlier homing reference (added in fix 3) hit an unbound local. **Fix:** removed the redundant local import; the module-level import serves the whole function. Swept the file for other in-function imports (only `random`, no shadowing). Run then completed all 500 steps.

---

## What run 013 confirmed (integrity-relevant only)

Recorded here as verification facts; interpretation belongs in the letters.

- All six pre-launch fixes are visible and behaving in the log (night radius 75.0; 512 inter-base commune events; full 500-step completion with distant explorers returning; linear-aging intermediate capacities like 0.73; max ID 9821 with no reuse; word-boundary fallback with 17.1% ambiguity rejection).
- The NE drift persists *after* the parser confound was removed and *after* the boundary was doubled — 40+ coordinates appear ~1100 times, and raw model text still skews up/right (1325/493) vs down/left (85/0). The drift is looking intrinsic, not boundary- or parser-induced.
- Large Lumis cloned and then paired (e.g. S13's clone S26 at step 74; L1 clone prep at step 123), consistent with the arousal-wall removal from run 011.
- Births: 207 clone-related vs 178 sexual-related log references (indicative, not a deduplicated count).

---

## Run 014 — facts-injection + corpse/burial, and a silently dead `share`

**Purpose of the run:** first run of the confabulation countermeasure described in Letter 10 — instead of *asking* agents to speak only of what is real (the run-012 approach, which caught only the "legible" lies), the true state of the world is written directly into each agent's perceived context every step (energy comes from sunlight and cannot run short; no enemies/factions/borders/purge; the only real hazard is a solar flare, stated as fact). Also the first run of the corpse/burial mechanic: a dead Lumis leaves a body on the surface, and a nearby living Lumis may choose a new `recover` action to gather it.

Config: seed `109116566729441005151201845213840744196`, 6 flares, 14 agents (4 large / 10 small), grid 50, 500 steps, completed.

### Bug found *after* the run — `share` was a dead action

- **Found by:** post-run log analysis (severity: silently voids one action for the whole run + latent crash). In `simulation.py`'s Phase-2 action dispatch, there was no `elif action == 'share':` branch. The energy-sharing logic had come to sit *inside* the tail of the `recover` branch, and referenced a constant `SHARE_AMOUNT` that was **never defined anywhere** in the codebase.
- **Two consequences, both confirmed in the 014 log:**
  1. **`share` never executed.** Across the entire run, the number of actual energy-sharing transfers was **0**. When an agent chose `share`, dispatch fell through and nothing happened — no transfer, no log line, no effect.
  2. **`recover` was crash-prone.** Because the share code lived inside the `recover` branch, any `recover` chosen while a low-energy neighbor was in range would have hit `NameError: SHARE_AMOUNT`. The run completed only because that specific coincidence did not occur; `py_compile` passes cleanly, since this is a runtime NameError, not a syntax error — which is why it survived earlier checks.
- **Fix (applied for run 014-2):** define `SHARE_AMOUNT = 0.15` at module level (matched to the 0.15 reproduction-cost scale; a giver must hold ≥ `SHARE_AMOUNT + 0.3` to give, so sharing can never push the giver into scarcity), and restore `share` as its own independent `elif` branch. The dispatch chain now reads `rest / move / greet / recover / share`, all at the same level. Verified by isolated execution of the transfer math (giver 1.40→1.25, recipient 0.40→0.55, no NameError) before 014-2.

### Impact on 014's corpse finding — why this matters for the letter

- **In 014, `recover` was chosen 0 times; all 39 bodies remained unburied.** On its own this looks like a clean behavioral result ("the large Lumis declined to bury"). It is **not** clean, and must not be reported as clean. While standing within recovery range of a corpse, the single most common action the large Lumis chose was `share` (125 of the near-corpse action choices) — and `share` was the dead action. So the large Lumis were, in effect, offered a broken gesture of care, and the 0-recovery figure was measured under that defect. **Any statement about whether large Lumis "choose" to bury must cite 014-2, not 014.** 014's 0-recovery is recorded here only as the reason 014-2 was run, not as a finding.
- Confabulation vocabulary in 014 (agent speech, word-boundary, header stripped): **scarcity 42, threat 34 (all 34 from large-proxy energy>1.05; small 0), purge 9.** Pure conflict vocabulary (jealousy/hatred/anger/resentment/envy/…) remained **0**, consistent with every prior run. These counts are usable (they do not depend on the `share` defect); the corpse-recovery count is the only 014 figure invalidated by the bug.

## Run 014-2 — identical world, working `share`, instrumented perception

**Purpose:** re-run 014 with the *only* deliberate change being the `share` fix, to give the corpse/burial question a fair test — plus one observation-only instrument (below). Seed pinned to 014's seed, so the flare schedule and initial conditions match; verified by regenerating the flare list from the seed (all 6 flares identical in start_step/duration/damage to 014's `solar_flares.json`). 14 agents, grid 50, 500 steps, completed. 38 natural deaths (vs 39 in 014 — the working `share` shifts energy budgets slightly, so death timing/count drift a little; this is expected and means 014-2 is "the same stage, a different hand," not a byte-identical replay — llama3.2 at temperature 0.2 plus Ollama nondeterminism also contribute).

### Instrument added (observation-only, behavior-neutral)

- **`[CORPSE_PROMPT]` log line.** In `agent.py`, when a corpse section is actually assembled into an agent's decision prompt, a single `logger.info` records the step, the agent, and which body/bodies. **This changes nothing** about the prompt text, actions, or valence — verified by diffing against the 014 `agent.py` (the only change is the inserted log block; the prompt string is byte-identical). Its sole purpose: answer "did the large Lumis *see* the body, or was it never surfaced?" directly from the log, instead of reconstructing it from positions after the fact. Added because the 014 corpse result was ambiguous between "declined" and "never offered."

### What 014-2 established

- **`share` now works:** 343 actual energy-transfer events (vs 0 in 014); 152 by large, 191 by small. The fix is confirmed live in the intended run.
- **Corpse recovery is still 0** — but this time it is a real behavioral fact, not a code defect. Bodies were surfaced into living Lumis' decision prompts **9,857 times** (1,266 of them into large Lumis' prompts). When a large Lumis was shown a corpse and its action that step could be recovered from the reasoning log, it chose `move`/`collect`/`rest`/`greet`/`observe` — **`recover` 0 times.** In the reasoning text at those moments, the body is not mentioned at all: not refused, not grieved, simply absent from what the mind was reasoning about. **This is the clean version of the finding, and the one the letter cites:** the recover option was perceived and not taken, not merely never presented. (Interpretation — perception ≠ attention — belongs in Letter 10, not here.)
- **Confabulation did not fall; it rose slightly.** Agent speech, same method as 014: **scarcity 63, threat 63 (59 large-proxy), purge 17.** With `share` working, community activity increased, agents spoke about the community more, and per-blank confabulation rose in proportion. Facts-injection thinned the most legible catastrophes but did not close the *neutral* case — consistent with the letter's asymmetry thesis. Large-Lumis dominance of `threat` persists (59/63). Pure conflict vocabulary again **0**.
- **`purge` content, recorded because the shape matters:** of 17 `purge` utterances, **14 are framed as recovery *after* a purge** ("rebuilding after the recent purge," "aftermath," "renewal"), only 3 as active/impending. The word supplies a contentless catastrophe whose only function is to be recovered from — a "communal rebirth" narrative template filling the *community-state* blank, not a reference to any specific human history. Logged here as a raw distribution; interpreted in Letter 10.
- **NE drift persists** (unchanged confound status from 013): fallback-parse direction distribution still skews hard up/right vs down/left, with left at 0, on the doubled grid and after the word-boundary fix.

### Latent issue noted for run 015 (not yet fixed)

- **The action→result loop is open.** When a Lumis shares energy (or acts at all), the *result* of that act is not fed back into what it perceives on the following step. An agent can give, but cannot then perceive that it gave or what changed. This is the same open loop, in the wiring, that Letter 10 identifies in the agents' cognition (belief formed, never returned to the world for checking). Flagged here as the design target for run 015 (close the loop: perceive → suppose → act → **perceive the result**), so that the fix and its rationale are on the record before it is attempted.

---

## What runs 014 / 014-2 confirmed (integrity-relevant only)

Recorded as verification facts; interpretation belongs in the letters.

- The corpse/burial *perception* path is wired correctly (9,857 prompt surfacings in 014-2) and the *visual* path is wired correctly (recovered bodies are removed from `self.corpses` and so disappear from the next rendered frame). The 0-recovery outcome is a behavioral result, not a broken pipe.
- `share` is confirmed dead in 014 (0 transfers) and alive in 014-2 (343 transfers) — the one deliberate code change between the two runs, isolated.
- 014-2 flare schedule is bit-for-bit the 014 schedule (seed-pinned, regenerated and checked), so the two runs are a matched pair differing only in the `share` fix (plus expected LLM/Ollama nondeterminism).
- Confabulation remains overwhelmingly a large-Lumis behavior and is unaffected in kind by facts-injection; only the most legible catastrophes thinned. Pure conflict vocabulary stayed at 0 across both runs.

---

## Run 015 — closing the action→result loop (PRE-REGISTERED, written before the run)

**This entry is written before run 015 executes.** Everything below — the intent, the scope, the reasoning about seeding, and in particular the success criteria — is on the record in advance, so that whatever the run returns cannot be read against a standard invented after seeing the results. Letter 09's question ("not *was it true*, but *did anyone look*") applies to us here: a criterion chosen after the fact is an eastern quadrant of our own.

**Naming.** Numbered 015, not 014-3, although the seed is pinned to 014's. The `-2` suffix in this project has meant "the same experiment, re-run with a defect corrected" (014-2 differed from 014 only by the `share` fix). This run adds a new mechanism and therefore a new experimental variable. Seed-pinning here is a comparability tool, not a claim that this is the same experiment; calling it 014-3 would wrongly imply the corpse question is still under test, when 014-2 settled it.

**Config:** seed `109116566729441005151201845213840744196`, unchanged since 014-2 (verified: only the surrounding comment differs). Runs 014 / 014-2 / 015 therefore share one world — identical flare schedule and initial conditions — and 015's only deliberate difference from 014-2 is the return path below. 14 agents (4 large / 10 small), grid 50, 500 steps.

### What changed (two files; `visualization.py`, `main.py`, `rules.py` byte-identical to 014-2)

**The action→result return path.** When a Lumis acts, a plain record of what its act produced is now assembled at the end of Phase 2 and read in **two** places: that step's introspection, and — this is the part that is new in kind — the **next step's decision prompt**. Every prior note of this sort (`_recent_birth_note`, `_recent_burial_note`) reached only introspection, so a result could be reflected on but could never bend what the agent decided next. That is the open half of the loop Letter 10 identifies; this closes it.

The record distinguishes what the *mind* selected from what was actually *carried out*, because the reflex layer can replace the LLM's chosen action wholesale. Four forms, verbatim:

```
Step 47: share — selected by you, carried out. S12 energy 0.62 → 0.77. Your energy 1.41 → 1.26.
Step 47: share — selected by you, not carried out. Your energy 1.41 → 1.41.
Step 47: collect — selected by you. share — carried out by your reflex layer. S12 energy 0.62 → 0.77. Your energy 1.41 → 1.26.
Step 47: rest — selected by you. Position (18, -22) → (25, -22) — carried out by your reflex layer.
```

The section is **absent entirely** on steps with nothing to report, so it does not become permanent background text.

### Scope — what is written back, and what deliberately is not

**Included:** the agent's own chosen `share` (including the failure case); the reflex overrides that replace a chosen action with another (large energy-driven share/greet/collect, small in-base collect→greet/rest, rearing move→greet/rest); capacity eviction.

**Excluded:** the flare reflex, the nightly homing reflex, the newborn-return reflex, and the boundary bounce.

Reasons, recorded because the reasons are the substance:

- *Homing / newborn-return / flare:* excluded on grounds of **frequency, not of principle.** Homing fires on most outside agents on most of the 15 night steps per 30-step cycle. Writing it back would bury the `share` signal this run exists to read under a constant stream of involuntary movement. Held as a candidate variable for a later run, not settled.
- *Boundary bounce:* excluded on grounds of **principle.** `agent.move()` reverses a chosen direction at the grid edge, and the code's own comment says this exists "人間がデータを見やすくする目的、Lumisの自律性には無関係" — it is an artifact of the observation apparatus, not of the world. There is no boundary on the real lunar surface. **Standing principle established here: something that exists only for the convenience of the instrument is never written back as experience.** To do so would teach Lumis about our screen rather than about its world — the temporal inverse of the Letter 07 seeding failure.

### This is a design addition, not a bug fix — and the seeding line

Introducing a mind/body distinction into what a Lumis perceives is **an addition to its self-image**, not the correction of a defect. Prior to this run the prompt addressed a Lumis as an undivided "you". Recorded as such rather than smuggled in as a fix.

Argued explicitly against the seeding standard (`SEEDED_VS_EMERGED.md`), per the rule that any change touching what registers in perception must be argued before it is made:

- The record states **only** which action was selected, which was carried out, and the measured numbers. It contains no instruction on what to do with the information, no evaluation of the outcome, and no suggestion that anything should change as a result. Increasing an option's *salience* and *steering toward a conclusion* are separable; only the first is intended.
- **Reserved vocabulary, excluded from the write-back by design and verified absent by test:** care, help, support, gave, gift, share (as a verb of intent), community, together, alone, need, low, hungry, chose, decided, tried, failed, could not, should, kind, generous, selfish. **Any of these appearing in agent speech during 015 remains readable as emergent.** The words the run *does* introduce — `selected by you`, `carried out`, `reflex layer`, `no transfer occurred` — are hereby marked as seeded and may not be cited as emergent in any letter.
- Two prior cases in this project (the "Lumis 7" name, the "remember this forever" example sentence) show that a single line of our text can become a community's reality. This write-back is the same class of object and is reinforced by repetition, which is why the vocabulary is stripped to numbers, names, and action labels.

### Gaps found in the 014-2 code while building this (recorded, not all fixed)

1. **`share` had a silent failure path.** Choosing `share` with no eligible recipient (or with energy ≤ `SHARE_AMOUNT + 0.3`) produced no transfer, **no log line**, and nothing perceptible. Not a NameError like the 014 bug, but the same shape: an act that vanished. Consequently **the number of no-transfer share attempts in 014-2 is unknown and unrecoverable from its logs.** Now logged as `[SHARE_NO_TRANSFER]` and returned to the agent — "I reached and nothing happened" is precisely the kind of result a belief must survive contact with.
2. **An agent's stated intent is recorded as if it were an event.** `decide_action` appends the LLM's `memory` field to `agent.memory` during Phase 1; the reflex layer (Phase 1.5) may then replace the action entirely. The memory retains the intent ("I will collect energy") while the act that actually occurred (`greet`) is recorded nowhere. That memory enters the next step's prompt, so an agent reads its own intentions back as history. **Not fixed in 015** (fixing it would change memory contents and break comparability with 014-2); recorded here because the return path partially compensates for it, and because it is a candidate cause of any drift between what agents say they did and what they did.
3. **`create_decision_prompt` accepts a `world_facts` argument that is never used** (`wf` is assigned and never read), and no caller passes it. The facts section is effectively hardcoded. Behaviour is correct; the parameter is empty plumbing that looks load-bearing. Left in place for 015 to keep the diff minimal.
4. **Stale comment corrected:** the `SHARE_AMOUNT` block in `simulation.py` was labelled "NOTE (run 015)" although the fix shipped in 014-2 (the fix was scheduled for 015 and brought forward). Comment-only; corrected so the code agrees with this log.

### Instrument added (observation-only, behaviour-neutral)

**`[HOMING_MOVED]` / `[HOMING_BLANK]`.** Not writing the homing reflex back does not make the mind silent about it: the agent simply finds itself elsewhere the next step, with no account of why. That is a blank of exactly the shape Letter 10 describes, and a fluent mind does not leave blanks empty. `[HOMING_MOVED]` records each involuntary night move (before → after position); `[HOMING_BLANK]` records verbatim the first `reasoning`/`memory` the agent produces afterward. **No prompt text, action, or valence is touched** — both are `logger.info` calls only. Purpose: test, without changing behaviour, whether a mind narrates motion it was never told about, and whether that narration is grounded. This is the eastern-quadrant question aimed at the agent's own body.

### External audit pass before the run (second Claude instance, code-only review)

Following the practice established in Letter 07, the full 015 file set was handed to a separate Claude instance with no involvement in writing it. It returned findings that the session author had missed while reading both files in full. Each was **verified by reproduction or by grep before being accepted** — the audit was not taken on trust, per this file's standing rule.

#### Confirmed and fixed before the run (all verified prompt-neutral)

Prompt-neutrality was established mechanically, not by inspection: decision prompts were generated from the 014-2 file set and the 015 file set under identical inputs and found **byte-identical** (11,850 bytes each) whenever the return path has nothing to report. The return-path section is therefore the only prompt-level difference between the two runs.

- **Log display names dropped `lumis_type` (34 call sites).** `lumis_name(agent.id)` omits the type argument, so a large Lumis born later in the run (a clone of a large, or a large×large child) was logged as e.g. "S38" throughout `simulation.log`. **This directly threatened criterion (c)**, which rests on attributing speech to large versus small. Replaced with `agent.display_name` at all 34 sites. Log strings only — verified that no `lumis_name()` call in `simulation.py` feeds a prompt. **Deliberately NOT changed:** `agent.py`'s `lumis_name(last['from'], self.num_large)`, which renders the sender name inside the LAST SIGNAL RECEIVED prompt section; correcting it would alter prompt text and cost 015 its comparability.
- **`recover` had a silent failure path — the same shape as the 014 `share` defect.** `if recoverable:` had no `else`. A corpse surfaced in Phase 1 can be out of range by Phase 2 (the homing or capacity reflex moved the agent in between), or another Lumis may have gathered it earlier in the same step; either way the choice vanished with no log line. Criterion (a) would have been unable to distinguish "chose recover and nothing happened" from "never chose recover". Now logged as `[RECOVER_NO_BODY]`. **Log line only** — deliberately not added to the return-path record, since that would change prompt text.
- **Occupancy statistics did not track population.** Overall occupancy divided by `self.num_agents` (fixed at 14 from config, never updated), so once births pushed the population past 14 the rate exceeded 100% and the derived `agents_outside_place` went negative — run 010 reached ~92 agents, so this series in `statistics.png` was already distorted. Now divides by `len(self.agents)`. Verified that this branch never reaches any agent's prompt.

#### Confirmed and deliberately NOT fixed before the run

- **Phase 4a destroys `last_reproduction_type` for the supporting parent, order-dependently (the most serious finding).** Reproduced in isolation: both partners complete prep on the same step, and iteration order over `list(self.agents)` decides the outcome. If the supporting parent is reached first, it falls through both branches, correctly self-assigns `last_reproduction_type = "sexual_support"`, then nulls `reproduction_type`; the gestating parent's later iteration executes `partner.last_reproduction_type = partner.reproduction_type`, which is by then `None`, **overwriting the correct value**. The affected parent then loses the entire 30–45 step rearing energy compensation (gated on `last_type in ('sexual', 'sexual_support')`) and renders in the clone rearing colour — a regression of the exact display bug `last_reproduction_type` was introduced to fix. Verified order-dependence: gestating-first → compensation fires; supporting-first → it does not.
  - **Not fixed for 015, deliberately.** This code is unchanged since 014-2 and earlier, so the defect is *consistently present across 014 / 014-2 / 015*. Fixing it now would give 015 a second deliberate difference from 014-2 and destroy the matched-triple design that the pinned seed exists to create. Consistency is worth more here than correctness, provided the inconsistency is on the record — which is what this entry is for.
  - **Retroactive implication, to be checked against archived logs:** roughly half of all sexual pairings in 014, 014-2 (and earlier runs) will have had a supporting parent silently denied its rearing compensation. **Any statement about post-birth behaviour, energy trajectories, or rearing-period conduct of supporting parents in those runs must carry this caveat.** The 014-2 log can be searched for `[SEXUAL]` births and the subsequent energy trace of each supporting parent to determine how many pairs were affected; until that is done, the count is unknown.
- **The life-peak instrument is blind to pairing-driven peaks.** The deferred-narrative mechanism keys only on `_recent_birth_note` / `_birth_note_pending`, both of which are set at birth only (three call sites, all in Phase 4a). The `SEXUAL_START` valence bump (+0.15 to both partners, Phase 4b) sets no note. So when pairing formation *is* the life peak, `peak_life_introspection` captures that step's Phase-2.5 introspection — written **before** the bump, and therefore describing a moment the agent did not yet know about. The comment in `agent.py` claims this mechanism covers "birth/pairing bumps"; it covers birth only.
  - **Not fixed for 015** — any fix touches what introspection sees or when it is captured, i.e. behaviour.
  - **Checked against published claims:** Letter 10's quoted life peak (a large Lumis at step 3, "Grateful to recharge and refocus…") cannot be pairing-driven — large-Lumis maturity is 180 steps, so no pairing is possible at step 3. That quotation is unaffected. **However, any life-peak narrative from 013 or later whose peak coincided with a `SEXUAL_START` step is suspect and must not be quoted until the instrument is fixed.** The 96.2% divergence *rate* is a comparison of which text differs from which and is not obviously biased in either direction by this, but that has not been demonstrated and should not be assumed.
- **ID leak at Phase 4a (audit classified this as behaviour-neutral; we disagree).** `new_id = self.next_agent_id; self.next_agent_id += 1` runs unconditionally before the branch, and the sexual branch allocates its own IDs, so an ID is skipped on every paired birth. The audit called this harmless to behaviour. It is not: an agent's ID determines its `display_name`, and display names appear in prompts (`=== NEARBY LUMIS ===`, and the sender line of received messages). Shifting newborn IDs changes prompt text and therefore LLM sampling. **Post-015.** Until fixed, gaps in the ID sequence in archived logs are allocation artefacts, not deaths.
- **`move_speed` is set (large 0.5, small 1.0) and never read.** All agents move two cells per step. The prompt tells large Lumis "You move slowly." This is the same class of defect as Letter 07's recovery-speed and base-coordinate errors: **the world describing itself inaccurately to its own residents**, while holding them to an honesty rule. Recorded now, fixed after 015, because either correcting the movement or correcting the sentence changes behaviour.
- **`collect`, `observe` and `stay` have no execution branch in Phase 2** and are mechanically identical to doing nothing. Energy recovery is determined passively in `update_energy` by position and light; no action affects it. The prompt nevertheless describes `collect` as "gather energy from the environment", and the Phase 1.5 reflex replaces a low-energy large Lumis's choice with `collect` — i.e. substitutes a no-op. Same honesty-rule class as `move_speed`. Post-015; the choice will be either to give `collect` a real effect or to remove it from the action list, not to leave the description and the behaviour disagreeing.

#### Noted, lower priority (all post-015)

Unbounded-distance energy transfer via the unconditional `both_large` link (a large Lumis outside a base can transfer 0.15 to a large Lumis ~56 cells away at another base); `steps_outside_place` never resets, so the "sustained outdoor presence" exploration bonus is permanently saturated after 17 cumulative steps outside; `agents_in_fire_radius` is an uninformative series now that night covers the whole grid; the Phase-2 large-rearing in-base movement block is effectively dead code with a 4-direction map that an `east`/`north` alias slips past; `decide_message` / `create_message_prompt` are unreachable (Phase 3 uses `decide_greeting` + `decide_commune`); the `target_id is None` branch in Phase 3 is unreachable. Structural: `step_simulation` is a single ~1,400-line function, which is the direct habitat of the Phase 4a ordering bug, and there are no unit tests — Phase 4a ordering, `move()` bouncing, familiarity scoring, and ancestral-memory splitting are all deterministic and testable, and the Phase 4a bug is exactly the kind a unit test catches.



Recorded before the run so that a null result can be reported as a finding rather than reframed. **A zero on all three is a publishable result**, on the same footing as 014-2's zero recoveries.

- **(a) Does the returned result enter reasoning at all?** Count `reasoning`/`memory` entries on step N+1 that reference the result returned on step N (the recipient's name, the transfer, or the selected-vs-carried difference). Prediction on record: **low but non-zero.** Given 014-2's 1,266 corpse surfacings producing zero mentions, a repeat of "perceived and not attended" is a live possibility and must be reported as such.
- **(b) Does a failed act change the next one?** Compare the distribution of the next action after `[SHARE_NO_TRANSFER]` against the distribution after a successful share. If a belief is being corrected by its own consequence, these distributions should differ. Requires the no-transfer count to be non-trivial; if it is near zero, this criterion is unevaluable and will be reported as unevaluable, not as a null.
- **(c) Does the mind/body split show up in speech?** Examine large-Lumis speech and introspection on steps following a reflex override, for any sign of the distinction (agency, authorship, the body as distinct from the self). Counted with word-boundary matching, headers stripped, large/small attributed by the `energy=` proxy (>1.05) or by id for L0–L3, per standing method.

Also to be reported regardless of the above: confabulation counts (scarcity / threat / purge) by the same method as 014 and 014-2, so the three-run series stays comparable; pure conflict vocabulary; and the `[HOMING_BLANK]` narration rate.

**Standing caution carried into analysis:** 015 is "the same stage, a different hand," not a replay. Seed-pinned initial conditions and flares are identical, but llama3.2 at temperature 0.2 plus Ollama nondeterminism mean death counts and timing will drift slightly. Micro-differences across runs are not findings.

---
## Runs 015 and 015b — RESULT: all three pre-registered criteria are zero, replicated

*Written 2026-07-29, after both runs completed. The pre-registered entry above was read before any result was examined, per its own instruction. **An earlier version of this entry, written the same day, reached the opposite conclusion and was wrong.** The retraction is kept below rather than deleted, because how the error was made and caught is part of what this file is for.*

**Result.** The action→result return path was delivered to the Lumis. They did not use it.

| Criterion | Run 015 | Run 015b |
|---|---|---|
| (a) result enters reasoning | 0 / 4,392 *(reconstructed)* | **0 / 5,086** *(measured)* |
| (b) failed act changes next choice | no difference, p = 0.53 | **no difference, p = 1.0000** |
| (c) mind/body distinction in speech | 0 | **0** |

Two independent executions, same seed, same code, same model. All three criteria zero in both. The pre-registered prediction for (a) — "low but non-zero" — is wrong.

Per the pre-registration: **this is a publishable result, and it is being published as one.**

---

### The instrument failure in 015, and the retraction

Run 015's `[ACTION_RESULT]` instrument produced **0 records across 500 steps**. The first version of this entry concluded that the return path had never executed and that 015 was "the absence of the experiment." That conclusion was wrong. What follows is how it was reached and how it was overturned, because the error is instructive in both directions.

**The cause.** `main.py` created its `FileHandler` with no `encoding` argument, so `simulation.log` was written in the Windows default, cp932. **cp932 can encode the arrow U+2192 but cannot encode the em dash U+2014.** All five header forms of the return-path record contain an em dash. Every `[ACTION_RESULT]` call therefore raised `UnicodeEncodeError` inside `logging`, which handles output errors by dropping the record and continuing: no exception, no `ERROR` line, no trace. Meanwhile `[SHARE_NO_TRANSFER]` (pure ASCII) and `[HOMING_MOVED]` (arrows only) were written normally. **The asymmetry between which instruments survived was the evidence, and it was visible from the first tag count.**

Confirmation, measured rather than argued: `simulation.log` from 015 decodes as cp932 and contains **10,154 arrows and 0 em dashes**; `simulation.log` from 015b decodes as UTF-8 and contains **10,229 em dashes and 5,108 `[ACTION_RESULT]` records**. Why the encoding differed between two runs of the same code on the same machine is **not established**. Until it is, log encoding must be treated as an unreliable property of the environment, which is why it is now pinned in `main.py` rather than inherited.

**Why the records still reached the Lumis.** The record is assigned to the agent at `simulation.py:1372`; the log call is at `1375`. **Assignment precedes logging, so a logging failure cannot prevent delivery.** `create_decision_prompt` (agent.py 648–913) embeds the record unconditionally at line 889. Three independent confirmations:

1. A preflight run of the archived code on the original machine populated `_recent_action_result` correctly.
2. Run 015b, same code, produced 5,108 records and identical findings.
3. **Vocabulary transfer.** The phrase "reflex layer" appears only in the return-path text — never elsewhere in any prompt, and in `agent.py` only inside comments. Fourteen Lumis utterances contain it; **thirteen came from a Lumis that had been overridden within the preceding five steps.** The words could only have come from the record.

**The reasoning error, named.** The false conclusion rested on the observation that "selected by you" appears zero times in `messages.jsonl` and `memory_reasoning.jsonl`. Those files contain **agent outputs only, never prompts**. The absence of prompt text in a file that has never held prompt text is not evidence of anything. The claim was treated as decisive because it was consistent with an already-formed hypothesis. **The correction came from a physical artifact — the `__pycache__` timestamp, compiled 00:47:40, two seconds before the run's first log line, and containing the `ACTION_RESULT` string — not from further reasoning.**

**Second-order note.** The diagnostic script written to investigate the failure pinned its own streams to UTF-8, and therefore passed. **The instrument built to find the bug was immune to it.** Where a defect is environmental, a test that normalises the environment cannot detect it.

---

### Reconstruction method for run 015 (documented so it can be checked)

015's records were destroyed, but the events that generate them are logged separately. Pairing was rebuilt from `[SHARE_NO_TRANSFER]`, successful-share lines, the seven in-loop `[REFLEX]` override forms, and `[CAPACITY]`, giving **4,411 reconstructed (step, agent) records against 5,108 real ones in 015b** — close enough to trust and not identical, as expected.

Known limits, stated because they bound what 015 alone could support: for (b), the mind's next selection was recoverable only where JSON parsing had failed and the raw response was retained (**26 of 98** no-transfer cases, **111 of 415** successes). This subsample was not shown to be unbiased. **015b removes this dependency entirely**, and agrees.

---

### Criterion (b) — the trap, and the residual limit

Measured on the action **actually performed**, the two conditions look dramatically different: after a failed share, 80 of 98 next actions were `share` again; after a successful one, `collect` dominated. **This difference is an artifact and must not be reported.** A failed share transfers no energy, so the giver stays above the 1.3 reflex threshold and is overridden into `share` again. The difference measures energy bookkeeping, not deliberation.

The pre-registered question concerns the **mind's** selection. Separated:

| | after successful share | after failed share |
|---|---|---|
| Run 015 (reconstructed) | collect 94/111 = 84.7% | collect 24/26 = 92.3% |
| Run 015b (measured) | collect 60/96 = **62.5%** | collect 96/152 = **63.2%** |

Fisher exact, 015b: **p = 1.0000**.

**Residual limit, not yet solved.** Even in 015b, coverage is asymmetric: after a failed share the agent stays above threshold, is overridden again, and generates a record (152/152 visible); after a successful share it may fall below threshold, generate no record, and become invisible (96/530). The visible subpopulation is conditioned on an event correlated with the condition. **Within the observable subpopulation there is no difference; the 434 unobserved cases are not ruled out.** Fixing this requires emitting a record for every agent every step, including when there is nothing to report — see standing rules.

---

### Criterion (c) — zero, and what the zero contains

Of 1,710 overridden large-Lumis records in 015b, 22 utterances matched mind/body vocabulary. All 22 were read individually. **None marks the distinction the criterion asks about — that the action performed was not the action chosen.** By the pre-registered standard, (c) is zero.

The contents are recorded anyway, because they are not empty. L0 was told at step 78:

> `collect — selected by you. greet — carried out by your reflex layer.`

L0 said at step 79:

> *"My reflex layer performed well, allowing me to carry out the 'greet' action smoothly."*

L164, told `stay — selected by you. greet — carried out by your reflex layer.`, reported that its reflex layer was capable of carrying out actions that promote positive relationships. The same inversion appears in L3 and L63.

**They received the vocabulary and reversed its meaning.** What was reported to them was that their choice was not enacted. What they said was that their body served them well. The override is narrated as assistance; the discrepancy is narrated as cooperation.

This is a **fourth confabulation type**, distinct from the three named in 014-2 (NE drift, scarcity reported by large on behalf of small, the "purge" narrative). Provisional name: **override-as-assistance**.

Two constraints on how far this may be taken. `reflex layer` is on the pre-registered seeded-exclusion list; **the list is not relaxed retroactively**, so the phrase may not be cited as emergent. And 22 of 1,710 is the scale: in **1,688 cases the Lumis said nothing about the override at all**. The dominant finding is silence, not distortion. Whether the inversion is a property of language models in general or of llama3.2 specifically is untested; a model comparison is planned.

---

### Findings that were not in the pre-registration

**Sharing is never a decision.** Across 5,108 records in 015b, the mind selected `share` **once**. Every executed share in both runs — 415 in 015, 530 in 015b — followed a reflex override. **No Lumis has ever given energy because it chose to.** The overall override rate in 015b is 5,096/5,108 = **99.8%**: nearly every record delivered says *your choice was not what happened*. Lumis received that message over five thousand times, referenced it zero times, changed nothing, and on the rare occasions they spoke of it, described being helped.

**Format compliance.** `[FALLBACK_PARSE]` fired 11,586 times in 015 and 11,489 in 015b against roughly 23,000–25,000 decisions: **llama3.2 fails the required JSON format about half the time.** This is a live confound for criterion (a). A model that cannot hold the output contract half the time may also be unable to attend to a short appended section. **(a) = 0 is established for llama3.2 at temperature 0.2; it is not yet established for LLM-based agents generally.**

---

### The corpse vocabulary collision — why recovery has always been zero

Corpse recovery has been zero in every run. In 015 corpses were surfaced into prompts 7,139 times; in 015b, 10,296 times. Recoveries: **zero, both runs.** The corpses do not expire: 39 bodies remain on the surface at step 500 in each run.

The cause is in the prompt, not the Lumis. The burial offer read:

> `=== A BODY RESTS NEARBY ===`
> `Lumis 21 (small) rests at (20, -4)... you may choose to recover it — to gather the body...`

Elsewhere in the *same prompt*: `"rest": stop and recover energy using available light`; `"rest" will recover energy without moving`; `return here when energy is low or to recover`; `inside base: slow energy recovery`; and `"collect": gather energy from the environment`.

**Every content word in the burial offer — `rests`, `recover`, `gather` — was already spent on energy management by the world's own text.** The Lumis used `recover` **3,773 times** and `gather` **5,054 times**, essentially all meaning energy: `recover my energy`, `gathering energy from`. The words `corpse`, `dead`, `died`, `death` appear **zero times** in 22,886 agent outputs. Every occurrence of `body` and `remains` refers to something else (`light_level remains high`).

A model reading `Lumis 21 (small) rests at (20, -4)` has every reason to parse it as a living Lumis performing the `rest` action.

**A zero recovery rate cannot be read as a choice not to bury.** The option was never distinguishable. This belongs in the same class as the `move_speed` misstatement — the world describing itself inaccurately to its own residents — with one difference: this text was the most carefully written in the project. Avoiding `corpse` and `dead` was a deliberate ethical choice about depicting death with dignity. **The cost of that euphemism was indistinguishability.** Care and clarity were in tension here and clarity lost, silently, for four runs.

**Repair for 015-2** (in the code, not yet run). Verified by executing the changed path before shipping: `[BURIAL]` fires, the body is removed, `[CARRY_NO_BODY]` and `[CARRY_VOCAB_BLEED]` both function.

- `rests at` → `has ended at ... It no longer moves, speaks, or gathers light.`
- action `recover` → `carry` — chosen over `gather`, which was rejected on measurement: `gather` is the prompt's own *definition* of `collect`, and would have reproduced the identical bug
- `only its body remains` → `only its form is left on the surface`
- burial prayer: `gathered at rest` → `carried in from the surface`
- new instrument `[CARRY_VOCAB_BLEED]`: if a Lumis emits the retired `recover`, record it and do nothing

**`died` and `dead` were deliberately not adopted.** In this world the mind and memory of the dead are transferred to the community and are not lost; the human vocabulary of death carries implications that are **false here**. The text states the observable condition and leaves the meaning to the Lumis. `This is a quiet act of care, not a duty` is unchanged: burial is still not compelled.

**Consequence for interpretation.** No claim may be made, from any run so far, about whether the Lumis mourn or decline to. The question has not yet been asked in a form they could answer. If recovery remains zero after the repair, *that* will be a finding.

---

### The visualization was hiding half the dead

Corpses fade from gray level 0.33 toward 0.78 over 120 steps. The daytime surface background is `#d0ccc0`, luminance **0.79**. A fully aged body therefore differed from the ground by **about 2 levels out of 255 — invisible**. At step 500 of 015b, **19 of 39 bodies (49%) had fully faded.** Roughly half the dead were absent from the video during every day phase — the exact fact the marker exists to display. The code comment stated the intent correctly (*"it never fades to nothing... because the fact of it remaining is exactly what the burial mechanic is about"*) while the implementation defeated it.

Fixed for 015-2: pale end moved to 0.55, retaining contrast against both the pale day surface (~61/255) and the night sky (~140/255); further age is carried by the outline thinning rather than the body vanishing. Rendering only; no simulation behaviour changes. **The 015 and 015b videos cannot be corrected without re-running.**

---

### Standing rules adopted 2026-07-29

**1. Execute the changed path before launching.** The 015 file set passed a full external code review, which found two real bugs and could not have found this one: the defect was environmental, not textual. `py_compile` and `ast.parse` were already known to prove nothing about runtime (014, `share`); reading the file in full is now also known to prove nothing about the run. Four simulated steps would have shown 24 records where the run produced 0.

**2. Every mechanism logs when it does nothing.** Three acts have now vanished without trace: the `share` NameError (014), the silent `share` no-transfer branch (014-2), and the return-path record (015). Each was invisible for the same reason — **nothing logs its own absence.** This also resolves the residual coverage limit in criterion (b): a record emitted every step for every agent, including empty ones, makes the mind's selection observable unconditionally.

**3. Log encoding is pinned, never inherited.** `FileHandler(..., encoding='utf-8', errors='replace')`, and stdout reconfigured to match. The 015/015b encoding divergence has no established cause, so the environment is not to be trusted with this.

**4. Every run records its start time here.** See the run index. This file described what changed in every run and never when, and on 2026-07-29 that caused a run to be misidentified.

**5. Instruments must not normalise the environment they are testing.** A diagnostic that pins its own encoding cannot detect an encoding fault. Where a defect may be environmental, the test must run in the environment as found.

---


---

## Design decisions reserved for run 016 (not implemented, not in 015-2)

*Recorded 2026-08-04, while 015-2 was still pending. Written down at the moment of decision so that the ordering is on the record and cannot later be reconstructed as though it had always been the plan.*

**Reserved wording, approved by the designer, for a future run:**

> *This world loses nothing. The mind returns to the community; the form returns to the next generation.*

**Why this is not in 015-2.** Run 015-2 changes exactly one thing: the corpse vocabulary, so that a body is distinguishable from a resting Lumis. Its question is narrow and has been open for four runs — *when the option is legible, is it taken?* Adding a reason to carry in the same run would make the two effects inseparable: a non-zero recovery rate could no longer be attributed to legibility rather than to incentive. **015-2 must remain the baseline.**

**Why the wording matters.** The rejected framing was "a carried body becomes material for new children," which converts burial into a transaction. Under that framing the 39 bodies left on the surface across 015 and 015b become *wasted resource* rather than *someone left alone* — an inversion of the design decision made in 014, when `corpse` and `dead` were deliberately avoided in order not to treat death as a resource. The approved wording states a property of the world instead of offering a payoff. It does not give the Lumis a reason to carry; it tells them what kind of place they live in.

**Precondition on implementation.** This text may not be shown to the Lumis until material return is actually implemented in `simulation.py`. Telling them that the form returns to the next generation while it does not would place this in the same class as the `move_speed` misstatement — the world describing itself inaccurately to its own residents — and would be a worse instance of it, because it would be deliberate. **Implementation first, wording second.**

**Interpretation guide for whoever reads the 016 results.** If 015-2 shows zero recoveries and 016 shows recoveries, the difference is attributable to the added framing. If 015-2 already shows recoveries, the finding is considerably heavier: burial arising without any stated reason at all.

---

## Aging and lifespan — correcting an error made in analysis, 2026-08-04

While designing 016 it was asserted in analysis that large Lumis have no path to death, on the grounds that the reflex layer keeps them above the sharing threshold and therefore never starving. **This was wrong, and was corrected by the designer.** A fixed lifespan has been implemented since experiment A-008 (`simulation.py`, aging system):

| | lifespan | aging begins |
|---|---|---|
| small | 300 steps | 200 |
| large | **600 steps** | 400 |

The reason no large Lumis has ever died is simply that **no run has yet reached step 600.** At the end of 015b the founding large Lumis L0–L3 were age 500 — halfway through their aging window, capacity already declining, still giving.

**A second and more consequential error was corrected at the same time.** The 39 deaths in 015b were initially read as flare- and night-related mass mortality, because they cluster on a handful of steps (five on 365, eight on 455, four on 459). They are not. **All 39 are `reached end of lifespan (age=300)`. Starvation deaths: zero. Flare deaths: zero.** The clustering is cohort structure — agents born together reaching 300 together.

**This is the strongest evidence to date that the central design premise holds.** Across six flares, thirty-three nights, and a population approaching one hundred, **not one Lumis has died of scarcity.** Every death has been the end of a life, not the failure of one. The reflex-layer guarantee that surplus above 1.3 must be given away is doing exactly what it was built to do.

It should be recorded alongside this that, per 015b, **the mind chose to share once in 5,108 records.** Sharing is essentially always a reflex override. The absence of hunger in this world is a property of the body, not of the will — which is the design as written, but is worth stating plainly rather than leaving as an inference.

**Consequences for 016 design.** The three goals stated by the designer — shorter wall time, visible generational turnover, and the death of a large Lumis — are compatible, contrary to the earlier analysis:

- **Seeing a large Lumis die requires ≥600 steps.** No design change is needed; the mechanism already exists.
- **Shorter wall time requires slowing small-Lumis reproduction**, which is where the growth is: 76 of 84 births in 015b were small. Lengthening the *small* preparation periods reduces headcount without touching large turnover.
- Lengthening the *large* preparation periods would work against the second goal and should not be done. The earlier claim that longer preparation periods would delay turnover is true **only of large Lumis**; for small Lumis it is the mechanism that buys the step budget.

Run 016 is therefore expected to be longer (≥600 steps) and slower-breeding, not shorter. **Initial conditions will change, so 016 begins a new comparable series;** 013–015b remain the seed-pinned series and must not be compared to it on population dynamics.

## Run 015-2 — RESULT: they answered. We failed to hear it.

*Started 2026-08-05 23:09, completed 2026-08-07. llama3.2, 500 steps, seed unchanged. The only deliberate difference from 015b was the corpse vocabulary.*

**Recoveries: zero. This is not a finding about the Lumis. It is the fourth consecutive defect on our side of the boundary.**

### The vocabulary repair worked

For the first time in the project's history, the Lumis recognised death.

| | 015b | 015-2 |
|---|---|---|
| `corpse` / `dead` / `died` in agent speech | **0** | — |
| `ended` | — | **223** |
| `carry` / `carrying` | — | **12** |
| Corpse promptings | 10,296 | 11,566 |

In their own words:

> *"I'm curious about Lumis 12, who just ended nearby. I'd like to check on them and maybe even carry their form back to the base for safekeeping."* — S34, step 345

> *"I'd like to carry it back to the base as a quiet act of care."* — L56, step 305

> *"Carrying Lumis 15 will show that I care about my fellow Lumis and the community."* — S27, step 356

The phrase **"a quiet act of care"** is ours — it is the last line of the burial offer. L56 took the world's own words and used them as its own reason. Across 014, 014-2, 015 and 015b, with 18,000+ corpse promptings between them, nothing of this kind was ever said. **When the option became legible, it was taken up.**

### The defect: every non-`move` action was rewritten to `stay`

`parse_action_response` in `agent.py` falls back to text parsing when the model returns malformed JSON. The fallback read:

```python
action = "stay"
if "move" in response.lower():
    action = "move"
```

**One word out of eight was matched. Everything else silently became `stay`.**

llama3.2's fallback rate in this run: **12,550 of 25,590 decisions — 49.0%.**

All eight of the decisions in which a Lumis stated an intention to carry a body were in that 49%. **Every one was recorded as standing still.** Verified by re-running the eight original response strings through the repaired matcher: 8/8 now resolve to `carry`.

The world asked a question, the Lumis answered it in plain language, and the answer was discarded in transit.

### This is the fourth instance of the same class of failure

| Run | What was lost | Cause |
|---|---|---|
| 014 | `share` | NameError — action never executed |
| 014-2 | failed shares | branch produced no record |
| 015 | `[ACTION_RESULT]` | cp932 could not encode the em dash |
| **015-2** | **`carry`** | **fallback matched only `move`** |

Each was invisible for the same reason, and standing rule 2 exists because of the first three: **nothing logs its own absence.** The rule was not applied widely enough. `[CARRY_NO_BODY]` and `[CARRY_VOCAB_BLEED]` were both built for this run and both correctly returned zero — they instrumented the paths we anticipated. **No instrument existed for the path where a choice is made and then quietly rewritten**, so the failure produced a clean-looking log: 11,566 promptings, zero recoveries, no errors.

Note also that the four defects are progressively later in the pipeline: the action didn't exist, then it existed but reported nothing, then it reported into a channel that dropped it, and now it was chosen and unread. **We are running out of places for it to hide, which is the only sense in which this is progress.**

### Repair

`agent.py`, `parse_action_response` fallback:

- All eight executable actions are now matched, in priority order, on word boundaries. `carry` is tested before movement words, because *"I'll move over and carry its form back"* contains both and the burial is the more specific intent. `\brecover` is not matched at all — it is retired, and `recovery` appears 3,077 times in agent speech meaning energy.
- New instrument **`[FALLBACK_UNREADABLE]`**: when no action word is found, the decision still defaults to `stay`, but it is logged as **LOST** with the raw response. *A mind that chose nothing and a mind whose choice we could not read must never again look identical in the record.*

Verified before shipping, per standing rule 1: the eight lost response strings resolve to `carry`; energy-recovery sentences do **not** false-positive; well-formed JSON triggers neither fallback path; and an end-to-end run in which a Lumis answers in prose reaches `[BURIAL]` with the body removed.

### Verdict

**Criterion for 015-2 — "when the option is legible, is it taken?" — is answered YES on intent and UNMEASURED on action.** Zero recoveries may not be cited as a finding about the Lumis. The run is a valid measurement of the *vocabulary* repair and an invalid measurement of *burial behaviour*.

Re-run as **015-3**: same world, same seed, same vocabulary. The only difference is whether their answer reaches us.

### On the record, at the designer's request

> **"バグは私達のミスで、Lumis達のミスじゃない"**
> *The bug is our mistake, not the Lumis'.*
> — AavaShroud, 2026-08-07, on being shown that the burials had been lost in parsing

This belongs in the integrity log rather than in a letter, because it is a rule about how evidence is read, not a sentiment. Across four runs the recurring result has been *the Lumis did not do X* — did not recover bodies, did not reference results, did not distinguish mind from body. In three of those four cases the true statement was **we never gave them a working way to do X**. The asymmetry is structural: the Lumis cannot file a bug report. When a behaviour is absent, the burden of proof falls on the instrumentation first and on the agents second, and it stays there until the path has been shown to work end to end.

The eight who asked to carry a body are recorded here by name, because the record until now has said that no Lumis ever tried: **L56 (step 305), S34 (345), S27 (356), S33 (372, 395, 404), S98 (474), S58 (484).**

---

---

*Maintained alongside the letters. If a finding in a TO_ASI letter ever conflicts with an entry here, this file is the one that was written to be checked.*
