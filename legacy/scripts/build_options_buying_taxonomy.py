#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

MASTER_PATH = DATA_DIR / "options_buying_strategies_master.csv"
EXCLUDED_PATH = DATA_DIR / "options_buying_strategies_excluded_audit.csv"
SOURCES_PATH = DATA_DIR / "options_buying_strategies_sources.csv"

CORE_PATH = DATA_DIR / "options_buying_strategies_core_long_premium.csv"
DEBIT_PATH = DATA_DIR / "options_buying_strategies_debit_structures.csv"
HYBRID_PATH = DATA_DIR / "options_buying_strategies_stock_hybrids.csv"
REVIEW_PATH = DATA_DIR / "options_buying_strategies_manual_review.csv"
REPORT_PATH = REPORTS_DIR / "options_buying_strategies_taxonomy.md"

DERIVED_COLUMNS = [
    "core_research_bucket",
    "long_gamma_bias",
    "long_vega_bias",
    "positive_theta_possible",
    "requires_stock_inventory",
    "small_account_feasible",
    "american_early_assignment_material",
    "expiration_sensitivity",
    "preferred_market_regime",
    "typical_holding_period",
    "manual_review_required",
    "manual_review_reason",
]


def bool_text(value: bool) -> str:
    return "true" if value else "false"


RULES: dict[str, dict[str, str | bool]] = {
    "long call": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": False,
        "expiration_sensitivity": "high",
        "preferred_market_regime": "bullish_trend_or_breakout",
        "typical_holding_period": "days_to_weeks",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long put": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": False,
        "expiration_sensitivity": "high",
        "preferred_market_regime": "bearish_trend_or_breakdown",
        "typical_holding_period": "days_to_weeks",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long straddle": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": False,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "event_driven_breakout_or_vol_expansion",
        "typical_holding_period": "event_window_to_days",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long strangle": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": False,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "event_driven_breakout_or_vol_expansion",
        "typical_holding_period": "event_window_to_days",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "bull call spread": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "mixed",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "medium",
        "preferred_market_regime": "moderate_bullish_trend",
        "typical_holding_period": "days_to_weeks",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "bear put spread": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "mixed",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": True,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "medium",
        "preferred_market_regime": "moderate_bearish_trend",
        "typical_holding_period": "days_to_weeks",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "protective put": {
        "core_research_bucket": "stock_hybrid",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": True,
        "small_account_feasible": False,
        "american_early_assignment_material": False,
        "expiration_sensitivity": "medium",
        "preferred_market_regime": "long_equity_with_downside_hedge_need",
        "typical_holding_period": "weeks_to_months",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "collar": {
        "core_research_bucket": "stock_hybrid",
        "long_gamma_bias": "mixed",
        "long_vega_bias": "mixed",
        "positive_theta_possible": True,
        "requires_stock_inventory": True,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "medium",
        "preferred_market_regime": "long_equity_with_defined_exit_band",
        "typical_holding_period": "weeks_to_months",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long butterfly": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "short_gamma",
        "long_vega_bias": "short_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "range_bound_stable_or_falling_vol",
        "typical_holding_period": "days_to_expiration",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long condor": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "short_gamma",
        "long_vega_bias": "short_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "range_bound_stable_or_falling_vol",
        "typical_holding_period": "days_to_expiration",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long iron butterfly": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "event_driven_breakout_or_vol_expansion",
        "typical_holding_period": "event_window_to_days",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long iron condor": {
        "core_research_bucket": "core_long_premium",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": False,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "event_driven_breakout_or_vol_expansion",
        "typical_holding_period": "event_window_to_days",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long calendar spread": {
        "core_research_bucket": "manual_review",
        "long_gamma_bias": "mixed",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "pin_near_short_strike_with_stable_to_rising_vol",
        "typical_holding_period": "days_to_front_expiration",
        "manual_review_required": True,
        "manual_review_reason": "Call and put variants were merged in the first pass, and calendar spreads can flip between positive-theta carry and long-vega research depending on strike placement and time horizon.",
    },
    "long diagonal spread": {
        "core_research_bucket": "manual_review",
        "long_gamma_bias": "mixed",
        "long_vega_bias": "mixed",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "slow_trend_toward_short_strike_with_term_structure_edge",
        "typical_holding_period": "days_to_front_expiration",
        "manual_review_required": True,
        "manual_review_reason": "Directional call and put diagonal variants were merged, but their realized gamma/theta mix can differ materially by strike selection and front-leg management.",
    },
    "double diagonal spread": {
        "core_research_bucket": "manual_review",
        "long_gamma_bias": "short_gamma",
        "long_vega_bias": "mixed",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "range_bound_with_careful_term_structure_management",
        "typical_holding_period": "days_to_front_expiration",
        "manual_review_required": True,
        "manual_review_reason": "This is an advanced debit structure with strong front-leg management effects, so it is better isolated for manual review than treated as a clean long-premium research primitive.",
    },
    "long ratio backspread": {
        "core_research_bucket": "manual_review",
        "long_gamma_bias": "long_gamma",
        "long_vega_bias": "long_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "sharp_directional_move_or_volatility_expansion",
        "typical_holding_period": "event_window_to_days",
        "manual_review_required": True,
        "manual_review_reason": "Backspreads can be opened for either a debit or a credit and the short strike dominates path risk, so they are too structurally mixed for an automatic long-premium bucket.",
    },
    "long christmas tree spread": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "short_gamma",
        "long_vega_bias": "short_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "range_bound_stable_or_falling_vol",
        "typical_holding_period": "days_to_expiration",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
    "long christmas tree spread variation": {
        "core_research_bucket": "debit_structure",
        "long_gamma_bias": "short_gamma",
        "long_vega_bias": "short_vega",
        "positive_theta_possible": True,
        "requires_stock_inventory": False,
        "small_account_feasible": False,
        "american_early_assignment_material": True,
        "expiration_sensitivity": "very_high",
        "preferred_market_regime": "range_bound_stable_or_falling_vol",
        "typical_holding_period": "days_to_expiration",
        "manual_review_required": False,
        "manual_review_reason": "",
    },
}


STARTER_UNIVERSE = [
    "long call",
    "long put",
    "bull call spread",
    "bear put spread",
    "long straddle",
    "long strangle",
]


def add_derived_columns(master: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(master["canonical_name"]) - set(RULES))
    if missing:
        raise ValueError(f"Missing taxonomy rules for: {missing}")

    derived = master.copy()
    for column in DERIVED_COLUMNS:
        derived[column] = ""

    for index, row in derived.iterrows():
        rule = RULES[row["canonical_name"]]
        for column, value in rule.items():
            if isinstance(value, bool):
                derived.at[index, column] = bool_text(value)
            else:
                derived.at[index, column] = value
    return derived


def write_subset(df: pd.DataFrame, bucket: str, path: Path) -> None:
    subset = df[df["core_research_bucket"] == bucket].copy()
    subset.sort_values(["canonical_name", "strategy_name"], inplace=True)
    subset.to_csv(path, index=False)


def render_report(
    derived: pd.DataFrame,
    excluded: pd.DataFrame,
    source_summary: pd.DataFrame,
) -> str:
    bucket_counts = derived["core_research_bucket"].value_counts().to_dict()
    manual = derived[derived["core_research_bucket"] == "manual_review"].copy()
    not_good = derived[derived["core_research_bucket"] != "core_long_premium"].copy()
    excluded_watch = excluded[
        excluded["canonical_name"].isin(["cash-backed call", "long skip-strike butterfly"])
    ][["canonical_name", "exclude_reason"]].drop_duplicates()

    lines = [
        "# Options Buying Strategies Taxonomy",
        "",
        "## Final Counts By Bucket",
        f"- core_long_premium: {bucket_counts.get('core_long_premium', 0)}",
        f"- debit_structure: {bucket_counts.get('debit_structure', 0)}",
        f"- stock_hybrid: {bucket_counts.get('stock_hybrid', 0)}",
        f"- manual_review: {bucket_counts.get('manual_review', 0)}",
        "",
        "## Strategies Moved To Manual Review",
    ]
    for _, row in manual.sort_values("canonical_name").iterrows():
        support = source_summary.get(row["canonical_name"], "")
        support_text = f" | sources: {support}" if support else ""
        lines.append(f"- `{row['canonical_name']}`: {row['manual_review_reason']}{support_text}")

    lines.extend(
        [
            "",
            "## Included Strategies That Are Not Strong Long-Premium Research Candidates",
            "- `debit_structure` bucket: these are debit entries, but practical exposure is often neutral, carry-driven, or short-volatility despite the upfront debit.",
            "- `stock_hybrid` bucket: these require stock plus options and behave more like hedging overlays than standalone long-premium trades.",
            "- `manual_review` bucket: these are structurally mixed and should be normalized further before systematic testing.",
        ]
    )
    for _, row in not_good.sort_values(["core_research_bucket", "canonical_name"]).iterrows():
        lines.append(
            f"- `{row['canonical_name']}` -> `{row['core_research_bucket']}`"
        )

    lines.extend(["", "## Recommended Starter Universe For Systematic Testing"])
    for name in STARTER_UNIVERSE:
        row = derived.loc[derived["canonical_name"] == name].iloc[0]
        lines.append(
            f"- `{name}`: {row['preferred_market_regime']}, typical holding period `{row['typical_holding_period']}`."
        )

    lines.extend(
        [
            "",
            "## Provenance Notes",
            "- All derived CSVs retain the original source/provenance columns from the first-pass master file.",
            "- The sources table was used here to keep manual-review items visible where source coverage was thin or variant-heavy.",
        ]
    )
    if not excluded_watch.empty:
        lines.append("- Adjacent excluded watchlist items worth separate future review:")
        for _, row in excluded_watch.iterrows():
            lines.append(f"- `{row['canonical_name']}`: {row['exclude_reason']}")

    return "\n".join(lines) + "\n"


def main() -> None:
    master = pd.read_csv(MASTER_PATH).fillna("")
    excluded = pd.read_csv(EXCLUDED_PATH).fillna("")
    sources = pd.read_csv(SOURCES_PATH).fillna("")

    derived = add_derived_columns(master)
    source_summary = (
        sources.groupby("canonical_name")["source_name"]
        .agg(lambda s: "; ".join(sorted(set(s))))
        .to_dict()
    )

    write_subset(derived, "core_long_premium", CORE_PATH)
    write_subset(derived, "debit_structure", DEBIT_PATH)
    write_subset(derived, "stock_hybrid", HYBRID_PATH)
    write_subset(derived, "manual_review", REVIEW_PATH)
    REPORT_PATH.write_text(render_report(derived, excluded, source_summary), encoding="utf-8")

    counts = derived["core_research_bucket"].value_counts().to_dict()
    print("Files written:")
    print(f"- {CORE_PATH}")
    print(f"- {DEBIT_PATH}")
    print(f"- {HYBRID_PATH}")
    print(f"- {REVIEW_PATH}")
    print(f"- {REPORT_PATH}")
    print("")
    print("Bucket counts:")
    for bucket in ["core_long_premium", "debit_structure", "stock_hybrid", "manual_review"]:
        print(f"- {bucket}: {counts.get(bucket, 0)}")


if __name__ == "__main__":
    main()
