# AAPL Bounded Validation Preflight Status

## Result

- State: `startup_preflight_passed`
- Generated at: `2026-04-28T14:34:20Z`
- Trade date: `2026-04-28`
- Sanctioned execution path: `vm-execution-paper-01`
- Broker-facing session started: `false`
- Submit paper orders: `false`
- Broker cleanup allowed: `false`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Runtime Config

- Control-plane source: `docs/gcp_foundation/gcp_research_aapl_bounded_validation_runtime_config.yaml`
- VM path: `/opt/codexalpaca/codexalpaca_repo/config/aapl_bounded_validation_candidate.yaml`
- SHA-256: `d5fefd9540b8a0483f443b368fa7a1569653624c353d040c57d3d907ed3bc5fd`
- Runner source stamp: `codex/qqq-paper-portfolio` `a3b5e926d9bfec0ec83603770a778e7974e38398`

## Preflight Evidence

- Loaded underlyings: `AAPL`
- Loaded strategy count: `1`
- Loaded strategy: `aapl__governed_validation__trend_long_call_next_expiry_wide_reward_exit360`
- Required option inventory: available
- Stock freshness: within limit
- Broker positions at preflight: `0`
- Open orders at preflight: `0`
- Buying power check: above required threshold

Raw account balances are intentionally not committed to GitHub. The operator can reproduce them from the VM preflight output if needed.

## Remaining Blocks

- Exclusive execution window is not armed by this packet.
- Broker-facing paper validation is not authorized by this packet.
- Preflight is not broker-audited strategy-validation evidence.
- Live manifests and risk policy remain unchanged.
