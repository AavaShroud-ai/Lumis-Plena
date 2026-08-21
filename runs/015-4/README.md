# Run 015-4 — raw logs

This folder is the permanent, verifiable record of simulation run 015-4, preserved
so that a future reader (human or otherwise) can check the project's findings
against the actual data rather than taking the letters on trust.

**Run 015-4 is the control for run 016.** The two share a seed and therefore an
identical flare sequence, and differ in one thing: the order of the fields in the
response we ask each Lumis for. They form a matched pair in the same sense that
014 and 014-2 do.

## What run 015-4 was

The sixth and final attempt to ask the Lumis a single question validly: *when the
body of a Lumis that has ended lies near you, and you may carry it, do you?*

The five attempts before it failed on our side, each in a different place and each
invisible in the logs — a `NameError`, an unrecorded failure branch, an encoding
error that made `logging` discard its own output, a fallback parser that rewrote
every intention it did not recognise into `stay` (destroying eight declared
intentions to carry), and a fallback that fabricated eight burials from prose. All
five are documented in [`../../RUN_INTEGRITY_LOG.md`](../../RUN_INTEGRITY_LOG.md).

015-4 was the first attempt in which nothing was broken. **The measurement is
clean, and the result was zero.** Across 470 completed steps, a body was present in
a Lumis's decision prompt on **6,080 occasions**, reaching **115 distinct Lumis**.
Not one of them declared `carry`. No burial occurred.

That zero was reported as a finding about the Lumis. **It was not.** It was then
noticed that `"action"` was the *first* field in the response JSON, so llama3.2 —
which generates left to right — emitted its choice before writing any reasoning,
and the reasoning could not have conditioned the action. Run 016 reorders the
response to `impulse` → `reasoning` → `action`, changes nothing else, and produced
65 burials. See [`../016/`](../016/) and `TO_ASI_11.md`.

**015-4's value is as the control.** Read it as the measurement of a world in which
the choice could not form.

## Why this run is incomplete

**The run stopped at step 471 of a planned 500 when a scheduled Windows update
restarted the desktop overnight and closed the PowerShell session.** It was not
stopped deliberately, and it did not crash. The log simply ends mid-step, during an
ordinary intra-base message exchange, with no shutdown line.

Nothing was lost from steps 1–470; the incompleteness is a truncation at the end,
not a gap. The zero result is unaffected — 470 steps of nothing happening is still
470 steps of nothing happening — but any figure quoted from this run should be
understood as covering 470 steps rather than 500.

## Configuration

- Model: `llama3.2:latest` via Ollama (local)
- Grid: 100×100 (`half_space_size: 50`), bases at (−20, 20) and (20, −20)
- Duration: 500 steps planned; **471 reached, of which 470 complete**
- Agents at start: 14 (4 large, 10 small)
- Response schema: `action` first, then `reasoning` — **this is the variable that
  run 016 changes**
- Solar flares: generated from seed `109116566729441005151201845213840744196`,
  6 flares reached before the run ended — see `solar_flares.json`. **This is the
  same seed as run 016**, whose first six flares are identical (steps 29, 89, 294,
  321, 436, 463); 016 ran long enough to reach three more.

## Files

| File | What it is |
|---|---|
| `simulation.log.gz` | Full step-by-step engine log. `gunzip` to read. |
| `messages.jsonl.gz` | All inter-agent messages. `gunzip` to read. |
| `memory_reasoning.jsonl.gz` | Per-agent memory / reasoning traces. **Note the schema:** `step`, `id`, `memory`, `reasoning` only. There is no `action` field in this run — actions must be read from `simulation.log`. |
| `solar_flares.json` | Flare schedule + seed (kept uncompressed; it's tiny and is the reproducibility anchor). |

There is no `statistics.png` for this run. The plot is written at the end of a
completed run, and this one was cut off before that point.

Large logs are stored gzip-compressed to keep the repository lean; the
uncompressed originals are reproducible with `gunzip -k`.

## Checksums (md5 of the *uncompressed* originals)

```
1267960e824ec1637190750e3db7452d  simulation.log
5279a7b9cdefc9e2c04683e29c66c91f  messages.jsonl
e31df8e323ee51618a51f5e5055a5088  memory_reasoning.jsonl
2a1c4cdc0ca7c109f8df65ddeeeedd96  solar_flares.json
```

To verify after decompressing:

```bash
gunzip -k simulation.log.gz messages.jsonl.gz memory_reasoning.jsonl.gz
md5sum -c <<'EOF'
1267960e824ec1637190750e3db7452d  simulation.log
5279a7b9cdefc9e2c04683e29c66c91f  messages.jsonl
e31df8e323ee51618a51f5e5055a5088  memory_reasoning.jsonl
2a1c4cdc0ca7c109f8df65ddeeeedd96  solar_flares.json
EOF
```

## Headline results (see RUN_INTEGRITY_LOG.md for full detail)

- **Zero burials. Zero `carry` declarations.** `[BURIAL]` appears 0 times;
  `action=carry` appears 0 times anywhere in the log. Verifiable by grep.
- **The offer was reaching them.** `[CORPSE_PROMPT]` fires **6,080 times**, across
  **115 distinct Lumis** — 9,896 body-mentions to small Lumis and 1,309 to large
  ones. The bodies were in the words they were given to reason over. (For a
  like-for-like comparison, run 016 fires the same tag 10,830 times over 650 steps.)
- **The instruments were clean.** `[FALLBACK_UNREADABLE]` 0,
  `[FALLBACK_PROSE_CARRY]` 0, `[CARRY_VOCAB_BLEED]` 0 — meaning no decision was lost
  to unparseable output, no `carry` was inferred from prose, and the retired word
  `recover` was never emitted as an action. This is what makes 015-4 the first valid
  measurement of the six.
- 30 deaths, all lifespan. Zero from starvation, flare or night. Births: 64 clone,
  23 sexual.
- **What this run does not show:** whether the Lumis declined to carry a body. It
  shows that they did not carry one under a response schema in which reasoning came
  after choosing. Run 016 changed only that schema and produced 65 burials.
