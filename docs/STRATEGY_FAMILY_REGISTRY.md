# Strategy Family Registry

This repo now carries a formal, GitHub-backed strategy-family registry so both the research machine and the new paper-runner machine can refer to the same family taxonomy, live-book overlay, and research-priority view.

## What It Is

- Builder script: `cleanroom/code/qqq_options_30d_cleanroom/build_strategy_family_registry.py`
- Committed snapshot:
  - `docs/strategy_family_registry/strategy_family_registry.csv`
  - `docs/strategy_family_registry/strategy_family_registry.json`
  - `docs/strategy_family_registry/strategy_family_registry.md`

The registry is family-level, not ticker-level. It answers:
- which families exist in the cleanroom now
- which strategy sets each family belongs to
- which families are already live
- which families have only been selected or promoted locally
- which families are still structurally under-tested across the ready universe
- what the steward agent should do next for each family

## Steward Role

The `Strategy Family Steward` is the control-plane owner of this registry.

Responsibilities:
- refresh the registry before major family-expansion waves
- refresh the registry before live-book review or replacement planning
- keep family taxonomy and live-manifest overlay current
- hand priority families to the Strategy Architect and discovery lanes
- never write the live manifest directly

## Refresh Command

Run this from the cleanroom code folder when you want a fresh registry:

```powershell
python build_strategy_family_registry.py `
  --output-root "C:\Users\<you>\Downloads\qqq_options_30d_cleanroom\output" `
  --ready-base-dir "C:\Users\<you>\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output\backtester_ready" `
  --live-manifest-path "C:\Users\<you>\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml" `
  --report-dir "C:\Users\<you>\Downloads\CodexAlpacaTest-TradeMigratyion\docs\strategy_family_registry"
```

## How To Use It

- Use the committed markdown for quick operator review.
- Use the JSON as the machine-readable source of truth for prompts, reporting, or agent planning.
- Use the CSV for quick spreadsheet-style ranking or manual review.
- Treat `priority_discovery` families as the best candidates for new discovery lanes.
- Treat `priority_validation` families as the best candidates for exhaustive follow-up.
- Treat `live_benchmark` families as replacement or diversification targets, not blind additions.
- Treat `promotion_follow_up` families as research areas with enough signal to merit review, but not automatic manifest edits.

## Current Intent

This registry is meant to stop the team from repeatedly rediscovering the same facts:
- the live book is still heavily single-leg
- multi-leg premium and convexity families are under-tested
- family-level gaps should drive the next tournament design

It is a reference surface first, not an autopromotion system.
