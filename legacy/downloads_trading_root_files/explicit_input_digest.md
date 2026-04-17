EXPLICIT INPUT DIGEST
Date: 2026-04-04
Order rule followed: the five exact files below were opened before any broader repo scan.

FILE STATUS

1. C:\Users\rabisaab\Downloads\top10_authoritative_inventory.txt
- Opened successfully: yes
- Priority role: highest-priority hard input from another machine
- Function in this tournament: authoritative ranked variant inventory; exact variant names, audited metrics, and reconstruction constraints must be preserved
- Strategy families or variants defined:
  - tv_pvt_top5_finalists :: tsla_30m
  - index_opening_drive_lab :: FB_OR15_W09351000_Dlong_only_EMA0_VWAP0_VOLoff_Xtime_stop_1030
  - tv_pvt_top5_finalists :: nvda_30m
  - tv_pvt_top5_finalists :: vix_vxx_30m
  - index_opening_drive_lab :: FB_OR5_W09351000_Dlong_only_EMA0_VWAP0_VOLoff_Xtime_stop_1030
  - tv_pvt_top5_finalists :: vix_vxx_60m
  - tv_pvt_top5_finalists :: iwm_15m
  - codex_leveraged_pipeline :: out_base_20260103_122420
  - tv_squeeze_top5_finalists :: TSLA_30m
  - flux_signal_engine_top20_2025 :: MSFT residual survivor
- Immediate implications:
  - This file materially extends the strategy universe beyond the 13-family memo.
  - Exact repo/code matches for these names have not yet been found locally, so several entries currently remain file-backed rather than repo-verified.

2. C:\Users\rabisaab\Downloads\master_strategy_memo.txt
- Opened successfully: yes
- Priority role: current canonical local consolidation memo
- Function in this tournament: family-level source of truth for the 13 consolidated local strategy families, their blockers, and their latest decision-grade interpretation
- Strategy families defined:
  - Down Streak Exhaustion
  - QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System
  - Durable cRSI Family
  - Momentum / Relative-Strength Family
  - RSI Pullback / Z-Score Pullback / Gap Reversion Family
  - Breakout / Trend-Continuation Family
  - Pullback in Trend Family
  - Turn of Month Trend Family
  - Stacked Ensemble Family
  - Older Corrected Mean Reversion Baseline
  - Older Corrected Day-of-Week / Vol-Regime / Breakout Baseline Cluster
  - Options Vertical-Spread Wrappers
  - TradingView Reference / Ideation Scripts Cluster
- Immediate implications:
  - This file is the best local description of the pre-existing 13-family consolidation.
  - It clearly distinguishes robust candidates from unconfirmed upside families and archive-only clusters.

3. C:\Users\rabisaab\Downloads\strategy_chat_seed.txt
- Opened successfully: yes
- Priority role: compact summary only
- Function in this tournament: quick shortlist and blocker recap; useful for triage, not authoritative over the memo or top-10 inventory
- Strategy families defined or summarized:
  - Top 5 shortlist: Down Streak Exhaustion, QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System, Durable cRSI Family, Momentum / Relative-Strength Family, Breakout / Trend-Continuation Family
  - Tier 1, Tier 2, Tier 3 grouping from the memo
- Immediate implications:
  - This file is consistent with the memo but lower priority.
  - It is best used as a compressed orientation layer.

4. C:\Users\rabisaab\Downloads\codex_master_tournament_prompt_with_top10.txt
- Opened successfully: yes
- Priority role: supporting workflow reference
- Function in this tournament: confirms the intended workflow and embeds the same authoritative top-10 inventory found in the dedicated top10 file
- Strategy families or variants defined:
  - Repeats the same 10 authoritative variants from top10_authoritative_inventory.txt
  - Repeats the tournament workflow, output requirements, and reconstruction rules
- Immediate implications:
  - This file reinforces the top-10 inventory rather than adding materially new strategy content.
  - It is lower priority than the dedicated top-10 file but useful as process guidance.

5. C:\Users\rabisaab\Downloads\codex_master_tournament_prompt.txt
- Opened successfully: yes
- Priority role: older workflow reference
- Function in this tournament: workflow guidance only; it predates the explicit top-10 file and therefore cannot override it
- Strategy families or variants defined:
  - References the previously consolidated families and asks for repo discovery of the top-10 inventory if present
  - Includes tournament workflow and output requirements
- Immediate implications:
  - This file is now superseded by the later prompt-with-top10 and by the direct top10_authoritative_inventory.txt file.

SOURCE PRIORITY DECISION

- Highest authority for exact variant lineage: top10_authoritative_inventory.txt
- Highest authority for local 13-family consolidation: master_strategy_memo.txt
- Summary only: strategy_chat_seed.txt
- Workflow only: codex_master_tournament_prompt_with_top10.txt and codex_master_tournament_prompt.txt

FAMILY / VARIANT DIGEST

High-priority exact variants added by the top-10 file:
- tv_pvt_top5_finalists: tsla_30m, nvda_30m, vix_vxx_30m, vix_vxx_60m, iwm_15m
- index_opening_drive_lab: OR15 finalist, OR5 finalist
- codex_leveraged_pipeline: out_base_20260103_122420
- tv_squeeze_top5_finalists: TSLA_30m
- flux_signal_engine_top20_2025: MSFT residual survivor

Canonical local families from the memo:
- Down Streak Exhaustion
- QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System
- Durable cRSI Family
- Momentum / Relative-Strength Family
- Breakout / Trend-Continuation Family
- RSI Pullback / Z-Score Pullback / Gap Reversion Family
- Pullback in Trend Family
- Turn of Month Trend Family
- Stacked Ensemble Family
- Older Corrected Mean Reversion Baseline
- Older Corrected Day-of-Week / Vol-Regime / Breakout Baseline Cluster
- Options Vertical-Spread Wrappers
- TradingView Reference / Ideation Scripts Cluster

KNOWN CONFLICTS OR TENSIONS

1. Coverage conflict, not a direct logic conflict
- The memo does not include the exact top-10 variants from the other machine.
- The top-10 file therefore expands the universe rather than contradicting the memo.

2. Authority conflict resolved by priority
- The older prompt files describe workflow, but the dedicated top-10 file and the memo now outrank them for actual strategy truth.

3. Raw-upside versus decision-grade evidence tension inside the memo
- Momentum / Relative-Strength Family and Breakout / Trend-Continuation Family show stronger raw-table upside than the memo’s confirmed winner, but the memo explicitly warns that those rows are not the final decision-grade conclusion.
- For tournament framing, these remain promising challengers rather than trusted leaders unless reproduction overturns that caution.

4. Overfit warning consistency
- The top-10 file labels tv_squeeze_top5_finalists :: TSLA_30m as likely overfit and untrustworthy until independently validated.
- Local repo outputs in C:\Users\rabisaab\project also contain TSLA 30m sqzmom_lb watchlist/shadow artifacts, which is directionally consistent with caution rather than promotion.

5. Retired / falsified warning consistency
- The top-10 file says flux_signal_engine_top20_2025 overall was later falsified and is not suitable for options translation.
- The local memo does not cover this family, so the top-10 file becomes the controlling verdict for it unless repo evidence explicitly overturns that, which has not happened yet.

INITIAL REPO MATCH CHECK

Direct local folder matches for these exact top-10 repo names were not found during the first targeted search:
- tv_pvt_top5_finalists
- index_opening_drive_lab
- codex_leveraged_pipeline
- tv_squeeze_top5_finalists
- flux_signal_engine_top20_2025

Meaning:
- The top-10 inventory is currently authoritative even without same-name local folders.
- Later registry entries must distinguish file-backed variants from repo-verified variants.

INITIAL LOCAL REPO-BACKED STRATEGY ENGINE MATCHES ALREADY VISIBLE

- C:\Users\rabisaab\Downloads\alpaca-stock-strategy-research
  Supports Down Streak Exhaustion, Durable cRSI, Momentum / Relative-Strength, Breakout / Trend-Continuation, RSI/Z-Score/Gap Reversion, Pullback in Trend, Turn of Month, and Stacked Ensemble families.

- C:\Users\rabisaab\Downloads\nasdaq-etf-intraday-alpaca
  Supports the QQQ-Led TQQQ/SQQQ Pair Opening-Range Intraday System.

- C:\Users\rabisaab\Downloads\alpaca-strategy-research
  Supports the older corrected baselines and the options-wrapper caution branch.

- C:\Users\rabisaab\project
  Supports local repo-backed intraday research families such as smart_money_concepts, sqzmom_lb, supertrend, rsi_cyclic_smoothed, and combo workflows; this repo may partially overlap with some external inventories but does not yet prove the exact top-10 repo names.

- C:\Users\rabisaab\fvg_backtest
  Supports a Fair Value Gap backtest workflow, pending deeper verification.

- C:\Users\rabisaab\qqq_gap_prob_tool
- C:\Users\rabisaab\qqq_range_engine
- C:\Users\rabisaab\qqq_scan
- C:\Users\rabisaab\qqq_today_nowcast
  These appear to be QQQ gap/range/nowcast signal engines or supporting models rather than direct full trade strategies by default.

INGEST CONCLUSION

- All five exact files were opened successfully.
- The hard top-10 file is now the controlling source for exact ranked variants from the other machine.
- The memo remains the controlling local family consolidation for the 13 canonical families.
- The next registry step must merge both layers without collapsing lineage, and must label which entries are file-backed only versus repo-verified.
