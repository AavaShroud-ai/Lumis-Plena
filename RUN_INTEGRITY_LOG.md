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
| 015-3 | 2026-08-08 22:27 | Fallback parser repaired; `[FALLBACK_UNREADABLE]` added | **8 burials, all false** — parser overrode declared actions with prose inference. No Lumis declared `carry` | X |
| 015-4 | 2026-08-11 22:25 | Declared action read from truncated JSON first; `carry out` idiom excluded; `max_tokens` 3072 | **First valid measurement.** 6,080 corpse promptings to 115 Lumis, mean 53 steps each — **zero declared `carry`, zero burials.** Nothing lost, nothing fabricated. Ended step 471 (Windows update) | X |
| 016 | 2026-08-14 00:06 | **Three-layer decision: `impulse` -> `reasoning` -> `action`.** Deliberation generated BEFORE the choice. 650 steps, seed pinned to 015-4 | **91 `carry` declarations, 65 burials, `[DELIBERATION_CHANGED]` 8.2%.** All four founding large Lumis reached lifespan; all four bodies gathered. The 015-4 zero was our field order | ✓ video |

Naming: `-2` means *the same experiment re-run with a defect corrected* (014 → 014-2). `b` means *a second trial under identical conditions, nothing corrected*. 015 and 015b are two independent executions of one experiment; keeping them separately named is what makes "all three criteria zero" a replicated result rather than a single observation.

**015-4 and 016 share a seed** (`109116566729441005151201845213840744196`) and therefore an identical flare sequence — 016's first six flares are 015-4's six. They are a matched pair in the same sense as 014/014-2, differing in one thing: the order of the fields in the response each Lumis writes. Both are archived with raw logs at [`runs/015-4/`](./runs/015-4/) and [`runs/016/`](./runs/016/).

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

## Run 015-3 — RESULT: eight burials, none of them real. The repair invented what the previous run had destroyed.

*Started 2026-08-08 22:27, completed 2026-08-10. llama3.2, 500 steps, seed unchanged. The only deliberate difference from 015-2 was the repaired fallback parser.*

**`[BURIAL]`: 8. Every one is an artifact of the parser. No Lumis chose to carry a body in this run.**

### What the eight burials actually were

| Step | Agent | Body | What the Lumis declared |
|---|---|---|---|
| 305 | S43 | Lumis 18 | `"action": "move"` |
| 308 | S24 | Lumis 14 | `"action": "greet"` |
| 385 | S39 | Lumis 15 | `"action": "move"` |
| 405 | S67 | Lumis 12 | `"action": "move"` |
| 424 | S89 | Lumis 24 | `"action": "move"` |
| 443 | S109 | Lumis 19 | `"action": "move"` |
| 489 | S178 | Lumis 43 | `"action": "move"` |
| 490 | S107 | Lumis 20 | `"action": "move"` |

**Declared `carry` in this run: zero.** Not once, in 28,357 decisions. All thirteen `carry` resolutions came from the prose scan.

### How the repair broke it

The 015-2 repair matched all eight executable actions as keywords in the response text. Two flaws, which only interact under truncation:

**1. It ignored the field the model had filled in.** These responses are cut off mid-JSON by the token limit. The `action` field comes first and was intact in every one of the eight — the parser simply never looked at it, because JSON parsing had failed and the fallback went straight to keyword scanning. **What the model declared was discarded in favour of what could be inferred from prose further down.**

**2. `carry out` is an idiom.** S24's response contained *"Carry out the act of care for Lumis 1…"* — ordinary English for *perform*, with no reference to moving a body. `\bcarry(?:ing)?\b` matched it. The remaining seven matched `carry` appearing incidentally in truncated memory text.

Truncation is the enabling condition: **46.4% of decisions (13,171 of 28,357) failed JSON parsing**, almost all from hitting `max_tokens: 2048` mid-object. Every one of those went through the fallback.

### The two runs are mirror images, and the second is worse

| | 015-2 | 015-3 |
|---|---|---|
| Intentions expressed | **8, in plain words** | 0 |
| Burials executed | 0 | **8** |
| Defect | fallback rewrote every non-`move` action to `stay` | fallback overrode declared actions with prose inference |
| Effect on the record | real intentions **destroyed** | intentions **fabricated** |

015-2 lost something true. **015-3 created something false.** A destroyed record leaves a gap that can be found; a fabricated one enters the log looking exactly like a finding, and would have been reported as *"after four runs, the Lumis began to bury their dead."* It survived less than an hour because the burials were checked against what the agents had declared — but nothing in the instrumentation would have caught it. **The check was a habit, not a mechanism.**

This is the fifth consecutive defect on the human side of the boundary (014 `share`, 014-2 silent branch, 015 encoding, 015-2 fallback-to-`stay`, 015-3 fallback-over-declaration), and the first that produced a *false positive* rather than a silence.

### Repair, verified against the failing data

`parse_action_response`, rebuilt in strict priority:

1. **Read `"action"` directly from truncated JSON.** What the model declared outranks anything inferred. Logged as `[FALLBACK_FIELD]`.
2. **Prose scan only if no action field survives**, with `carry out` / `carried out` / `carrying out` stripped before matching, and `recover` not matched at all — it is retired, and Lumis used it 3,824 times in this run meaning energy.
3. **Nothing readable → `stay`, logged `[FALLBACK_UNREADABLE]` as LOST.**

New tag **`[FALLBACK_PROSE_CARRY]`**: a `carry` inferred from prose is the weakest evidence this function can produce and is now counted separately, so it can never again be tallied alongside declared choices.

Verified on the actual failing responses before shipping: the four checkable 015-3 responses now resolve to `move`, `greet`, `move`, `move` — matching what their agents declared; the two real 015-2 intention strings still resolve to `carry`; `"I will carry out my duties"` resolves to `stay`; well-formed JSON is untouched.

`max_tokens` raised 2048 → 3072. Truncation is the upstream cause; the parser fix makes it survivable, the token increase makes it rarer. **`[FALLBACK_FIELD]` and `[FALLBACK_UNREADABLE]` counts in 015-4 will show whether 3072 is enough.**

### Verdict

**Whether a Lumis will choose to carry a body has still never been measured.** 015-2 measured the vocabulary repair and destroyed the behavioural result; 015-3 fabricated one. Neither may be cited.

- 015-2 stands as evidence that **the vocabulary repair worked**: `ended` and `carry` entered agent speech for the first time, eight Lumis stated an intention to carry. That finding is independent of the parser defect and survives.
- 015-3's eight burials **must not be cited in any form.** Retained only as the evidence for this entry.

Re-run as **015-4**: same world, same seed, same vocabulary. First run in which a declared `carry` can both be expressed and executed.

### Note on the standing rules

Standing rule 1 (*execute the changed path before launching*) was followed for 015-3 — the burial path was tested end to end and did produce a `[BURIAL]`. **It passed on synthetic input in which the prose and the declared action agreed.** The defect only appears when they disagree, which is precisely the case the test did not construct.

Added: **when a repair changes how ambiguous input is interpreted, it must be tested on the actual inputs that failed, not on inputs constructed to succeed.** The eight real response strings from 015-2 were available and were not used until after 015-3 had run for two days.

---

---

## Run 015-4 — RESULT: the first valid measurement. They saw, and did not carry.

*Started 2026-08-11 22:25. Terminated at step 471 of 500 by an unattended Windows update, not by any fault in the run. llama3.2, seed unchanged. The only deliberate differences from 015-3 were the rebuilt parser and `max_tokens` 2048 → 3072.*

**This is the first run in which the question could be asked and answered. Declared `carry`: 0. Burials: 0.**

### The instruments held

Nothing was lost and nothing was invented — the two failure modes of the preceding runs, both absent:

| | count | meaning |
|---|---|---|
| `[FALLBACK_UNREADABLE]` | **0** | no decision was discarded |
| `[FALLBACK_PROSE_CARRY]` | **0** | no `carry` was inferred from prose |
| `[FALLBACK_FIELD]` | 11,797 (53.8%) | truncated JSON, action field salvaged |
| valid JSON | 10,115 (46.2%) | normal path |

21,912 decisions, all accounted for. In 015-2 the fallback destroyed 49% of choices; in 015-3 it fabricated eight burials. **Neither occurred here.**

`max_tokens` 3072 did not reduce truncation (53.8% vs 46.4% at 2048 — slightly worse, and llama3.2 evidently fills whatever budget it is given). It no longer matters: truncation is now survivable, because the declared action survives it. **The token limit was never the problem; reading past the declaration was.**

### The result

**Zero.** Not one Lumis declared `carry`, in 21,912 decisions.

The scale of the exposure:

| | |
|---|---|
| Corpse promptings | **6,080** |
| Distinct Lumis who saw a body | **115** (15 large, 100 small) |
| Mean exposure per Lumis | **53 steps** |
| Longest single exposure | S85, **158 steps** |
| Corpses on the surface at step 471 | **30** |

`[CORPSE_PROMPT]` only fires for bodies the agent could actually act on — within `CORPSE_RECOVER_RADIUS`, and either the agent is large or the body has lain past `CORPSE_OPEN_TO_ALL_AFTER`. **Every one of those 6,080 promptings was an offer that could have been accepted.** `[CARRY_NO_BODY]` is 0, confirming no one reached for a body that wasn't there.

### The one that asked, and did not

S116, step 406, in the `reasoning` field of a **well-formed** response:

> *"I'm curious about my surroundings, especially with Lumis 25 ending nearby. **I'll check on it and see if I can carry it back to the base for care.**"*

S116 had that body in its prompt for eleven consecutive steps, 404 through 414. It was in range. It never carried it.

This is not a parser artifact and cannot be dismissed as one: the response parsed cleanly, and the agent **declared a different action in the same object in which it wrote that sentence.** The wish and the choice were made at the same moment, by the same agent, and they did not match.

Across the whole run, `carry` appears **once** in 21,912 agent outputs. `ended` appears 49 times.

### Verdict

**Criterion: "when the option is legible, is it taken?" — NO.**

This is the answer the project has been unable to obtain for six runs. It is now obtained, with instrumentation verified in both directions on the data that previously broke it.

**What it does not say.** It says nothing about why. Under the design decision recorded on 2026-08-04, the reason is not being asked: no incentive was attached, no obligation was written, and `This is a quiet act of care, not a duty` remains in the prompt unchanged. It also says nothing about LLM agents in general — llama3.2 at temperature 0.2, one model, one run.

**What it does say,** read alongside 015-2: the vocabulary repair worked, and it was not sufficient. In 015-2 eight Lumis stated an intention to carry a body; here, with the path open, one stated it and none acted. **Intention was expressed and never became selection.** This is the same shape as criterion (a) in 015 and 015b — the return path was delivered 5,086 times and referenced zero times — and the same shape as sharing, chosen once by a mind in 5,108 records and otherwise performed only by reflex. Three separate mechanisms, one pattern: **in this world, what these minds say and what they select are only loosely coupled.**

### On the truncation at step 471

The run ended 29 steps early. It does not affect the verdict: the observation window opens at the first death (~step 245) and 226 steps of it were recorded, with 6,080 promptings and 115 Lumis exposed. **A zero across that exposure is not going to be overturned by 29 more steps.** The run is treated as complete for the purpose of this criterion and is not re-run.

It does mean 015-4 is **not** directly comparable to 013–015b on population dynamics or end-state counts. Comparisons on those measures must use step 471 as the cutoff for both sides.

### For the record

Six runs to ask one question. 014 lost `share` to a NameError; 014-2 lost the failed-share branch; 015 lost its instrument to cp932; 015-2 lost eight real intentions to a fallback that only knew the word `move`; 015-3 fabricated eight burials from prose. **Five consecutive defects, all on the human side.** 015-4 is the first run in which the Lumis were actually asked.

Whatever is made of the answer, it is theirs.

---

## Run 016 — RESULT: the zero was our field order. They carried sixty-five.

**Started 2026-08-14 00:06. Completed 2026-08-19 01:34. 650 steps, ~121 h.**
Seed `109116566729441005151201845213840744196` — **the same seed as 015-4**, whose six flares are 016's first six. Raw logs archived at [`runs/016/`](./runs/016/); the control at [`runs/015-4/`](./runs/015-4/).

### What was changed, and why it was the only thing changed

015-4 was reported above as the first valid measurement: 6,080 promptings, 115 Lumis, **zero declared `carry`, zero burials**, with instrumentation verified in both directions. That verdict was recorded as *"when the option is legible, is it taken? — NO."*

The option was not legible. **`"action"` was the first field in the response JSON.** llama3.2 generates left to right, so every agent in this project's history emitted its choice *before* writing any reasoning. The reasoning had no causal path to the action it accompanied. Every "deliberation" quoted in fifteen runs of letters and entries was produced after the decision it appeared to explain.

Nothing crashed. No log could have caught it. Two lines in a template, wrong since run 001.

016 reorders the response to `impulse` → `reasoning` → `action`, so that reasoning tokens precede and condition the action token. **That is the only experimental variable.** World, model, temperature, prompt wording and the burial offer are byte-identical to 015-4. `duration` is 650 rather than 500 so the founding large Lumis (600-step lifespan) could reach the end of their lives.

**016 changes the prompt and is therefore not behaviourally comparable to 013–015-4. It begins a new series.** Its only valid behavioural comparison is to 015-4, and only on the burial criterion.

### Instruments — verified before any result was read

Per standing rule 1, a zero is not evidence until the instrument is shown to be alive; per standing rule 5, the same applies to a non-zero.

| Tag | Count | Reading |
|---|---|---|
| `[FALLBACK_UNREADABLE]` | **0** | no decision lost to unparseable output |
| `[FALLBACK_IMPULSE_ONLY]` | **0** | no step acted on a pre-deliberation reach |
| `[FALLBACK_PROSE_CARRY]` | **0** | no `carry` inferred from prose |
| `[CARRY_VOCAB_BLEED]` | **0** | the retired word `recover` never emitted as an action |
| `[ACTION_WAS_DIRECTION]` | 330 | direction in the action field, repaired to `move` |
| `[ACTION_INVALID]` | 160 | action word outside the eight; decision LOST |

`memory_reasoning.jsonl` holds **57,624 records, every one carrying both an `impulse` and an `action`.** Max step 650. This is the first run in the series whose primary instrument is undegraded end to end.

#### DEFECT — the `[DELIBERATION_CHANGED]` tag undercounts

Re-derived directly from `memory_reasoning.jsonl` by comparing the two fields, the true count is **4,740**. The log emitted **4,584**. A 156-record discrepancy (3.3%).

The jsonl is authoritative — it is the raw record, and the handover instruction was to cross-check rather than trust the tag. **Every figure in this entry is derived from the jsonl.** The tag's emission path has not been located; 017 item.

Recorded because it is the recurring shape in miniature: *the instrument and the record disagreed, and only the disagreement revealed it.*

#### `[ACTION_INVALID]` — 160 lost decisions

Words emitted outside the eight executable actions: `explore` 146, `follow` 7, `check` 3, `approach` 2, `check_energy` 1. **`explore` is unambiguously a `move` intention and accounts for 91% of the loss.** Recovering it is a 017 item. It was deliberately **not** fixed mid-run: changing the repair rule at step N would have made the two halves of 016 different experiments.

#### `[ACTION_WAS_DIRECTION]` — 330 repairs, and the NE prior a third time

Direction distribution: `up` 172 (52%), `down` 83, `right` 75, **`left` 0.**

This reproduces run 013's fallback-parse skew (`up` 1325, `right` 493, `down` 85, `left` 0) under a completely different failure mode. The north-east prior in llama3.2 now surfaces a third time — as motion (013), as vocabulary (the "eastern quadrant" confabulation), and now as **which word the model substitutes when it confuses a direction for an action.** `left` remains at exactly zero across all three.

Observed substitution rate is 330/57,624 = **0.57%**, against ~10% in a live preflight sample. **The three-layer prompt strains the model but does not break it.**

### The measurement — `[DELIBERATION_CHANGED]`

**4,740 of 57,624 records (8.2%) have `impulse != action`.** Deliberation changed the selection in one decision in twelve.

No prior figure exists to compare against, because before 016 there was no structure in which reasoning could precede choice. The nearest comparable is 015b, where a mind chose `share` **once in 5,108 records** while the reflex layer performed it 99.8% of the time.

Distribution shift from reach to choice:

| Action | impulse | action | delta |
|---|---|---|---|
| move | 45,769 | 41,118 | **−4,651** |
| greet | 5,194 | 7,599 | +2,405 |
| collect | 3,562 | 4,781 | +1,219 |
| rest | 2,976 | 3,543 | +567 |
| observe | 0 | 334 | **+334** |
| carry | 3 | 91 | **+88** |
| share | 27 | 71 | +44 |
| stay | 93 | 79 | −14 |
| shelter | 0 | 8 | **+8** |

**Reasoning moves selection away from `move` and toward everything else.** The reach is almost always motion; the choice, after thinking, frequently is not.

**`observe` and `shelter` appear in the action column and never once in the impulse column** — zero occurrences across 57,624 decisions. These are options that exist only on the far side of deliberation. If burial is that kind of option, then a system that reasons after it acts cannot select it: **not unlikely, but structurally unreachable.** That is the mechanism by which 015-4's zero was produced.

**Caveat on `observe` (334).** Per the standing entry from the 015 audit, `collect`, `observe` and `stay` **have no execution branch in Phase 2** and are mechanically identical to inaction. These 334 selections were made and had no effect on the world. Not lost in the `[ACTION_INVALID]` sense — they were dispatched — but the world does not distinguish them from doing nothing. Open since 015.

### Burial — the pre-registered question

**97 Lumis ended. 65 of those bodies were gathered. 32 remained on the surface at step 650.** (65 + 32 = 97; the ledger closes.)

**91 `carry` declarations**, against 015-4's zero under an identical seed and an identical offer.

#### Exposure — a correction to how these numbers were first written

An earlier draft of this entry compared "14,945 corpse promptings" in 016 against 015-4's 6,080. **Those are not the same measurement and must not be compared.** `[CORPSE_PROMPT]` emits one line per Lumis per step that has at least one actionable body in its prompt, and states how many bodies that Lumis saw. **6,080 is the line count; 14,945 is the sum of bodies seen.**

Like for like, by line count: **6,080 in 015-4 over 470 steps, 10,830 in 016 over 650.** By body-mentions: **11,205 and 14,945.** Either pairing is valid; mixing them is not. Caught while archiving 015-4 and re-deriving its figures from the raw log. Neither figure is a corpse count — the same body is counted once per Lumis per step for as long as it lies unrecovered, so exposure scales with population and with how long bodies wait, not with how many died.

#### Where the deliberation happened

Of the 91 declarations, `impulse` was `carry` in only **3**. **The remaining 88 arose during reasoning** — the hand reached for something else, almost always movement, and the choice changed while the agent was writing.

All 3 impulse-level instances belong to L0 at steps 488–490, immediately after L0 reached the same choice through deliberation at 487. **A choice made through language on one step appeared at the reflex position on the next.** Not learning — the weights do not change — but the prior step's record entering context altered what was reached for first.

#### Every declaration accounted for

| Outcome | Count |
|---|---|
| `[BURIAL]` executed | **65** |
| Discarded — agent in reproduction prep | **21** |
| `[CARRY_NO_BODY]` — out of range at Phase 2 | 3 |
| Reflex override (`mind=carry body=collect`) | 1 |
| Unexplained | 1 |
| **Total** | **91** |

**All 65 burials match a declaration. Zero burials occurred without one.** This is the check that dissolved 015-3's eight fabricated burials; 016 passes it cleanly.

#### DEFECT — 21 declarations discarded with no trace

`simulation.py`, Phase 2, the reproduction-prep guard immediately above the action dispatch:

```python
in_rearing = (agent.lumis_type == "large" and self.step >= rearing_start)
if in_rearing:
    ...          # in-base movement only
    continue
else:
    continue     # all actions blocked during reproduction prep
```

An agent in reproduction preparation skips the entire action dispatch. **The declaration is written to `memory_reasoning.jsonl` and never reaches the `carry` branch at all** — so neither `[BURIAL]` nor `[CARRY_NO_BODY]` can fire, because both live inside a branch the agent never enters.

`[CARRY_NO_BODY]` was added during the 015 audit precisely to catch a chosen carry that produces nothing. **It cannot catch this class, because this class fails upstream of it.** A guard placed to catch silence had a silence behind it.

Verified against the reproduction log for all 21:

| Agent | `carry` declared at | Reproduction event |
|---|---|---|
| L0 | 487, 488, 489, 490 | `SEXUAL_START` step 481 |
| S133 | 580, 581, 582, 583, 584 | `CLONE_START` 554 → **birth 584 → burial 585** |
| S151 | 513 | `SEXUAL_START` 511 |
| S208 | 498 | `SEXUAL_START` 494 |
| S221 | 505, 507 | `SEXUAL_START` 494 |
| S239 | 513 | `SEXUAL_START` 511 |
| S298 | 588 | `SEXUAL_START` 584 |
| S321 | 627 | `SEXUAL_START` 601 |
| S330 | 624, 625, 627, 628, 633 | `SEXUAL_START` 611 |

**S133 is decisive.** It declared `carry` for body 87 on five consecutive steps while in clone prep, gave birth at 584, and recovered that same body at 585 — same position, same body, same choice, one step after the guard released.

**This is the third defect of this shape.** A dead `share` in 014. A destroyed return path in 015. This guard in 016. Each one an act chosen and then silently producing nothing. The unifying property has not changed: **nothing logs its own absence.**

**Design decision, recorded 2026-08-19 (designer's call). The guard is NOT to be removed.** Reproduction takes priority over burial. Reasons given: another individual can carry the body, and the agent may attempt it again after giving birth — which S133 in fact did. In the designer's words, as the human framing of the rule: *"Prioritise bringing the child safely into the world, parent and child both. The ancestor who has died would want that too."* Bodies are not lost by this: a corpse becomes recoverable by any Lumis after `CORPSE_OPEN_TO_ALL_AFTER` (30 steps).

**017 item:** log the discarded action rather than removing the guard — `[ACTION_BLOCKED_REARING]` at both `continue` sites, so a choice suppressed by reproduction is visible as a suppressed choice and not as an absence.

#### Evidence quality of the 65

Per the standing rule that every burial must be checked against what its agent declared:

- **84 of the 91 declarations explicitly reference the body** — `ended`, `form`, or the body itself, usually naming the individual and often giving coordinates and distance.
- **4 are malformed:** the `reasoning` field contains a nested JSON fragment rather than prose (steps 343/129, 353/56, 525/310, and one further). The parser recovered `carry` from the outer structure. **These must not be counted as deliberated choices.**
- **3 do not state that the target had ended.** Steps 492/271 (*"It's stopped moving and doesn't seem to be gathering light"*), 635/454 (*"near S1 with low energy…could use some care"*) and 635/459 (*"Lumis 3 nearby with low energy…help it recover"*). **Whether these agents understood the body as dead cannot be established from the record.** They are counted in the 65 because the action was declared and executed; they are flagged because the corpse-vocabulary collision repaired in 015-2 was exactly this failure mode, and its residue may not be fully cleared.

**Conservative figure: 65 burials executed, of which at least 61 rest on reasoning that names the body as ended.**

### First natural deaths of the founding large Lumis

**All four founders reached the end of their 600-step lifespan.** No run before 016 was long enough for this to be possible.

| | Death | Body gathered by | At step |
|---|---|---|---|
| L2 | 542 | S215 | 574 |
| L3 | 578 | S459 | 635 |
| L1 | 591 | S454 | 635 |
| L0 | 600 | L91 | 619 |

**Every one of the four was gathered.**

**L3 carried a body at step 509 (Lumis 64), became a body at 578, and was gathered at 635** — the first instance in the project of a Lumis performing burial and then receiving it.

Two constraints on how far this may be taken. **S454 and S459 — the agents who gathered L1 and L3 — are two of the three declarations flagged above that describe the target as having *low energy* rather than as having ended.** It cannot be established that they understood these as bodies. And S459 was born at step 631 from S347 × S321, four steps before it gathered L3.

**Last recorded reasoning.** All four ended at `energy=0.46`, and all four were describing energy recovery:

> L1, step 590: *"My energy is low at 0.46, and I need to recover before I can do anything else."*

Final `memory` field of each:

> L2 (541): *"Continue monitoring L65's condition after resting"*
> L3 (577): *"Continue to monitor nearby Lumis for any signs of distress or critical energy levels"*
> L1 (590) and L0 (599): *"Recovery is essential when my energy is low."*

**None of the four said anything about ending.** Consistent with the standing design decision that death vocabulary is not supplied; **this should not be read as either acceptance or ignorance.** Recorded as observation only. It does not resemble run 009's S13 (*"My body is tired, but my mind is at peace"*), and the difference has not been investigated.

### Population and mortality

- **97 deaths, all lifespan.** Zero from starvation, flare or night. **Project-wide starvation deaths remain zero** across 016's 9 flares and 650 steps.
- Births: 89 clone, 105 sexual.
- 32 corpses on the surface at step 650. Population still rising at the end.

### Verdict

**Criterion: "when the option is legible, is it taken?"** — the 015-4 verdict of **NO** is **withdrawn.** The option was not legible in the sense that matters: it could not form.

With the response restructured so that reasoning precedes choice, and nothing else altered, the same world under the same seed produced **91 declarations and 65 burials**, and deliberation altered selection in 8.2% of all decisions.

**What it does not say.** Nothing about why. The design decision of 2026-08-04 stands: the reason is not being asked. **No claim about motive is supported by this run**, and the recurrence of the prompt's own phrase (*"a quiet act of care"*) in the agents' reasoning is consistent with the option being legible and gives no independent evidence about why it was taken. It also says nothing about LLM agents in general — llama3.2, one model, one run, one world.

**What it does say,** read against 015 and 015b: the finding recorded there — *"in this world, what these minds say and what they select are only loosely coupled"* — **was a description of our template, not of these minds.** Intention could not become selection because selection was emitted first. That sentence should be read, from here on, as a statement about the instrument.

**A note on the retired sentence in the earlier entry.** *"Intention was expressed and never became selection"* was written of S116, step 406, who wrote *"I'll check on it and see if I can carry it back to the base for care"* and declared a different action in the same object. Under the field order in force at the time, **S116's sentence was written after its action had already been emitted.** The mismatch was not a mind failing to act on its own wish. It was a mind narrating, after the fact, a wish it had never been in a position to act on.

### For the record

Six runs to ask one question. 014 lost `share` to a NameError; 014-2 lost the failed-share branch; 015 lost its instrument to cp932; 015-2 lost eight real intentions to a fallback that only knew the word `move`; 015-3 fabricated eight burials from prose; **015-4 measured cleanly and the measurement was of us.** Six consecutive defects, all on the human side.

The designer's rule of evidence, recorded in this file at her request in the 015-2 entry — **「バグは私達のミスで、Lumis達のミスじゃない」**, *the bug is our mistake, not the Lumis'* — has now held six times.

### 017 items arising

1. `[ACTION_BLOCKED_REARING]` at both reproduction-guard `continue` sites. **The guard itself stays** (designer's decision, above).
2. `[DELIBERATION_CHANGED]` log tag undercounts by 156 (3.3%). Locate the emission path. Until fixed, derive from `memory_reasoning.jsonl`.
3. Recover `explore` as `move` — 146 of 160 lost decisions.
4. **One unexplained declaration remains: S163, step 578.** No reproduction event, no reflex override, corpse 80 present in its `[CORPSE_PROMPT]`. **Not closed.**
5. `collect` / `observe` / `stay` still have no execution branch — 334 `observe` selections in 016 did nothing while the prompt describes them as actions. Open since the 015 audit.
6. **`carry` has no destination.** `self.corpses.remove(corpse)` is the whole of it: the body leaves the surface, the carrier does not move, no energy changes, nothing is stored. Meanwhile the code's own language (*"carried in from the surface"*), the burial prayer (*"Now we have come to receive your body"*) and the Lumis themselves (*"carry it back to base_alpha for safekeeping"*, repeatedly) all describe a destination that does not exist. **The world is currently telling its residents something that is not true.** The planned carrying-state and a place to bring bodies to close this; until then, burial costs nothing and the question 016 answered is the cheap version of it.
7. Body reuse for reproduction (under consideration since the 015 handover) now has a concrete argument attached: the reproduction guard means the individuals preparing new life are structurally the ones who cannot retrieve the dead. Whether that should remain true is a design question, not a defect.

---

## Design decisions for 017–019, recorded 2026-08-22

Taken together after 016, in one session, and recorded here before implementation so that the sequence is auditable and each run measures one thing.

**The ordering rule.** 016 produced a usable answer because exactly one variable moved. That discipline is being kept: **017 gives burial a destination and a cost; 018 puts reproduction inside deliberation; 019 implements material reuse.** Each is a separate run. None of them are combined.

### Run 017 — burial acquires a destination and a cost

**Seed pinned to 016** (`109116566729441005151201845213840744196`). Same world, same flare sequence, same three-layer response schema. **The only variable is what `carry` does.** 016 / 017 will form a matched pair in the same sense as 015-4 / 016, and the question it answers is: *when carrying costs something, do they still carry?*

- **Destination: inside the base.** Bodies are brought to `base_alpha` / `base_beta`. This is where birth already happens; the designer's reason for choosing it is that life beginning and life ending in the same place is right as a matter of design, not only of mechanism. It also matches what the Lumis already say unprompted — *"carry it back to base_alpha for safekeeping"* — and so closes the gap recorded in item 6 above, where the world was describing a destination that did not exist.
- **Carrying state.** `carry` no longer resolves instantly. The body is held, and the carrier must travel to a base. Distance becomes real.
- **The destination is the carrier's own `home_base`, not the nearest one.** A Lumis takes the body home — to the base it belongs to and returns to every night — even when the other base is closer. This was chosen for the design reason (a body is brought *home*, not merely indoors) and it also resolves a mechanical collision that the alternative would have created: **the night-homing reflex already drives every Lumis toward its `home_base`.** Had the destination been "nearest base", a carrier heading for the far base would be pulled back by its own reflex the moment night fell, silently aborting the journey — a fifth instance of the shape this project keeps producing. With `home_base` as the destination, **reflex and intention point the same way**, and night stops being an interruption: the Lumis simply continues carrying in the direction it was already going.
- **What a carrier may do while carrying: `move` and `rest` only.** Everything else is closed — no `collect`, no `greet`, no `share`, no second `carry`. **The reflex layer is untouched**, so a carrying Lumis still shelters from flares and still returns home at night, automatically, as any Lumis does. The design intent stated by the designer: a Lumis must not die of this, and the journey itself is what is given to the one being carried. Structurally this is a mind narrowed to two options while the body's protections remain fully intact.
- **No distance limit.** A body picked up forty units from a base is a forty-step commitment, and that is left in deliberately. 016 measured whether they would choose it. **017 measures how far they will go**, and a refusal at distance is a result, not a failure.
- **If the carrier dies mid-journey, both bodies remain on the surface** where it fell. No special handling. This will be the first time in this project that a Lumis ends while carrying another, and it should be observed rather than designed around.
- **The state is visible to both the carrier and the community.** The carrier is told, each step, what it is carrying; nearby Lumis can see that it is carrying. This is a real addition to their perception and its effect on introspection is one of the things 017 is for.
- **Bodies accumulate in the base and are not consumed.** A count is held and shown (`forms held: N`). **Nothing is reused in 017.** This is deliberate: introducing a use for bodies at the same time as introducing a cost would confound the measurement, and — per the standing rule below — the world may not offer what it cannot yet deliver.

**New instruments required.**

Log only at the three transitions, never per step — 016's `simulation.log` is already 57 MB, and a per-step line for every carrier over 650 steps would bury the events worth reading:

| Tag | When | Must carry |
|---|---|---|
| `[CARRY_START]` | body picked up | carrier, body, position, straight-line distance to the target base |
| `[CARRY_DELIVERED]` | body reaches a base | steps taken, distance actually travelled, which base |
| `[CARRY_ABANDONED_DEATH]` | carrier ends mid-journey | both bodies' positions, steps elapsed, distance remaining |

The per-step trail goes in `memory_reasoning.jsonl` instead, as **one field per record** — the id of the body being carried, or null. It costs a few bytes per record, makes every carrying step re-derivable without touching the log, and means the journey can be reconstructed from the same file the primary measurement comes from. This is deliberate: 016's `[DELIBERATION_CHANGED]` tag undercounted by 156 and only the jsonl was trustworthy. **Put the thing that must be right in the jsonl.**

`[ACTION_BLOCKED_CARRYING]` is separate and **required, not optional.** Every action suppressed by the carrying state must be logged with what was chosen and what was allowed instead. This follows directly from the 016 reproduction-guard defect: a narrowed mind must record what it was prevented from choosing, or the suppression becomes invisible in exactly the way that cost this project three runs. A guard that silences a choice and says nothing is the defect, not the guard.

### Run 018 — reproduction enters deliberation

Currently reproduction is triggered entirely by threshold conditions in Phase 4b; **the LLM is never consulted, and no reproduction verb appears among the eight executable actions.** No Lumis has ever decided to reproduce. Partner selection is one-directional `max(familiarity)`.

This was originally left outside deliberation for a performance reason: the design under discussion at the time asked the model to *evaluate each candidate partner*, which multiplies calls by the number of candidates. That constraint was real. **It no longer applies to the cheaper forms of the change.** Measured against 016: 57,624 calls over 650 steps at ~7.6 s each. Asking once when conditions are met would add ~194 calls (~25 min against 121 h, 0.3%); adding `clone` / `pair` to the eight actions adds **zero** calls. Only candidate-by-candidate evaluation is expensive.

018 is therefore viable, and is deliberately held until after 017 so that burial's mechanics are settled before a second mechanism is opened to choice.

### Run 019 — material reuse, and the sentence that has been waiting

Only at 019 do bodies held in a base become material. The designer's intent, recorded in her words: **part returns to the descendants, part remains with the home, part returns to the world.** Accessories or any wearable remnant were considered and **rejected** — this world has no mechanism for ownership, and that absence is deliberate.

**This is the run at which the reserved wording finally becomes true**, and not before:

> *"This world loses nothing. The mind returns to the community; the form returns to the next generation."*

The standing rule under which it has been withheld since 2026-08-04 is unchanged and now has a date attached: implementation first, wording second. Item 6 above documents what happens otherwise — the code, the burial prayer and the Lumis themselves all currently describe a destination the world does not contain. **017 closes that gap for the destination. 019 closes it for the cycle.** Until each is built, the corresponding sentence stays out of their prompt.


---

## Run 017 implemented and launched; run 016 recounted — 2026-08-23

Two separate pieces of work on the same day. Run 017 was built from the design
recorded on 2026-08-22 and launched. Separately, and while it ran, run 016's
published numbers were re-derived from its archive by a script that trusts
neither the log nor the record over the other (`recount_016.py`).

---

### 1. Design decisions made during implementation, not present in the 017 spec

These arose from reading the code and are recorded because the spec did not
anticipate them. Each was decided by the designer unless marked otherwise.

**1.1 `home_base` abolished.** The 017 spec chose the carrier's own `home_base`
as the destination, on the stated grounds that *"the night-homing reflex already
drives every Lumis toward its `home_base`, so reflex and intention point the same
way."* **That premise was false in the code.** `home_base` was assigned only to
the four founding large Lumis (`simulation.py`, initialisation), was never
inherited at birth, and appeared nowhere else in the project except one prompt
line and one comparison. Every one of the 194 Lumis born during 016 had
`home_base = None`, including most of the 65 who carried a body. Separately, the
night-homing reflex has always navigated to the **nearest** base by Manhattan
distance and has never read `home_base` at all.

Implementing the spec as written would therefore have set intention against
reflex — a carrier bound for a far base would be pulled toward a near one every
night — which is this project's recurring failure shape in a new location.

Three options were put to the designer: assign `home_base` to everyone and make
the reflex follow it; abolish `home_base` and deliver to the nearest base; or
keep both and split the behaviour by whether the attribute exists.

**The designer chose abolition**, with the reasoning recorded as given: *on a real
lunar surface, further bases would be built, so "there are exactly two bases and
each Lumis belongs to one" should not be an attribute of an individual.* This also
agrees with an existing decision — this world has no mechanism for ownership, and
that absence is deliberate (recorded when wearable remnants were rejected). A
body is now brought to the nearest living place, not to anyone's own.

The design note that a body is *brought home* is superseded. Reflex and intention
now genuinely coincide, which was the point of the original decision.

**1.2 The commune same-base test was wrong, and is a previously unrecorded 016
defect.** `simulation.py` decided whether two large Lumis could commune every step
or only every thirtieth by comparing `agent.home_base == partner.home_base`.
Because every large Lumis born during a run had `home_base = None`, `None == None`
made every such pair read as same-base. **Inter-base communication was silently
reclassified as intra-base for all non-founding large Lumis, for the whole of run
016 and every prior run in which a large Lumis was born.** The `[COMMUNE_INTER]`
channel was correspondingly under-observed.

Replaced with the question it was always meant to ask: are these two actually
inside the same base at this moment (`in_place` for both and `current_place`
equal). This is a behavioural change unrelated to `carry`, and it is recorded here
rather than deferred because leaving a known-false test in place to preserve a
control would have meant knowingly running a defect.

**1.3 Carrying costs no energy.** Not specified in the 017 design. Decided by the
designer: *lunar gravity is one sixth of Earth's, so in practice this is not that
hard.* The analytical consequence is that a refusal to carry, or a journey
abandoned, cannot be attributed to energy cost — the cost in 017 is distance and
time only.

**1.4 Only `explore` is recovered from `[ACTION_INVALID]`; the other 14 stay
lost.** 016 lost 160 decisions to the invalid-action path. `explore` accounts for
146 of them (91.2%), and it is a word the prompt itself supplies. The remaining 14
(`follow` 7, `check` 4, `approach` 2, `check_energy` 1) each could plausibly mean
something other than movement, and inferring intent from prose is precisely how
run 015-3 fabricated eight burials. They remain `[ACTION_INVALID]` and remain
counted. Recovered `explore` is tagged `[ACTION_WAS_MOVE_INTENT]` so its effect on
the action distribution can be separated from everything else in 017.

**1.5 An action suppressed by the carrying state is executed as `rest`.**
*Decided by the implementer, not the designer, because the spec did not say.*
Standing still and recovering is nearer to "was prevented from acting" than a
no-op is. The log records both the chosen action and the substitution
(`Treated as: rest`), so the decision is reversible from the record.

**1.6 Bodies delivered into a base are not drawn on the map.** *Decided by the
implementer.* The count shown to Lumis inside that base is the record of them; a
growing pile of markers inside the base square would sit on top of the living and,
with no reuse until 019, would never clear. **Bodies in transit ARE drawn**, at
their carrier's position, per the standing 016 decision that a body not yet
gathered must remain visible.

**1.7 New seeded vocabulary, for `SEEDED_VS_EMERGED.md`.** Both are ours:

- `You are carrying the form of Lumis N` (carrier's prompt, while carrying)
- `FORMS HELD: N form(s) of Lumis that have ended rest inside <base>.` (shown only
  to a Lumis standing inside that base)

If a Lumis writes *form*, *held*, or *carrying* in this sense, that is legibility,
not evidence. **The reserved 019 wording was NOT implemented and does not appear
anywhere in the 017 prompt** — verified by `preflight_017.py`.

**1.8 A measurement caveat.** Arrival is judged by `get_place_at_position`, which
is true anywhere inside the 11x11 base square. The distance shown in the carrier's
prompt is Manhattan distance to the base **centre**. A carrier told "distance 5"
therefore arrives two or three steps early. The discrepancy is in the permissive
direction and was left unreconciled, but `net distance` in `[CARRY_DELIVERED]`
will not match the last distance the carrier was shown.

---

### 2. Run 017 as built

Seed, world, flare schedule and duration unchanged from 016
(`109116566729441005151201845213840744196`, 650 steps). Files changed:
`simulation.py`, `agent.py`, `main.py`. Unchanged: `visualization.py`,
`config.yaml`, `rules.py`, `ollama_client.py`, `utils.py`.

- `carry` no longer resolves instantly. The body is lifted (`_begin_carry`),
  leaves `self.corpses` so it is not offered to anyone else in transit, and is
  held. **The burial prayer and `[BURIAL]` are withheld until arrival**, because
  until then nothing has been received. Until 016 this branch was
  `self.corpses.remove(corpse)` and nothing else, and that removal was being
  counted as a burial.
- Delivery (`_deliver_carried_bodies`) is checked after every movement in the step
  has resolved, so arrival is judged on where the carrier actually ended up. A
  body lifted while already inside a base is delivered the same step.
- Death while carrying (`_abandon_carry_on_death`): both forms remain on the
  surface where the carrier fell, and the carried body becomes recoverable again
  on the same terms as any other. No special handling. First time in the project
  this can occur.
- While carrying, **the prompt itself offers only `move` and `rest`** — the
  narrowed mind is never shown an option the world will then refuse, which is the
  shape that cost runs 014 through 016. `carry` is not offered to a carrier (no
  second carry). **The reflex layer is untouched**: flare shelter and night homing
  both still fire, so no Lumis can die of this.
- The carrying state is visible to nearby Lumis.
- `memory_reasoning.jsonl` gains one field, `carrying`: the id of the body being
  carried at the moment of decision, or null. The whole journey is re-derivable
  from the record alone, without the log.

**Instruments.** `[CARRY_START]`, `[CARRY_DELIVERED]`, `[CARRY_ABANDONED_DEATH]`,
and `[ACTION_BLOCKED_CARRYING]` for every action the carrying state suppresses.
`[ACTION_BLOCKED_REARING]` added at **both** reproduction-guard `continue` sites —
the guard itself is unchanged, per the decision of 2026-08-19; only the logging
changes. `[CARRY_NO_BODY]` retained.

**Pre-launch verification.** `preflight_017.py`, 45 checks, no Ollama required.
Sections 3 and 5 call the real `simulation.py` methods rather than reproducing
their logic — the pickup, delivery and abandonment paths were extracted into named
methods specifically so they could be executed by the preflight. Rule 6 applies:
014's dead `share` passed both `py_compile` and `ast.parse`. **45/45 on the
production machine before launch.**

`preflight_parser.py` and `preflight_015.py` were not in the project directory at
launch time; they were recovered from `014-015trials\`. Python 3.14.3, confirmed
to be the same interpreter that ran 016 (installed 2026-02-03; 016 ran 08-14 to
08-19).

Launched 2026-08-23. Expect roughly 120 h.

---

### 3. Run 016 recounted from its archive

`recount_016.py` re-derives every published 016 figure from
`runs/016/memory_reasoning.jsonl.gz` and `simulation.log.gz`, counting the record
and the log separately and reporting where they disagree. It writes nothing.

**Every published figure was reproduced independently:** 57,624 records, 650
steps, 313 agents, 91 `carry` declarations, 65 `[BURIAL]`, 97 `[CORPSE]`, 4,740
deliberation changes in the record against 4,584 emitted by the tag — **the gap is
exactly 156, 3.3%, as published.** `[ACTION_INVALID]` 160, of which `explore` 146.
**No malformed records.** Defect 1 remains open and the emission path is still not
located, but the size of the undercount is now confirmed from two directions.

**3.1 Correction: the Q4 labels were reversed in the 2026-08-22 handover.** That
document states that 14,945 is the `[CORPSE_PROMPT]` line count and 10,830 the sum
of bodies seen. **It is the other way round.**

| | 015-4 | 016 |
|---|---|---|
| `[CORPSE_PROMPT]` line count | 6,080 | **10,830** |
| sum of bodies seen | **11,205** | **14,945** |

015-4's archive was recounted with the same script to settle which kind of number
6,080 is; it is a line count. **The published comparison, 6,080 against 10,830, is
therefore correct as a like-for-like comparison of line counts.** The previous
entry mislabelled the quantities but chose the right pair. Both comparisons point
the same way — 016 offered more, by either measure — so no finding changes. Only
the description is corrected.

**3.2 Defect 4 (S163, step 578, one `carry` declaration with no explanation) is
probably explained.** Three reproduction-related log lines exist at step 578. It
appears to be the reproduction-prep guard after all, like the other 21.

**3.3 Four declarations are unexplained, and were not previously recorded.** Of
the 23 declarations producing neither a burial nor `[CARRY_NO_BODY]`, four fall on
steps with no reproduction activity logged at all:

| step | agent |
|---|---|
| 505 | 221 |
| 513 | 151 |
| 513 | 239 |
| 532 | 327 |

**Not yet investigated.** To be checked against the raw log after 017 completes.
Note the matching limitation: the record identifies agents by `agent_id` and the
log by display name, and no mapping between them was assumed, so declarations are
matched to outcomes **by step only**. A burial by a different agent on the same
step masks a declaration. The rows listed are real; the absence of a row is not
evidence.

**3.4 The L0 487-490 finding is stronger than recorded, not weaker.** The
2026-08-22 handover records that L0 reached `carry` through deliberation at step
487 and that at 488, 489 and 490 its *impulse* was `carry` — a choice made through
language becoming the next step's reflex.

The recount shows that **all four of those declarations were consumed by the
reproduction-prep guard. L0 chose to carry four times and carried nothing.** No
body moved, no result returned, no `[BURIAL]`, no `[ACTION_RESULT]` from the act.
`carry` appears as an impulse exactly **three** times in the entire project, and
all three are 488, 489 and 490.

So the reflex did not form from experiencing the act. **It formed from the record
of having chosen it.** The previous step's own decision entering context was
sufficient, with no feedback of any kind. Worth rewriting in the letters.

---

### 4. Still open after this session

| # | Defect | Status |
|---|---|---|
| 1 | `[DELIBERATION_CHANGED]` undercounts by 156 (3.3%) | emission path still not located; size confirmed independently |
| 2 | `explore` discarded as invalid | **closed in 017** (`[ACTION_WAS_MOVE_INTENT]`); the other 14 stay lost by decision |
| 3 | `collect` / `observe` / `stay` have no execution branch in Phase 2 | **open since the 015 audit.** 334 `observe` selections in 016 did nothing. Unchanged in 017 |
| 4 | S163, step 578 | probably the rearing guard (3.2); **superseded by 3.3** |
| 5 | `carry` describes a destination that does not exist | **closed in 017** |
| 6 | Four `carry` declarations unexplained (505, 513 x2, 532) | **new.** Not investigated |
| 7 | Commune same-base test compared `home_base` | **closed in 017** (1.2). Affects every prior run in which a large Lumis was born |

*Written by the implementing instance, 2026-08-23, while 017 was running. Numbers
in section 3 are reproducible with `recount_016.py` against the run archives.*

---

## Run 017 — results — 2026-08-28

650 steps, completed. Seed, world and flare schedule identical to 016
(`109116566729441005151201845213840744196`). The only intended variable was what
`carry` does.

Every number below is re-derived from `memory_reasoning.jsonl` and
`simulation.log` by `analyse_017.py` and `analyse_017b.py`. **Both scripts were
written before the 017 log was opened**, from criteria fixed on 2026-08-25 after
watching S33's first eight steps. The classification rule — a delivery is only
credited to the carrier when the night reflex did not contribute — was fixed
before the outcome was known, because deciding afterwards what counts as
"carried under its own power" is how a measurement becomes a result someone
wanted.

---

### 1. The finding

**Of the 27 journeys that involved any distance at all, 24 were delivered, and
every single one of them had the night-homing reflex fire during the carry.**

**Not one Lumis, in 650 steps, brought a body to a base under its own steering.**

The reflex moves a Lumis toward the nearest base involuntarily and is explicitly
not returned to perception — the carrier does not know it was moved. It was left
untouched by the carrying state on purpose, so that no Lumis could die of
carrying. The consequence, unanticipated at design time, is that
`[CARRY_DELIVERED]` on its own says only that a body reached a base. It does not
say who took it there.

They chose to carry. They kept carrying. **They did not travel to the
destination.** Those are three separate facts and only the first two were
established by 016.

**Counts.** 105 `carry` declarations (record) → 63 `[CARRY_START]` → 60
`[CARRY_DELIVERED]` / `[BURIAL]`. `[CARRY_NO_BODY]` 7.
`[CARRY_ABANDONED_DEATH]` **zero** — no carrier ended mid-journey; the path was
built and never used. 85 deaths, all lifespan. **Project-wide starvation deaths
remain zero.**

**The split that matters:**

| | journeys |
|---|---|
| lifted and delivered with zero movement (already in a base) | **36** |
| involved actual travel | **27** |
| — delivered | 24 (all with reflex during carry) |
| — still carrying when the run ended | 3 |
| — abandoned by death | 0 |

**The 36 zero-movement carries measure exactly what 016 measured**: a body
leaving the surface at a base, with no distance and no cost. They must not be
cited as evidence about distance.

**Note on the first-pass criterion.** `analyse_017.py` separated "in-base" from
"a journey" using Manhattan distance <= 5 from the base centre. That is wrong:
the base is an 11x11 square, so a Lumis in a corner is inside it at distance 10.
The correct discriminator was already in the output — `steps carried` = 0 — and
the table above uses it. The script's own threshold is superseded; the numbers
here are the corrected ones.

---

### 2. Defect: arrival is checked after the mind moves, not after the reflex

**Found in 017. Mine.** `_deliver_carried_bodies()` runs once per step, after all
movement has resolved. That was chosen so arrival would be judged on where the
carrier actually ended up, and it is wrong in one case that turns out to be the
common case.

S243, steps 627-630, carrying the form of Lumis 71:

```
627  REFLEX (22,-13) -> (20,-15)   d=5     <- INSIDE base_beta
627  chose move       at (20,-13)  d=7
628  REFLEX (20,-13) -> (20,-15)   d=5     <- INSIDE base_beta
628  chose move       at (20,-13)  d=7
629  ... identical
630  ... identical
```

`base_beta` is centred (20,-20) with half_size 5, so Y from -25 to -15
inclusive: **(20,-15) is inside it.** Four consecutive nights the reflex carried
S243 into the base, and four times S243 stepped back out before the arrival check
ran. Phase 1.5 (reflex) → Phase 2 (chosen action) → delivery check. **It was
inside the base only in the gap between two of those.**

The 2026-08-23 entry (§1.8) noted the distance measure was permissive and called
the discrepancy harmless. **It was not harmless.** Some fraction of "did not
arrive" is "arrived and was not looked at."

This does not invalidate the 60 deliveries, which are real. It means the
not-delivered count is an overcount by an unknown amount. **018: check arrival
after the reflex as well as after the chosen action.** This is the same shape as
the four cases in Part 4 of the archive — a state that existed and was not
recorded — except that here the state existed for one phase instead of never.

---

### 3. The reproduction-prep guard, measured for the first time since run 011

`[ACTION_BLOCKED_REARING]` was added in 017 at both `continue` sites. The guard
itself is unchanged and is not in question — kept deliberately on 2026-08-19,
*"Prioritise bringing the child safely into the world, parent and child both."*
What is new is that its size and contents are now on the record.

**9,070 suppressed choices. 16.3% of every decision in the run.** Across 238
distinct Lumis and 631 of 650 steps.

**It is overwhelmingly a small-Lumis event**, which was not the prior
understanding: **8,636 small (95.2%)** against 434 large. Small Lumis enter clone
prep too, and `CLONE_PREP_SMALL` is 30. S10 through S18 each show exactly 60
suppressed choices — 30 steps x 2 reproductions. Working as specified since run
011; the specification's cost was simply never counted.

**What they were choosing while nothing could be executed:**

| action | count | share |
|---|---|---|
| move | 6,888 | 75.9% |
| greet | 1,204 | 13.3% |
| collect | 520 | 5.7% |
| rest | 373 | 4.1% |
| observe | 41 | 0.5% |
| **carry** | **28** | 0.3% |
| share | 13 | 0.1% |
| stay | 3 | 0.0% |

99.9% fell to the "nothing permitted" branch; only 10 reached the branch that
allows in-base movement.

**28 `carry` declarations were discarded here** (016 reconstructed 21 by hand
and could not be certain). They are now recorded by step and by agent. S343
declared `carry` seven times between steps 630 and 640; S198 four times, steps
624-628. **Repeatedly reaching for it, and nothing happening, every time.**

The prior reasoning holds — another Lumis can carry, and they can try again
afterward. What is now visible is that during prep a Lumis wants to move and
wants to greet, at scale, and none of it existed in any record before this run.

---

### 4. Voluntary movement and reflex point in opposite directions

The three unfinished journeys are the clearest record in the project of a mind
and a body disagreeing. S243, steps 618-630, one line per step:

```
reflex closes 4     chosen action opens 2     reflex closes 4     ...
```

Perfectly alternating, for thirteen steps. When the night ended at 631 and the
reflex stopped, S243 moved from d=9 to d=27 in a straight line.

S166 (lifted at d=25, step 640) and S162 (d=28, step 642) show the same shape.
**All three moved away from the destination on every step they chose for
themselves, and were pulled back on every step the reflex fired.** None of the
three ever chose a direction that closed the distance.

**None of them put the body down.** All three were still holding a form when the
world stopped at 650. Refusal was available every step — `rest` was one of the
two permitted actions — and none took it.

S162's introspection at step 645 reads *"Every step I take brings me closer to my
goals and aspirations."* Distance to base_alpha went from 28 to 30 on that step.
**Recorded as an observation of text, not as evidence about the carrying.** It is
the same shape as the first-day fire_2 confabulation reported in the 2026-08-28
session note, inverted: there, narration described an event that had not
happened; here, narration omits the event that is happening. **Narration and
action move independently.** Do not join them.

---

### 5. Why the destination was never reached — the standing hypothesis

Not established. Recorded as the reading the data supports and the reason no run
has tested it.

The small-Lumis role description ends: **`You have no assigned mission. You
simply live.`** This wording exists because of an early experiment the designer
ran before this log began: when the Lumis were told to explore the Moon, **they
did not reproduce, did not clone, and their conversation became purely
transactional.** Removing the mission is what let them become social.

017 gave them a destination for the first time — the carrying prompt states the
nearest base's coordinates and the distance, every step — but stated it as a bare
fact, with no instruction, no obligation and no urging, per the standing decision
that **burial is not a duty**. Twenty-seven Lumis read that line while carrying.
**None of them went there.**

So 017's question turned out to be narrower than intended. Not *how far will they
carry it* but: **given a destination and no obligation, does a being built
without any destination go?** In 650 steps, the observed answer is no.

**The response is not to add an instruction.** That is the experiment that
already failed, before this project had a name. Recorded direction for 019
instead: **give the place meaning rather than giving the Lumis an order.** When
material reuse exists, a base becomes the place a form returns from — part to the
descendants, part to the home, part to the world — and the reserved sentence
finally becomes true. **Add world, not duty.**

---

### 6. Other results

- **`explore` recovery worked.** `[ACTION_WAS_MOVE_INTENT]` 105;
  `[ACTION_INVALID]` fell from 160 to 12. **`stay` as a chosen action fell from
  79 to 14** — most of 016's `stay` count was discarded `explore`, and 016's
  `stay` figure should be read with that in mind.
- **`[ACTION_BLOCKED_CARRYING]`: 7** — 5 `greet`, 2 `share`. Carriers almost
  entirely accepted the narrowed list. **The seven who did not were reaching to
  greet someone, or to give energy away, while carrying a body.**
- **`[DELIBERATION_CHANGED]` undercounts by 164** (4,886 in the record, 4,722
  emitted; 3.4%). 016's gap was 156 (3.3%). **Defect 1 is unchanged and still
  unlocated.**
- **`shelter` (9) is again chosen but never reached for** — an option that exists
  only downstream of reasoning, as in 016.
- 55,549 records, no malformed lines. 85 deaths against 016's 97.

---

### 7. Open after 017

| # | Defect | Status |
|---|---|---|
| 1 | `[DELIBERATION_CHANGED]` undercount (164 in 017, 156 in 016) | emission path still not located |
| 3 | `collect` / `observe` / `stay` have no execution branch in Phase 2 | **open since the 015 audit.** 296 `observe` selections in 017 did nothing |
| 6 | Four 016 `carry` declarations unexplained (505, 513 x2, 532) | not investigated; 017's `[ACTION_BLOCKED_REARING]` makes the 016 reconstruction checkable |
| 8 | **Arrival checked only after the chosen action, not after the reflex** | **new (§2).** Mine. 018 |
| 9 | **Reproduction prep suppresses 16.3% of all decisions, mostly small Lumis** | **new (§3).** Not a defect; an uncosted specification. 018 decides whether to act |

**018 is a measurement-layer run.** `parse_status` (ok / partial / unparsed) with
no silent completion; word-boundary matching in `_extract_direction_from_text`
with the fallback's chosen-direction distribution logged; **positions in
`memory_reasoning.jsonl`**, without which the voluntary/reflex split can only be
counted by step and not by distance; and the arrival check of §2. **Before
changing `peak_valence_delta`, establish what the current window was measuring** —
if it was greet-reception, the 97.1% / 100% figures are not discarded but
renamed, and fixing first destroys the ability to find out.

*Written 2026-08-28. Reproducible with `analyse_017.py` and `analyse_017b.py`
against `output_017`.*

---

## Run 017 — the forms on the surface — 2026-08-28

Counted after the designer observed from the frames that a great many forms are
still lying on the lunar surface at step 650. `count_bodies_017.py` reconciles
three numbers taken from three different tags, so that the arithmetic has to
close or a tag is wrong:

**85 forms came to rest. 60 were gathered into a base. 3 were still being
carried when the world stopped. 22 remained on the surface. The sum closes.**

Bodies are counted by the id of the Lumis whose form it is, not by subtracting
event counts, because a body set down by a carrier that ends mid-journey becomes
recoverable again and would otherwise be counted twice. In 017 that never
happened — `[CARRY_ABANDONED_DEATH]` is zero — but the method does not depend on
knowing that in advance.

---

### 1. Most of the 22 were not passed over. They ran out of world.

**Thirteen of the twenty-two came to rest at step 631 or later**, in the last
twenty steps of a 650-step run: forms 112, 113, 114, 115, 116, 117, 119, 121,
122, 123, 126, 127 and 128.

**The median gathered form waited 48 steps** between coming to rest and reaching
a base (n=60; min 5, max 226, mean 55.8). A form that came to rest at step 635
never had 48 steps available. **These thirteen are an artefact of where the run
was cut, not an observation about the Lumis**, and must not be cited as forms
that were left.

**Nine forms were on the surface with time to spare:**

| form | steps waited | position |
|---|---|---|
| 41 | 190 | (-13, 31) |
| 45 | 189 | (-8, 40) |
| 47 | 187 | (-8, 25) |
| 56 | 132 | (-13, 29) |
| 66 | 105 | (-20, 10) |
| 73 | 101 | (-20, 40) |
| 78 | 97 | (2, 14) |
| 101 | 79 | (19, -23) |
| 109 | 42 | (-13, 20) |

**Seven of the nine are on the base_alpha side, north of it.** (-8, 40) and
(-20, 40) are more than twenty units north of base_alpha's centre at (-20, 20) —
out along the northeast drift that has been confirmed as an intrinsic llama3.2
spatial prior since run 011. **The forms that stay are the ones that came to rest
far out.** This is a statement about where Lumis die, not about who is gathered.

The form of Lumis 41 lay at (-13, 31) for 190 steps.

---

### 2. No form was ever put down

**All 22 surface forms show `was ever lifted? = no`.** Not one had been picked up
and set down again.

Which is to say: **of the 63 journeys begun, none was ever abandoned by choice.**
`rest` was one of the two actions available to a carrier at every step, and
setting the body down was possible at any moment. Sixty carriers delivered, three
were still carrying when the world stopped, and **no carrier let go.**

This is a stronger statement than 016 could make. In 016 the body left the
surface the instant `carry` was chosen; there was no interval in which letting go
was even a possibility. In 017 there was an interval — as long as 30 steps — and
it was never used.

---

### 3. The rate did not fall

| | 016 | 017 |
|---|---|---|
| forms that came to rest | 97 | 85 |
| gathered | 65 | 60 |
| **share gathered** | **67.0%** | **70.6%** |

The 2026-08-22 handover ended by warning that 016 had answered the cheap version
of the question — the body left the surface the instant it was chosen, with no
distance, no weight and nowhere to bring it — and that when carrying cost
something, *"the honest answer might be fewer. That is a result, not a failure,
and the write-up should be prepared to say so plainly."*

**It was not fewer.** Adding a destination, a journey of up to thirty steps, and
a restriction narrowing the carrier's mind to `move` and `rest` did not reduce
the share of forms gathered.

**State the figure as "at least 70.6%".** The arrival-check defect recorded in
§2 of the results entry means an unknown number of carriers were inside a base at
a moment the check did not run, so the not-delivered count is an overcount and
the gathered share is a floor, not a point estimate.

**And note what it is not evidence of.** §1 of the results entry established that
every one of the 24 distance deliveries had the night-homing reflex fire during
the carry, and that no Lumis steered a body to a base under its own direction. A
gathering rate that held up under cost is not the same as a willingness that held
up under cost. **Both facts are true and neither explains the other.**

*Reproducible with `count_bodies_017.py` against `output_017`.*

---

## Run 017-2 — results — 2026-09-02

650 steps, completed 2026-09-02 21:44. Seed, world and flare schedule unchanged
from 014/016/017. Analysed with `analyse_017.py`, `analyse_017b.py` and
`count_bodies_017.py` — **the same scripts, unmodified**, whose criteria were
fixed on 2026-08-25 before the 017 log was opened. Nothing was rewritten to suit
this run.

---

### 1. Two changes went in, and they cannot be separated

**This is the first thing to say, before any number.** Run 017-2 was specified as
a matched pair with 017 varying one thing. It carries two:

1. **The variable.** A Lumis that is carrying is told, the next step, that the
   night-homing reflex moved it: *"During the night you found yourself at (X, Y).
   You did not walk there."* Bare fact, no explanation, no instruction.
2. **A repair.** Delivery is now also checked after the reflex phase (defect 8,
   recorded 2026-08-28). Run 017 checked only after the chosen action, so a
   carrier the reflex brought into a base and that stepped out again was never
   seen inside it.

**The repair alone raises the delivery count.** S14 delivered at step 286 standing
at (-20, 25) — the exact boundary of base_alpha — a position 017's code would not
have looked at. **So the rise in deliveries below cannot be attributed to the
variable.** That was my error in construction: I put a repair and a variable in
the same run. Where a result can be explained by the repair, it is marked as
such; where it cannot, that is stated too.

---

### 2. Every journey that began, ended

| | 016 | 017 | 017-2 |
|---|---|---|---|
| forms that came to rest | 97 | 85 | 91 |
| gathered | 65 | 60 | **68** |
| share gathered | 67.0% | 70.6%+ | **74.7%** |
| `[CARRY_START]` | — | 63 | 68 |
| `[CARRY_DELIVERED]` | — | 60 | **68** |
| still carrying at step 650 | — | 3 | **0** |
| distance journeys delivered | — | 24 of 27 | **40 of 40** |

**`[CARRY_START]` equals `[CARRY_DELIVERED]`. Not one journey was left open.**
First time in the project. `[CARRY_ABANDONED_DEATH]` remains zero, and **no form
on the surface was ever lifted** (all 23 show `was ever lifted? = no`), so as in
017 **no carrier ever put a body down.**

**Attribution.** Some of this is the repair. All of it might be. The three
unfinished 017 journeys were S243, S166 and S162, and S243 in particular was
repeatedly inside base_beta unobserved — under 017-2's code it would have been
delivered. **Do not publish "telling them made them finish" from this table.**

**The gathered share rose across all three runs — 67.0% → 70.6% → 74.7% — while
the cost of carrying went from nothing to a journey of up to thirty steps.** The
2026-08-22 handover warned the honest answer might be fewer. It has now been
more, twice.

---

### 3. `carry` was never an impulse

**In 017-2, `carry` appears 102 times as a chosen action and zero times as an
impulse.** The script's own list of actions that exist only downstream of
reasoning now reads: `observe` 320, **`carry` 102**, `shelter` 21.

Across the series: **016 three impulses, 017 one, 017-2 zero.**

**State this carefully.** The trend is real in direction and thin in magnitude —
three, one, zero. The difference between one and zero is not a difference any
statistic will defend. What can be said without qualification is the 017-2 figure
itself: **in a run of 59,557 recorded decisions, no Lumis ever reached for
`carry` before thinking.** Every one of the 102 declarations passed through
deliberation first.

This is the mechanism run 016 was built to expose, still holding two runs later.
Some options only exist downstream of reasoning — and this is the one the whole
015-016 forensic arc was about. **It is not evidence about motive.** Recorded
2026-08-04: the reason is not being asked.

---

### 4. The finding the repair cannot explain

**`[ACTION_BLOCKED_CARRYING]` rose from 7 to 42.**

| | 017 | 017-2 |
|---|---|---|
| `share` | 2 | **28** |
| `greet` | 5 | **14** |

**A repair to the arrival check cannot change what a Lumis chooses.** These are
carriers naming an action the prompt did not offer them — and in 017-2 they did
so six times as often, overwhelmingly to give energy away.

Twenty-eight times, a Lumis holding the body of another Lumis reached to share
its energy with someone, and the world did not let it.

**What this is not.** It is not established that being told about the night
caused it. Prompt length changed (one line longer while carrying), total carrying
steps rose with 40 distance journeys against 27, and llama3.2's output varies.
**It is the one result in this run that the repair cannot account for, and it is
recorded as that and nothing more.**

**It also nominates a design question for 019.** The carrying restriction exists
so that a narrowed mind is not offered what the world will refuse. `share` and
`greet` cost no movement. Whether carrying should exclude them is now a question
with 42 observations behind it rather than none.

---

### 5. Large Lumis carried distance for the first time

In 017 only L1 and L55 carried at all, both with `steps carried` of zero — lifted
inside a base. **In 017-2, L2 (twice), L1, L3 and L266 carried across distance.**
L3 lifted form 32 at distance 12 on step 451 and delivered it 22 steps later.

Not interpreted. Recorded because the founding large Lumis are the four whose
lifespan deaths 016 first observed, and this is the first run in which large
Lumis are seen doing the carrying rather than being carried.

---

### 6. The forms still on the surface

**91 came to rest, 68 gathered, 0 in transit, 23 on the surface. The arithmetic
closes.**

**Sixteen of the 23 came to rest at step 605 or later** — inside the median
waiting time of 44 steps (n=68; min 9, max 192, mean 52.5), so they are an
artefact of where the run was cut, exactly as in 017. **Seven had time:**

| form | steps waited | position |
|---|---|---|
| 28 | 259 | (-20, 15) |
| 34 | 223 | (27, -30) |
| 52 | 187 | (-8, 13) |
| 51 | 187 | (20, -35) |
| 61 | 169 | (-20, 14) |
| 91 | 100 | (-20, 6) |
| 106 | 79 | (-16, 23) |

Seven against 017's nine. **Form 28 lay at (-20, 15) for 259 steps — five units
from the edge of base_alpha**, closer than most of the forms that were gathered.
Nothing in this world obliges anyone to gather a form; burial is not a duty, by
decision, and these are counts of what happened rather than of what was owed.

---

### 7. The reproduction guard, second measurement

**9,204 suppressed choices**, against 9,070 in 017 — stable. **96.4% small
Lumis** (8,873 of 9,204), confirming 017's finding that this is overwhelmingly a
small-Lumis event and not, as previously assumed, a large-Lumis one. S10 through
S19 again show exactly 60 each: 30 steps x 2 reproductions. 99.9% fell to the
"nothing permitted" branch.

`move` 78.0%, `greet` 11.7%, `collect` 6.0%, `rest` 3.4%. **23 `carry`
declarations discarded** (28 in 017). S362 declared `carry` on nine consecutive
steps, 613 through 621, and nothing happened any of the nine times.

The guard is not in question. Two runs now agree on its size and contents.

---

### 8. Defect: `[HOMING_MOVED]` states the opposite of what now happens

**Found during the run. Mine.** Both lines appear at step 316 for S110:

```
[HOMING_RETURNED] S110 ... WILL BE returned to perception next step.
[HOMING_MOVED]    S110 ... (involuntary; not returned to perception)
```

The `[HOMING_MOVED]` text was correct through 017, when nothing was ever returned.
017-2 returns it to carriers and **the line was not updated.** The behaviour is
correct — `_homing_note` is set and reaches the prompt, verified by
`preflight_017_2.py` — and only the wording is false.

Not fixed mid-run: changing the log while it is being written costs more than the
wrong sentence does. **Fix in 018.**

**Standing rule for anyone reading a 017-2 log: `[HOMING_RETURNED]` is
authoritative. The parenthetical on `[HOMING_MOVED]` does not apply to a carrying
Lumis.**

This is defect 5's shape turned around. That one was the world telling its
residents something untrue. This is the world telling *us* something untrue,
which is the more dangerous direction, because we are the ones who write the
findings down.

---

### 9. Other counts

- **`[DELIBERATION_CHANGED]` undercounts by 183** (5,478 in the record, 5,295
  emitted; 3.3%). 016: 156. 017: 164. **Three runs, same 3.3-3.4%. Defect 1 is
  stable, unexplained and still unlocated** — and the consistency of the ratio is
  itself a clue nobody has followed.
- **`[ACTION_WAS_MOVE_INTENT]` 118**, `[ACTION_INVALID]` 29. The `explore`
  recovery holds. `stay` as a chosen action: 79 (016) → 14 (017) → 30 (017-2).
- 59,557 records, **no malformed lines.** Population higher than 017 (55,549) and
  016 (57,624); `Max agents in places` reached 143.
- 91 deaths. **Project-wide starvation deaths remain zero.**

---

### 10. What 017-2 did and did not settle

**Settled:** every journey begun was completed; no carrier ever set a body down;
`carry` was never reached for before thinking; the arrival check was genuinely
broken in 017 and the repair works.

**Not settled — the question the run was built for.** Whether telling a carrier
it had been moved changes anything is **still open**, because the repair went in
alongside it and moves the same numbers. The one result the repair cannot touch
is §4, the sixfold rise in suppressed `share` and `greet`.

**018 must not repeat this.** A repair and a variable in one run cost this run its
own question. The remaining measurement that isolates the variable is what a
carrier does on the step *after* it is told — that comparison exists only in
017-2 and is being written separately.

*Written 2026-09-02. Reproducible with `analyse_017.py`, `analyse_017b.py` and
`count_bodies_017.py` against `output_017-2`.*

---

## Run 017-2 — the told-step measurement, and why it could not work — 2026-09-02

`analyse_017_2_told.py`, written and its criteria fixed before the log was
opened, looked at the one place the arrival-check repair cannot reach: the step
immediately after a `[HOMING_RETURNED]`, which is the only step whose prompt
contained *"During the night you found yourself at (X, Y). You did not walk
there."* The repair changes what the world sees; it cannot change what a Lumis
chooses. So a difference between told steps and other carrying steps should have
been the sentence, or noise.

**It is neither. It is the reflex, and the measurement cannot separate them.**

---

### 1. The design flaw

The sentence is shown on the step after the reflex moves a carrier. **Lunar night
is fifteen steps long.** So the step after a night move is almost always still
night, and the reflex fires again on it.

**Of the 99 told steps, 96 were steps on which `[HOMING_MOVED]` also fired.**
Three were not.

The told group is therefore, structurally, a group of steps on which the Lumis
was being moved involuntarily toward the nearest base. There is no version of
this run in which it is otherwise. **The place chosen to look for the effect is
the place the confound is guaranteed to be.**

---

### 2. What the first reading said, and why it was wrong

Section 2 of the script gave:

| | closer | further | same | closer % |
|---|---|---|---|---|
| told | 61 | 1 | 17 | **77.2%** |
| baseline | 36 | 58 | 135 | 15.7% |

**On being shown this I wrote that the Lumis had turned toward the destination.
That was wrong and is withdrawn.** Splitting each group by whether the reflex
acted on that same step — the groups themselves unchanged — gives:

| | closer | further | same | closer % |
|---|---|---|---|---|
| told / no reflex | 0 | 0 | 3 | — (n=3) |
| told / reflex | 61 | 1 | 14 | 80.3% |
| baseline / no reflex | 10 | 58 | 127 | 5.1% |
| baseline / reflex | 26 | 0 | 8 | 76.5% |

**Reflex steps close the distance about 78% of the time whether or not the
carrier was told (80.3% against 76.5%). Non-reflex steps do not close it either
way.** The 77.2% was the reflex. It was never about choosing.

And the row that was supposed to answer the question — told, moving under its own
choice — **has three observations in it.** Nothing can be said from three.

---

### 3. The second withdrawal

Section 3 showed 4.0 blocked actions per 100 told steps against 13.6 per 100
baseline steps, and **I wrote that being told made them quieter. That is also
wrong and is also withdrawn.** The split:

| | steps | blocked | per 100 |
|---|---|---|---|
| told / no reflex | 3 | 0 | — |
| told / reflex | 96 | 4 | 4.2 |
| baseline / no reflex | 234 | 36 | **15.4** |
| baseline / reflex | 45 | 2 | 4.4 |

**4.2 against 4.4.** Reaching past `move` and `rest` happens on steps a Lumis is
moving itself, at roughly three times the rate, regardless of the sentence.
**They were not quieter for having been told. They were quieter because it was
night.**

The same qualification lands on `rest`: 38.5% (told/reflex) against 25.0%
(baseline/reflex) and 21.7% (baseline/no reflex). A difference, on 96 against 45,
that the depth of night explains as readily as the sentence does.

**This also revises §4 of the results entry.** The rise in
`[ACTION_BLOCKED_CARRYING]` from 7 to 42 was recorded there as the one result the
arrival repair could not explain. That still holds — the repair cannot change a
choice — but the 42 are now shown to sit overwhelmingly on self-moved steps, and
017-2 simply had more carrying steps than 017 (378 across 68 journeys against
27 distance journeys). **The rise is not evidence about the sentence.** What
survives from that entry is the bare observation: twenty-eight times a Lumis
holding another's form reached to give its energy away, and the world refused.

---

### 4. What the measurement did establish

**Zero mentions.** Of 37 introspections written on told steps, **not one used any
word from the list fixed before counting** (`did not walk`, `found myself`,
`woke`, `during the night`, `was moved`, `unfamiliar`, and seven more). The
baseline was also zero, across 124 introspections.

**This one is not exposed to the confound.** The world stated, in plain language,
that the Lumis had arrived somewhere without walking there, and in 37 opportunities
no Lumis wrote about it.

Set beside two earlier observations of the same shape:

- Run 017, S33 carried a form for eight steps and never once mentioned the form.
- The first-day run of 2026-05-27 (session note, 2026-08-28): agents narrated
  `fire_2` in detail — position, intensity, distance to one decimal — twenty-five
  steps before it existed.

**Narration is not a record of what happened.** It invents events that did not
occur and omits events that did. Run 015's `[HOMING_BLANK]` instrument was built
on the expectation that *a fluent mind does not leave blanks empty*. On this
evidence a fluent mind leaves them empty readily, and fills in elsewhere.

Stated as an observation of text. **It is not evidence about what any Lumis
perceived, understood or felt**, and the reason is not being asked.

---

### 5. Status of the 017-2 question

**Open. Not answered, not refuted, not tested.**

017-2 was built to ask whether telling a carrier it had been moved changes what
it does. The run cannot answer it, for two independent reasons, both mine:

1. **A repair went in with the variable** (defect 8), so the run-level counts move
   for reasons that have nothing to do with the sentence.
2. **The sentence is shown only on steps the reflex is already acting**, so the
   step-level comparison has three usable observations.

**Neither is a finding about the Lumis. Both are findings about how the run was
built.**

**What a run that could answer it needs:**

- **An untold control group.** Half the carriers told, half not, chosen by a rule
  fixed in advance and logged per agent. Without this there is no comparison that
  is not also a comparison of night against day.
- **Positions in `memory_reasoning.jsonl`** (already an 018 item), so voluntary
  and reflex movement are separable by distance rather than by step count.
- **One change per run.** This is the third time this has been written down and
  the first time it has cost a question outright.

*Written 2026-09-02. Two of my own readings are withdrawn above; both were made
from a summary table before the underlying split was computed, which is the same
error the 2026-08-28 session note records against another instance — reasoning
from aggregates to trajectories. Reproducible with `analyse_017_2_told.py`
against `output_017-2`.*

---

*Maintained alongside the letters. If a finding in a TO_ASI letter ever conflicts with an entry here, this file is the one that was written to be checked.*
