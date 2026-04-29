# Beta Promotion Retest Handoff

Date: April 29, 2026.

## Status

- Canonical runner commit `91ce125` was confirmed on `origin/codex/qqq-paper-portfolio` and the clean runner lane is checked out at `91ce125adb33003a1d999ccd74958eec60b9556d`.
- Beta manifest was pulled and parsed from `C:\Users\abisa\Downloads\codexalpaca_repo_gcp_lease_lane_refreshed\config\promotion_manifests\multi_ticker_portfolio_beta_promotions.yaml`.
- Exact live strategies: 94.
- Promoted beta retest families: 6.
- Retest-gap symbol count: 29.
- Exact promoted subset preserved: `Call backspread`.
- Governed supersets only: `Iron butterfly, Long straddle, Put backspread, Single-leg long call, Single-leg long put`.
- Offline retests run: none; required local priority-gap option replay inputs are incomplete.
- Verification: JSON packet parsed successfully; runner manifest-builder tests passed with `2 passed` in the repo-local venv; packet files are ASCII-only.

## Next Best Action

Run research-only offline retests in this order once the missing local or GCS replay inputs are available: Put backspread, Long straddle, Iron butterfly retest-gap tickers, then a QQQ exact-live sanity slice. Preserve the 0.90 fill gate and current strategy/risk policy.

## Guardrails

Do not trade, start a paper/live broker-facing session, mutate the live strategy manifest, relax the fill gate, widen the temporary parallel-runtime exception, or create new infrastructure from this handoff.

## Durable Files

- `docs/beta_retest/beta_promotion_retest_plan.md`
- `docs/beta_retest/beta_promotion_retest_plan.json`
- `docs/beta_retest/beta_promotion_retest_handoff.md`
