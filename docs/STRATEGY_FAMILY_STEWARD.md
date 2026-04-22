# Strategy Family Steward

This repo keeps a formal GitHub-backed strategy-family registry so both research machines can refer to the same family-level source of truth before discovery, validation, and live-book review.

## Source Of Truth

- Builder:
  - `cleanroom/code/qqq_options_30d_cleanroom/build_strategy_family_registry.py`
- Generated artifacts:
  - `docs/strategy_family_registry/strategy_family_registry.md`
  - `docs/strategy_family_registry/strategy_family_registry.json`
  - `docs/strategy_family_registry/strategy_family_registry.csv`

## Steward Responsibilities

- Refresh the family registry before large family-expansion or down/choppy waves.
- Track which families are already live, which are validated but non-live, and which remain structurally under-tested.
- Keep family-level priority labels stable enough that discovery lanes do not drift into ad hoc repetition.
- Hand the highest-priority families to the discovery and exhaustive lanes.

## Refresh Command

From the repo root:

```powershell
python .\cleanroom\code\qqq_options_30d_cleanroom\build_strategy_family_registry.py `
  --live-manifest-path "C:\Users\<you>\Downloads\codexalpaca_repo\config\strategy_manifests\multi_ticker_portfolio_live.yaml"
```

The builder prefers the sibling `qqq_options_30d_cleanroom\output` layout used on the new machine, and falls back to the current shared OneDrive-ready dataset path on this machine.

## When To Refresh

- Before assigning new family-specific agent work
- Before building a Phase 1 discovery pack
- Before live-book hardening or replacement review
- After adding a new family or materially changing the strategy surface

## Priority Labels

- `priority_discovery`: family is still under-tested and belongs in discovery rotation
- `priority_validation`: family has evidence but needs exhaustive validation
- `promotion_follow_up`: family has enough evidence for manual live-book review
- `live_benchmark`: family is already live and should be benchmarked for diversification or replacement
- `monitor`: family is cataloged and should simply be refreshed as new evidence lands
