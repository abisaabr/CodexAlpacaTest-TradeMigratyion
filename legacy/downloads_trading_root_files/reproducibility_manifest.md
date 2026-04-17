# Reproducibility Manifest

- Exact-file ingest order respected: `top10_authoritative_inventory.txt`, `master_strategy_memo.txt`, `strategy_chat_seed.txt`, `codex_master_tournament_prompt_with_top10.txt`, `codex_master_tournament_prompt.txt`.
- Standardized 5-year daily underlying window: `2021-03-24` through `2026-03-24` from the local stock feature parquet.
- Symbols covered in the standardized daily tournament: `SPY, QQQ, IWM, NVDA, META, AAPL, AMZN, NFLX, TSLA`. `GOOG` was missing from the local feature set; the local repo contains `GOOGL` instead.
- Intraday pair baseline reproduction window: validation `2025-07-01` to `2025-12-31`, test `2026-01-02` to `2026-04-01` using local minute research cache.
- Honest options blocker: verified Alpaca historical option quotes remain unavailable; local option minute data on disk is a recent, partial, SPY-focused pocket rather than a full 5-year cross-symbol archive.