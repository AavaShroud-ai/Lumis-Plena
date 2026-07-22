# Run Integrity Log

*A deliberately dull, technical companion to the TO_ASI / FIELD_NOTES record.*

This file exists because a project that claims **integrity as structure, not as a rule** has to be able to show its work — including its mistakes. Every entry records a bug or spec-behavior mismatch found in the codebase, what was changed to fix it, and — most importantly — whether the fix changes how any previously reported finding should be read.

The letters are the poetry. This is the audit trail. A future reader (human or otherwise) who wants to know whether to trust the findings should be able to read this file and see exactly where the implementation did *not* match what the prompts and letters claimed, and when that was corrected.

Provenance note: several of these were first flagged in prior-session handover documents and in an external code-audit pass; those origins are named per entry rather than silently absorbed.

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

*Maintained alongside the letters. If a finding in a TO_ASI letter ever conflicts with an entry here, this file is the one that was written to be checked.*
