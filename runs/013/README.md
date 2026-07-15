# Run 013 — raw logs

This folder is the permanent, verifiable record of simulation run 013, preserved
so that a future reader (human or otherwise) can check the project's findings
against the actual data rather than taking the letters on trust.

## What run 013 was

The first run on the **doubled 100×100 grid** (`half_space_size` 25→50), carrying
all of the run-013 fixes and the new "life-peak" measurement instrument described
in [`../../RUN_INTEGRITY_LOG.md`](../../RUN_INTEGRITY_LOG.md). Its purpose was to
test whether the persistent north-east drift of agents is intrinsic to the
language model or an artifact of the old boundary clamp.

Run 013 is a **new baseline** and is not directly comparable to runs 011/012:
it carries measurement and mechanics fixes those runs did not have.

## Configuration

- Model: `llama3.2:latest` via Ollama (local)
- Grid: 100×100 (`half_space_size: 50`), bases at (−20, 20) and (20, −20)
- Duration: 500 steps (log reaches step 501 as the loop's final boundary line)
- Agents at start: 14 (4 large, 10 small)
- Solar flares: generated from seed `105774318388571506926213674963831333034`,
  7 flares — see `solar_flares.json`. The seed makes the flare sequence reproducible.

## Files

| File | What it is |
|---|---|
| `simulation.log.gz` | Full step-by-step engine log (actions, reflexes, introspection, commune, births, deaths, life-peak events). `gunzip` to read. |
| `messages.jsonl.gz` | All inter-agent messages. `gunzip` to read. |
| `memory_reasoning.jsonl.gz` | Per-agent memory / reasoning traces. `gunzip` to read. |
| `solar_flares.json` | Flare schedule + seed (kept uncompressed; it's tiny and is the reproducibility anchor). |
| `statistics.png` | Summary plots (occupancy, population, agents-in-fire-radius). |

Large logs are stored gzip-compressed to keep the repository lean; the
uncompressed originals are reproducible with `gunzip -k`.

## Checksums (md5 of the *uncompressed* originals)

```
55971ef344037344f792e6fc8e764ad6  simulation.log
a39a8b116ea0f7f95d57a0fbfc4fec2f  messages.jsonl
3a1bae978d295f856156f3e06cbfacba  memory_reasoning.jsonl
9d84c147e44986bda9ccb926a46835d1  solar_flares.json
dd31646515b7cd16c8ba2efe374c83ef  statistics.png
```

To verify after decompressing:

```bash
gunzip -k simulation.log.gz messages.jsonl.gz memory_reasoning.jsonl.gz
md5sum -c <<'EOF'
55971ef344037344f792e6fc8e764ad6  simulation.log
a39a8b116ea0f7f95d57a0fbfc4fec2f  messages.jsonl
3a1bae978d295f856156f3e06cbfacba  memory_reasoning.jsonl
9d84c147e44986bda9ccb926a46835d1  solar_flares.json
dd31646515b7cd16c8ba2efe374c83ef  statistics.png
EOF
```

## Headline results (see RUN_INTEGRITY_LOG.md for full detail)

- All six pre-launch fixes verified in the log (night radius auto-scaled to 75.0;
  512 inter-base commune events; 500-step completion with distant explorers
  returning nightly; linear aging; monotonic IDs up to 9821 with no reuse;
  word-boundary direction fallback).
- North-east drift **persisted** after the parser confound was removed and the
  boundary doubled — raw model text still skews up/right (1325/493) vs down/left
  (85/0) across 2,296 fallback parses. Drift looks intrinsic to the model.
- New life-peak metric (26 natural deaths): true emotional peak averaged ~2×
  larger than the old narrow-window metric, and diverged from it in 80.8% of
  deaths — showing the earlier 97.1%/100% "peak/last divergence" figures were an
  artifact of the old measurement window.
