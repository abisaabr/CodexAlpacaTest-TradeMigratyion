# GCP Research Expansion Plan

- Generated at: `2026-04-24T14:39:36.347884-04:00`
- Status: `ready_for_parallel_data_and_strategy_expansion`
- Target initial cash: `$25,000`
- Observed strategy variants: `2070`
- Target ticker count: `150`
- Ticker count: `150`
- Broker facing: `False`
- Live manifest effect: `none`
- Risk policy effect: `none`

## Search Lanes

- `smoke`: Reject broken/no-trade/pathological variants cheaply. Run all variants on compact data windows before expensive option-aware testing.
- `coarse_discovery`: Find broad edge neighborhoods across tickers and regimes. Use low-discrepancy or Latin-hypercube-like parameter coverage instead of dense grids.
- `successive_halving`: Spend compute on winners without hiding early losers. Advance only candidates with enough trades, positive after-cost expectancy, and sane drawdown.
- `local_refinement`: Promote stable neighborhoods, not one lucky parameter point. Search adjacent stops, targets, timing windows, liquidity gates, and DTE choices around survivors.
- `walk_forward_stress`: Protect against overfit and fragile market-regime dependence. Require train/test or rolling splits plus slippage, fee, and fill-coverage stress.

## Ticker Buckets

- `ticker_bucket_01` count `15`: AAPL, ABBV, ABNB, ABT, ACN, ADBE, ADI, ADP, ALB, AMAT, AMD, AMGN, AMZN, ANET, ARKK
- `ticker_bucket_02` count `15`: ASML, AVGO, AXP, BA, BABA, BAC, BIDU, BKNG, BMY, BX, C, CAT, CHWY, CL, CMCSA
- `ticker_bucket_03` count `15`: COIN, COP, COST, CRM, CRWD, CSCO, CVS, CVX, DASH, DD, DE, DIA, DIS, DKNG, DOCU
- `ticker_bucket_04` count `15`: DOW, EA, EBAY, EEM, EFA, EMR, ENPH, EWZ, F, FCX, FDX, FXI, GE, GILD, GLD
- `ticker_bucket_05` count `15`: GM, GOOG, GOOGL, GS, HD, HON, HOOD, IBM, INTC, IWM, JETS, JNJ, JPM, KO, KRE
- `ticker_bucket_06` count `15`: LOW, LULU, LYFT, MA, MARA, MCD, MDT, META, MRK, MRNA, MS, MSFT, MU, NFLX, NIO
- `ticker_bucket_07` count `15`: NKE, NOW, NVDA, ORCL, PANW, PFE, PG, PLTR, PYPL, QCOM, QQQ, RBLX, RIOT, ROKU, SBUX
- `ticker_bucket_08` count `15`: SHOP, SLV, SMCI, SNAP, SNOW, SOFI, SPY, SQ, T, TGT, TLT, TNA, TQQQ, TSLA, TSM
- `ticker_bucket_09` count `15`: U, UAL, UBER, UNG, UNH, UPS, USO, V, VIXY, VLO, VWO, VXX, WBA, WFC, WMT
- `ticker_bucket_10` count `15`: X, XBI, XHB, XLC, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY, XOM, XOP, ZM

## Promotion Contract

- Allowed transition: `research_only_to_governed_validation_candidate`
- Required: positive after-cost out-of-sample result
- Required: enough completed trades or option fills
- Required: fee and slippage stress survival
- Required: single-day PnL concentration <= 35%
- Required: stable adjacent parameter neighborhood
- Required: complete strategy metadata and reproducible code/data refs
- Required: loser taxonomy without repeated unresolved structural defect

## Execution Plan

- Build/publish the 150-ticker raw and curated data manifest.
- Run current 2070-variant 25k-account smoke on existing 5-symbol data.
- Scale to 150 tickers only after data-quality verdicts are clean enough.
- Shard strategy x ticker x parameter blocks into resumable GCP Batch jobs.
- Reduce results into a single evidence ledger and promotion packet.
