# Runner Execution Upgrade Handoff

Use this handoff when the new machine needs to bring the live paper runner up to the current institutional execution baseline in `abisaabr/CodexAlpacaTest-Trade`.

## Scope

This handoff covers four runner-side upgrades that were implemented on branch `codex/qqq-paper-portfolio` in the main runtime repo:

1. `50764cf` - `Add Alpaca multi-leg order routing to paper runner`
2. `4292514` - `Align paper runner with Alpaca option fee model`
3. `f6d6168` - `Add multileg exit cleanup fallback`
4. `8037710` - `Harden multileg exit reconciliation`

Target repo on the new machine:
- `C:\Users\<you>\Downloads\codexalpaca_repo`

Primary files touched in the runtime repo:
- `alpaca_lab/multi_ticker_portfolio/trader.py`
- `tests/test_multi_ticker_portfolio.py`

## What Changed

### 1. True Alpaca Multi-Leg Routing

The paper runner's normal entry and exit path now supports real Alpaca `mleg` combo orders instead of silently routing only `legs[0]`.

Behavior change:
- single-leg strategies still use the existing simple order ladder
- multi-leg strategies now build combo limit orders with the correct per-leg open and close intents
- credit and debit combo pricing is normalized so the runner can submit combo orders in Alpaca-compatible notation
- combo fills now update combo-level trade state correctly instead of mutating only the first leg

Important boundary:
- emergency and safeguard cleanup still run leg-by-leg on purpose

### 2. Alpaca-Aligned Fee Model In The Runner

The paper runner no longer assumes a flat `$0.65` per contract commission.

It now models Alpaca's current option fee posture:
- broker commission: `0.0`
- ORF on buys and sells
- OCC on buys and sells
- TAF on sells only
- CAT for options currently modeled at `0.00`
- fee totals rounded up to the nearest cent

This now flows through:
- entry cashflow
- exit cashflow
- open-trade equity marking
- expected PnL checks
- cleanup exits
- completed trade records
- trade-event telemetry

### 3. Combo Exit Cleanup Fallback

The paper runner no longer treats a not-filled multi-leg combo exit as a dead end.

Behavior change:
- routine multi-leg exits still try the normal combo `mleg` limit ladder first
- if that combo exit does not fill, `_run_exit()` now falls back immediately into the known-trade cleanup path
- the cleanup closes each leg deliberately and records the trade as `via_cleanup=True`
- exit telemetry now distinguishes:
  - clean combo exits
  - combo exits that missed and degraded into cleanup
  - the cleanup trigger reason `combo_exit_not_filled`

Important boundary:
- this is still a deterministic safeguard path, not a partial-combo reconciliation engine
- startup/EOD order-state reconciliation still deserves extra care around partially filled combo exits

### 4. Partial-Fill-Safe Reconciliation

The paper runner now does a better job of not fighting its own combo exits.

Behavior change:
- open close-order suppression now inspects `legs[*].position_intent` on Alpaca `mleg` orders instead of relying only on the top-level order symbol
- known-trade cleanup now prefers live broker leg quantities when they are available
- that means a partially filled combo exit is less likely to trigger duplicate cleanup or oversize cleanup orders

Important boundary:
- if Alpaca has already flattened all trade legs before cleanup starts, the runner still falls back to its current deterministic accounting path rather than reconstructing the broker's exact combo fill economics
- statement-level reconciliation is still the next layer above this

## Why This Matters

These four changes close a major research-to-execution gap:
- the cleanroom can now research defined-risk and multi-leg structures more realistically
- the paper runner can now express those structures at the broker in a combo-native way
- live runner economics are much closer to Alpaca's actual options fee posture
- routine combo exits now degrade into an explicit cleanup path instead of silently stalling on a not-filled combo order
- cleanup sizing and startup/EOD suppression are safer when combo exits partially fill

Without these changes, multi-leg strategies can look valid in research while still being distorted in live runner accounting or routed as if they were single-leg trades.

## Validation Standard

When these commits are present on the new machine, validate with:

```powershell
python -m pytest -q
```

Expected result at the time of this handoff:
- `109 passed`

## Official Alpaca Sources

Use these sources when verifying fee and order assumptions:
- [Regulatory Fees](https://docs.alpaca.markets/docs/regulatory-fees)
- [Brokerage Fee Schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)
- [Options Level 3 Trading](https://docs.alpaca.markets/docs/options-level-3-trading)

## Recommended New-Machine Procedure

1. Open `C:\Users\<you>\Downloads\codexalpaca_repo`.
2. Fetch `origin/codex/qqq-paper-portfolio`.
3. Confirm that commits `50764cf`, `4292514`, `f6d6168`, and `8037710` are present.
4. If the machine is intentionally tracking a different branch, inspect and cherry-pick or merge these changes deliberately.
5. Run `python -m pytest -q`.
6. Summarize:
   - whether the runner now supports combo-native `mleg` orders
   - whether the runner fee model is Alpaca-aligned
   - whether a not-filled multi-leg exit now degrades into cleanup instead of stalling
   - whether combo close-order detection now inspects `mleg` legs and cleanup sizing now prefers live broker quantities
   - whether the full test suite is green
   - whether any local operational config should stay unchanged before market open

## Not Included Yet

These are still good next upgrades, but they are not part of this handoff:
- explicit SEC sell-fee modeling inside combo executions
- statement-level reconciliation of realized live fees against runner estimates
- execution-calibration feedback directly altering runner-side entry and exit ladders
- combo fill-probability and no-fill modeling in the live runner
