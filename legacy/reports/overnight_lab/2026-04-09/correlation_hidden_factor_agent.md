# Correlation / Hidden-Factor Review

## Verdict

`Core4` survives this review, but it is not "free breadth." It is best described as a two-bloc cyclical / risk-on cRSI portfolio, not a disguised single-factor index clone.

The old champion is still the cleanest paper-trial base because it keeps market linkage low while preserving the best target-clearing balance of PnL, drawdown, and implementation simplicity. The broader 9-name extension is real breadth, but it becomes more market-sensitive and less clean as a paper-trial base.

## What The Correlations Say

- Core4 average pairwise sleeve correlation is `0.100`.
- Core4 max pairwise sleeve correlation is `0.295` on `GE-RKLB`.
- Core4 first principal component share is `0.333`, with an effective bet count of about `3.76`.
- Core4 average active-day pair overlap is `0.548`, and the active-only mean correlation stays low at about `0.094`.

That is not the fingerprint of one hidden factor bet. It is a small portfolio with mild internal coupling.

The 9-name extension is more clustered:

- Average pairwise correlation rises to `0.120`.
- First principal component share falls to `0.229`, but the portfolio becomes more market-sensitive.
- The portfolio-to-QQQ correlation rises from `0.003` in Core4 to `0.117` in the equal-weight 9-name mix.
- The QQQ up-day vs down-day PnL gap widens from about `5.3` dollars/day to about `62.0` dollars/day on a 25k basis.

That says the breadth extension adds names, but it also adds more explicit equity beta and regime dependence.

## Cluster Structure

At a correlation threshold of `0.25`, the 9-name graph splits into two real blocs plus two satellites:

- `FCX, CAT, GE, RKLB`
- `BE, HOOD, XLY`
- `CRM`
- `XBI`

Within-bloc average correlations are about:

- `0.244` for the `FCX/CAT/GE/RKLB` bloc
- `0.271` for the `BE/HOOD/XLY` bloc

Cross-bloc correlations are much weaker, around `0.087` on average. This is the key hidden-factor result: the book is not one monolithic factor, but it is also not nine independent bets.

The strongest individual pairwise links are:

- `HOOD-XLY` at `0.476`
- `GE-CAT` at `0.466`
- `FCX-CAT` at `0.425`
- `GE-RKLB` at `0.295`

Those pairs explain most of the visible clustering.

## Concentration Contribution

Using the stored daily sleeve-return matrix as a relative contribution proxy:

- Core4 relative contribution HHI is `0.291`.
- Core4 top sleeve share is `41.6%` for `BE`.
- Core4 top two sleeves share is `64.9%`.
- Core4 top three sleeves share is `85.8%`.

That is concentrated, but not absurdly so for a four-name alpha basket.

For the 9-name mix:

- Relative contribution HHI falls to `0.143`.
- Top sleeve share falls to `25.8%`.
- Top two sleeves share falls to `40.3%`.
- Top three sleeves share falls to `53.3%`.

So breadth does reduce single-sleeve dependence. The problem is that it also raises market sensitivity and weakens the target-clearing edge.

## Regime Sensitivity

Core4 is close to market-neutral on the saved replay:

- `portfolio_vs_qqq_corr = 0.003`
- `avg_pnl_qqq_up_days_25k = 213.45`
- `avg_pnl_qqq_down_days_25k = 208.10`

That looks like a local overnight mean-reversion edge with little direct index dependence.

The broader 9-name mix looks more like a risk-on sleeve book:

- `portfolio_vs_qqq_corr = 0.117`
- `avg_pnl_qqq_up_days_25k = 178.63`
- `avg_pnl_qqq_down_days_25k = 116.62`

That is still potentially tradable, but it is no longer the same clean market-neutral shape as Core4.

## Practical Read

Core4 is diversified enough for a paper trial and not so correlated that it becomes a fake portfolio. The hidden-factor risk is real, but it is a manageable cluster risk, not a collapse into one disguised ticker.

CAT looks like a useful later breadth seed, not a new independent alpha source. It belongs in the industrial/cyclical bloc, so it broadens the set without really changing the factor DNA.

## Uncertainty

This review uses the saved `2026-01-05` to `2026-04-02` replay artifacts and scoreboards in this workspace. I did not have a broader-history rebuild in this turn, so the regime conclusions are still replay-window conclusions, not a multi-year proof.
