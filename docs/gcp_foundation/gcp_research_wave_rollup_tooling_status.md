# Research Wave Rollup Tooling Status

## State

- Status: `research_wave_rollup_tooling_ready`
- Runner branch: `codex/qqq-paper-portfolio`
- Runner commit: `6dca362e41bf`
- Source archive: `gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_6dca362e41bf.zip`
- Broker-facing: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## What Changed

The runner now has `scripts/build_research_wave_portfolio_rollup.py`.

The tool scans shard-level `research_portfolio_report.json` files and produces:

- one wave-level portfolio rollup
- one wave-level research-only capital plan
- one blocker/fill-failure map
- one data-repair priority queue
- one strategy-redesign priority queue
- one generated promotion-review packet

This is the missing systematic aggregation layer for large brute-force runs. It keeps the `0.90` fill gate intact and prevents manual cherry-picking from individual shard outputs.

## Validation

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_build_research_wave_portfolio_rollup.py tests/test_build_research_portfolio_report.py tests/test_build_research_promotion_review_packet.py tests/test_build_dense_option_universe.py tests/test_run_option_aware_research_backtest.py
```

Result after fill-inference hardening: `10 passed` for rollup/portfolio/promotion tests.

## Operator Use

After Phase37/Phase38 shards are downloaded or staged locally:

```powershell
.\.venv\Scripts\python.exe scripts\build_research_wave_portfolio_rollup.py `
  --report-root <local-report-root> `
  --output-dir <local-output-dir> `
  --fill-coverage-gate 0.90 `
  --min-option-trades 20 `
  --min-test-net-pnl 0 `
  --max-positions 8 `
  --max-strategies-per-symbol 2 `
  --max-symbol-weight 0.25 `
  --initial-cash 25000
```

## Guardrails

This tooling is research-only. It does not authorize trading, window arming, broker-facing sessions, live manifest changes, risk-policy changes, or fill-gate relaxation.
