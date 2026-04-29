# GCP Research Option Fill Ladder 20260429 Closeout Status

## Current Read

- Status: `complete`
- Campaign: `option_fill_ladder_20260429`
- Mode: `research_only_option_fill_ladder_closeout`
- Broker-facing: `false`
- Trading effect: `none`
- Live manifest effect: `none`
- Risk policy effect: `none`
- Packets aggregated: `40/40`

## Fill-Gate Verdict

| Stage | Packets | Pass | Fail | Min Coverage | Avg Coverage | Failing Symbols |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `7d_atm` | 10 | 9 | 1 | 0.800000 | 0.980000 | `AMZN` |
| `30d_atm` | 10 | 10 | 0 | 0.904762 | 0.985714 | none |
| `30d_5x5` | 10 | 10 | 0 | 0.926407 | 0.983098 | none |
| `365d_5x5` | 10 | 10 | 0 | 0.986545 | 0.994541 | none |

## Important Findings

- The broad fill problem is not inherent to these top-10 liquid symbols when using active+inactive contract inventory and nearest listed expiration after trade date.
- The full `365d_5x5` next-trading-expiry dataset passes the `0.90` fill gate for every tested symbol.
- `AMZN` `7d_atm` is the only blocked narrow-scope dataset at `0.80` coverage; `AMZN` passes the `30d_atm`, `30d_5x5`, and `365d_5x5` gates.

## Successful Jobs

- `fill-ladder-7d-atm-20260429014336`
- `fill-ladder-repair-30d-atm-20260429015546`
- `fill-ladder-repair-30d-5x5-20260429015546`
- `fill-ladder-repair-365d-5x5-20260429015546`

## Durable Outputs

- Aggregate summary: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/summary/fill_ladder_aggregate_summary.md`
- Aggregate JSON: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/summary/fill_ladder_aggregate_summary.json`
- Aggregate rows CSV: `gs://codexalpaca-control-us/research_results/option_fill_ladder_20260429/summary/fill_ladder_aggregate_rows.csv`
- Option data root: `gs://codexalpaca-data-us/research_option_data/option_fill_ladder_20260429/`
- Stock data root: `gs://codexalpaca-data-us/research_stock_data/option_fill_ladder_20260429/`

## Guardrails

- Research-only data artifact and fill diagnostic.
- Do not trade from this packet.
- Do not arm an execution window from this packet.
- Do not start a broker-facing paper or live session from this packet.
- Do not modify live manifests, strategy selection, or risk policy from this packet.
- Do not relax the `0.90` fill gate for promotion review.

## Next Safe Step

Use the `30d_atm`, `30d_5x5`, and `365d_5x5` passing datasets for research-only strategy replay and liquidity-first promotion review. Keep `AMZN` `7d_atm` blocked unless repaired or excluded.
