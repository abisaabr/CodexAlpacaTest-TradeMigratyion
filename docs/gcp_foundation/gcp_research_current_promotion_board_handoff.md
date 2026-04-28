# Current Research Promotion Board Handoff

## Current State

- Control packet: `docs/gcp_foundation/gcp_research_current_promotion_board.md`
- Control JSON: `docs/gcp_foundation/gcp_research_current_promotion_board.json`
- State: `phase41_dense_coverage_passed_phase42_download_replay_running`
- Active research Batch jobs: `phase38-dense-top10-20260428203428` (`RUNNING`, older baseline lane) and `phase42-dense-download-replay-20260428182000` (`SCHEDULED`, repaired dense option download/replay)
- Broker-facing status: `not_started`

## Canonical Candidate State

`AAPL` exit-360 is the only current bounded-validation candidate. It is not live-promoted and has not yet produced broker-audited paper evidence.

`NVDA` exit-300 looked promising in Phase28 but failed Phase30 governance stress, so it is research-only.

The `AMZN`/`AVGO`/`MSFT`/`MU` wide-lag cluster failed Phase31 economics and should not be replayed unchanged.

Phase32, Phase32b, and Phase36 have completed and are included in the wave-level rollup. The completed rollup scanned `45` source reports and `640` candidates; `0` are eligible for governed promotion review.

Phase37 top-10 ATM completed and blocked all `183` candidates with `selected_contract_universe_gap`; max min-fill was only `0.1111`.

Phase39 completed and confirmed the dense fill bottleneck is option contract inventory, not stock reference coverage. Stock references were usable at `16/17` weekdays, while dense selected-contract coverage was only `4/17` weekdays for most symbols and `0/17` for `MU`.

Runner commit `91d75fb36c7c` adds the active+inactive historical contract inventory downloader. Phase40 rebuilt top-10 contract inventory using that pattern and existing Secret Manager credentials.

Phase40 fixed the inventory coverage gate: all ten symbols reached `17/17` requested weekday coverage for the `0-7` DTE inventory window.

Phase41 passed dense selected-contract coverage for all ten symbols: `16/17` selected weekdays (`0.941176`), with the remaining weekday being the market holiday gap.

Phase42 is now running option bar/trade download and strategy replay against the repaired dense selected-contract roots.

## Next Safe Research Step

Monitor Phase42 completion. If clean, aggregate shard portfolio reports into a wave-level promotion review. Do not promote from individual shard packets.

Do not broaden broker-facing paper validation beyond the current AAPL candidate without a new governed packet.

## Next Safe Execution Step

Only if explicitly authorized: arm a bounded exclusive execution window and run the existing AAPL bounded validation process. Otherwise keep research non-broker-facing.

## Hard Rules

Do not trade, arm a window, start a broker-facing paper/live session, modify live manifests, change risk policy, or relax the `0.90` fill gate.
