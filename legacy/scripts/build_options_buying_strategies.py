#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
CACHE_DIR = DATA_DIR / "cache" / "options_buying_strategies"

MASTER_CSV = DATA_DIR / "options_buying_strategies_master.csv"
EXCLUDED_CSV = DATA_DIR / "options_buying_strategies_excluded_audit.csv"
SOURCES_CSV = DATA_DIR / "options_buying_strategies_sources.csv"
SUMMARY_MD = REPORTS_DIR / "options_buying_strategies_summary.md"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

MASTER_COLUMNS = [
    "strategy_name",
    "canonical_name",
    "aliases",
    "source_name",
    "source_title",
    "source_url",
    "source_type",
    "strategy_family",
    "classification",
    "net_premium_type",
    "directional_bias",
    "volatility_bias",
    "time_decay_bias",
    "legs_summary",
    "uses_calls",
    "uses_puts",
    "uses_stock",
    "min_legs",
    "max_legs",
    "defined_risk",
    "defined_reward",
    "typical_outlook",
    "entry_debit_or_credit",
    "max_profit_summary",
    "max_loss_summary",
    "breakeven_summary",
    "exercise_assignment_risk",
    "american_assignment_relevant",
    "common_use_case",
    "complexity_level",
    "margin_notes",
    "notes",
    "dedupe_key",
    "is_options_buying_strategy",
    "include_reason",
    "exclude_reason",
]

SOURCE_COLUMNS = [
    "strategy_name",
    "canonical_name",
    "source_name",
    "source_title",
    "source_url",
    "source_type",
    "collection_method",
    "is_live_fetched",
    "strategy_family",
    "classification",
    "is_options_buying_strategy",
    "dedupe_key",
    "source_notes",
]

SOURCE_PRIORITY = {"OIC": 0, "Fidelity": 1, "Cboe": 2, "Schwab": 3}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.replace("\xa0", " ").split())


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def slugify(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_")


def split_alias_text(value: str | None) -> list[str]:
    if not value:
        return []
    aliases: list[str] = []
    for piece in value.split(";"):
        item = clean_text(piece)
        if item and item not in aliases:
            aliases.append(item)
    return aliases


def merge_aliases(*groups: list[str]) -> str:
    seen: list[str] = []
    for group in groups:
        for item in group:
            alias = clean_text(item)
            if alias and alias not in seen:
                seen.append(alias)
    return "; ".join(seen)


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_with_cache(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    html_path = CACHE_DIR / f"{digest}.html"
    meta_path = CACHE_DIR / f"{digest}.json"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")

    response = requests.get(url, headers=HEADERS, timeout=45)
    response.raise_for_status()
    html_path.write_text(response.text, encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "url": url,
                "final_url": response.url,
                "status_code": response.status_code,
                "fetched_at_utc": datetime.now(UTC).isoformat(),
                "content_type": response.headers.get("content-type", ""),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return response.text


def parse_section_blocks(main: BeautifulSoup) -> dict[str, str]:
    sections: dict[str, str] = {}
    for header in main.select("h3"):
        title = clean_text(header.get_text(" ", strip=True))
        body_parts: list[str] = []
        sibling = header.find_next_sibling()
        while sibling and getattr(sibling, "name", None) not in {"h1", "h2", "h3"}:
            body = clean_text(sibling.get_text(" ", strip=True))
            if body:
                body_parts.append(body)
            sibling = sibling.find_next_sibling()
        if title:
            sections[title] = " ".join(body_parts)
    return sections


def parse_highlights(text: str) -> dict[str, str]:
    labels = [
        "Motivation",
        "Market Outlook",
        "High Volatility Expectation",
        "Volatility Expectation",
        "Maximum Gain",
        "Maximum Loss",
        "Time Decay",
        "Volatility Impact",
        "Exercise/Assignment Risk",
        "Assignment Risk",
        "Expiration Scenarios",
    ]
    positions: list[tuple[int, str]] = []
    for label in labels:
        idx = text.find(label)
        if idx != -1:
            positions.append((idx, label))
    positions.sort()

    result: dict[str, str] = {}
    for i, (start, label) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        result[label] = clean_text(text[start + len(label) : end])
    return result


def extract_parenthetical_aliases(name: str) -> list[str]:
    matches = re.findall(r"\(([^)]+)\)", name)
    aliases: list[str] = []
    for match in matches:
        for piece in match.split(","):
            alias = clean_text(piece)
            if alias and alias not in aliases:
                aliases.append(alias)
    return aliases


def strip_parenthetical(name: str) -> str:
    return clean_text(re.sub(r"\s*\([^)]*\)", "", name))


def family_from_name(name: str) -> str:
    lowered = name.lower()
    if "straddle" in lowered:
        return "straddle"
    if "strangle" in lowered:
        return "strangle"
    if "collar" in lowered:
        return "collar"
    if "calendar" in lowered or "horizontal" in lowered:
        return "calendar"
    if "diagonal" in lowered:
        return "diagonal"
    if "butterfly" in lowered or "christmas tree" in lowered:
        return "butterfly"
    if "condor" in lowered:
        return "condor"
    if "ratio" in lowered or "back spread" in lowered or "backspread" in lowered:
        return "backspread"
    if (
        "vertical" in lowered
        or "bull call spread" in lowered
        or "bear put spread" in lowered
        or "bear call spread" in lowered
        or "bull put spread" in lowered
        or ("call spread" in lowered and "ratio" not in lowered)
        or ("put spread" in lowered and "ratio" not in lowered)
    ):
        return "vertical"
    if any(token in lowered for token in ["synthetic", "stock"]):
        return "synthetic"
    if any(token in lowered for token in ["call", "put"]):
        return "single_leg"
    return "other"


def parse_time_decay_bias(text: str) -> str:
    lowered = text.lower()
    if not lowered:
        return "unknown"
    if "positive" in lowered and "negative" in lowered:
        return "mixed"
    if "positive" in lowered or "profits from time decay" in lowered:
        return "positive_theta"
    if "negative" in lowered or "lose money from time erosion" in lowered:
        return "negative_theta"
    if "offset" in lowered or "not a major consideration" in lowered or "roughly offset" in lowered:
        return "mixed"
    return "unknown"


def parse_volatility_bias(text: str) -> str:
    lowered = text.lower()
    if not lowered:
        return "unknown"
    if "positive impact" in lowered or "positive vega" in lowered or "fueled by an increase" in lowered:
        return "long_vol"
    if "negative impact" in lowered or "negative vega" in lowered or "falls when implied volatility rises" in lowered:
        return "short_vol"
    if "offset" in lowered or "mixed" in lowered:
        return "mixed"
    return "unknown"


def infer_uses(strategy_name: str, summary: str) -> tuple[bool, bool, bool]:
    lowered = f"{strategy_name} {summary}".lower()
    return ("call" in lowered, "put" in lowered, "stock" in lowered or "shares" in lowered)


def infer_legs(strategy_family: str, strategy_name: str, uses_stock: bool) -> tuple[int | None, int | None]:
    lowered = strategy_name.lower()
    if strategy_family == "single_leg":
        return (2, 2) if uses_stock else (1, 1)
    if strategy_family in {"vertical", "calendar", "diagonal"}:
        return (2, 2)
    if strategy_family in {"straddle", "strangle"}:
        return (2, 2)
    if strategy_family == "collar":
        return (3, 3)
    if strategy_family == "butterfly":
        return (6, 6) if "christmas tree" in lowered else (4, 4)
    if strategy_family == "condor":
        return (4, 4)
    if strategy_family == "backspread":
        return (3, 3)
    return (None, None)


def infer_defined_reward(text: str) -> bool:
    lowered = text.lower()
    return bool(lowered) and "limited" in lowered and "unlimited" not in lowered and "substantial" not in lowered


def infer_defined_risk(text: str) -> bool:
    lowered = text.lower()
    if not lowered or "unlimited" in lowered:
        return False
    return any(token in lowered for token in ["limited", "premium paid", "net cost", "debit", "cost of the strategy"])


def choose_representative(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            SOURCE_PRIORITY.get(row["source_name"], 99),
            row["source_name"],
            row["source_title"],
            row["strategy_name"],
        ),
    )[0]


def normalize_direction_for_excluded(name: str, outlook: str) -> str:
    lowered = f"{name} {outlook}".lower()
    if "bull" in lowered:
        return "bullish"
    if "bear" in lowered:
        return "bearish"
    if "neutral" in lowered:
        return "neutral"
    if "volatility" in lowered or "either direction" in lowered or "up or down" in lowered:
        return "volatility_up"
    if "mixed" in lowered:
        return "mixed"
    return "unknown"


def default_margin_notes(strategy_family: str, is_included: bool, uses_stock: bool) -> str:
    if uses_stock:
        return "Stock financing or fully paid stock can drive capital needs alongside any option premium."
    if strategy_family in {"single_leg", "straddle", "strangle"} and is_included:
        return "Typically premium paid upfront; no additional option margin beyond the long premium for standard long equity options."
    if strategy_family in {"vertical", "calendar", "diagonal", "butterfly", "condor", "backspread"} and is_included:
        return "Spread approval is typically required; short legs can create temporary assignment or stock exposure even when entry is a net debit."
    return "Margin treatment depends on the short-option or stock components of the structure."


def canonical_from_name(name: str) -> str:
    lowered = clean_text(strip_parenthetical(name)).lower()
    manual = {
        "long call": "long call",
        "buying index calls": "long call",
        "long put": "long put",
        "buying index puts": "long put",
        "long straddle": "long straddle",
        "long strangle": "long strangle",
        "protective put": "protective put",
        "married put": "protective put",
        "collar": "collar",
        "bull call spread": "bull call spread",
        "bear put spread": "bear put spread",
        "long call calendar spread": "long calendar spread",
        "long put calendar spread": "long calendar spread",
        "long calendar spread with calls": "long calendar spread",
        "long calendar spread with puts": "long calendar spread",
        "long diagonal spread with calls": "long diagonal spread",
        "long diagonal spread with puts": "long diagonal spread",
        "double diagonal spread": "double diagonal spread",
        "long call butterfly": "long butterfly",
        "long put butterfly": "long butterfly",
        "long butterfly spread with calls": "long butterfly",
        "long butterfly spread with puts": "long butterfly",
        "long call condor": "long condor",
        "long put condor": "long condor",
        "long condor spread with calls": "long condor",
        "long condor spread with puts": "long condor",
        "long iron butterfly": "long iron butterfly",
        "long iron butterfly spread": "long iron butterfly",
        "long condor": "long iron condor",
        "long iron condor spread": "long iron condor",
        "long ratio call spread": "long ratio backspread",
        "long ratio put spread": "long ratio backspread",
        "1x2 ratio volatility spread with calls": "long ratio backspread",
        "1x2 ratio volatility spread with puts": "long ratio backspread",
        "long christmas tree spread with calls": "long christmas tree spread",
        "long christmas tree spread with puts": "long christmas tree spread",
        "long christmas tree spread variation with calls": "long christmas tree spread variation",
        "long christmas tree spread variation with puts": "long christmas tree spread variation",
        "long skip-strike butterfly spread with calls": "long skip-strike butterfly",
        "long skip-strike butterfly spread with puts": "long skip-strike butterfly",
        "cash-backed call": "cash-backed call",
        "cash-secured put": "cash-secured put",
        "covered call": "covered call",
        "covered put": "covered put",
        "covered ratio spread": "covered ratio spread",
        "covered strangle": "covered strangle",
        "double bull spread": "double bull spread",
        "bear spread spread": "double bear spread",
        "long stock": "long stock",
        "naked call": "short call",
        "naked put": "short put",
        "short call butterfly": "short butterfly",
        "short put butterfly": "short butterfly",
        "short call calendar spread": "short calendar spread",
        "short put calendar spread": "short calendar spread",
        "short condor": "short iron condor",
        "short iron butterfly": "short iron butterfly",
        "short ratio call spread": "short ratio spread",
        "short ratio put spread": "short ratio spread",
        "short stock": "short stock",
        "short straddle": "short straddle",
        "short strangle": "short strangle",
        "stock repair": "stock repair",
        "synthetic long put": "synthetic long put",
        "synthetic long stock": "synthetic long stock",
        "synthetic short stock": "synthetic short stock",
    }
    return manual.get(lowered, lowered)


INCLUDED_CANONICALS = {
    "long call",
    "long put",
    "long straddle",
    "long strangle",
    "protective put",
    "collar",
    "bull call spread",
    "bear put spread",
    "long calendar spread",
    "long diagonal spread",
    "double diagonal spread",
    "long butterfly",
    "long condor",
    "long iron butterfly",
    "long iron condor",
    "long ratio backspread",
    "long christmas tree spread",
    "long christmas tree spread variation",
}


CANONICAL_PROFILES = {
    "long call": {
        "aliases": ["bought call", "buying index calls"],
        "strategy_family": "single_leg",
        "classification": "pure_long_premium",
        "net_premium_type": "debit",
        "directional_bias": "bullish",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Buy 1 call option; index-option variant also observed in source pages.",
        "uses_calls": True,
        "uses_puts": False,
        "uses_stock": False,
        "min_legs": 1,
        "max_legs": 1,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Bullish directional upside view with limited downside to premium paid.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Upside profit is theoretically unlimited after recovering the premium paid.",
        "max_loss_summary": "Maximum loss is limited to the option premium paid.",
        "breakeven_summary": "Breakeven at expiration is strike plus premium paid.",
        "exercise_assignment_risk": "No short-leg assignment risk; a long in-the-money option can be exercised or auto-exercised at expiration.",
        "american_assignment_relevant": False,
        "common_use_case": "Directional upside speculation or leveraged upside exposure with capped loss.",
        "complexity_level": "basic",
        "margin_notes": "Typically premium paid upfront; no additional option margin beyond the long premium for standard long equity options.",
        "notes": "Canonical row merges equity and index-option source variants.",
        "include_reason": "Pure long-option strategy funded by purchased premium.",
    },
    "long put": {
        "aliases": ["bought put", "buying index puts"],
        "strategy_family": "single_leg",
        "classification": "pure_long_premium",
        "net_premium_type": "debit",
        "directional_bias": "bearish",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Buy 1 put option; index-option variant also observed in source pages.",
        "uses_calls": False,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 1,
        "max_legs": 1,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Bearish directional downside view with limited downside to premium paid.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Profit grows as the underlying falls, bounded only by a move toward zero.",
        "max_loss_summary": "Maximum loss is limited to the option premium paid.",
        "breakeven_summary": "Breakeven at expiration is strike minus premium paid.",
        "exercise_assignment_risk": "No short-leg assignment risk; a long in-the-money option can be exercised or auto-exercised at expiration.",
        "american_assignment_relevant": False,
        "common_use_case": "Directional downside speculation or downside hedge with capped loss.",
        "complexity_level": "basic",
        "margin_notes": "Typically premium paid upfront; no additional option margin beyond the long premium for standard long equity options.",
        "notes": "Canonical row merges equity and index-option source variants.",
        "include_reason": "Pure long-option strategy funded by purchased premium.",
    },
    "long straddle": {
        "aliases": [],
        "strategy_family": "straddle",
        "classification": "pure_long_premium",
        "net_premium_type": "debit",
        "directional_bias": "volatility_up",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Buy 1 call and 1 put with the same strike and expiration.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Expect a sharp move in either direction and/or a rise in implied volatility.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Upside profit is unlimited and downside profit can be substantial if the move is large enough.",
        "max_loss_summary": "Maximum loss is limited to the combined premiums paid.",
        "breakeven_summary": "Two expiration breakevens: strike plus total premium and strike minus total premium.",
        "exercise_assignment_risk": "No short-leg assignment risk; in-the-money long legs can be exercised or auto-exercised at expiration.",
        "american_assignment_relevant": False,
        "common_use_case": "Directional uncertainty but strong conviction that realized or implied volatility will rise.",
        "complexity_level": "basic",
        "margin_notes": "Premium paid upfront; no additional option margin beyond the two long-option premiums.",
        "notes": "",
        "include_reason": "Pure long-premium volatility strategy using only purchased options.",
    },
    "long strangle": {
        "aliases": ["long combination"],
        "strategy_family": "strangle",
        "classification": "pure_long_premium",
        "net_premium_type": "debit",
        "directional_bias": "volatility_up",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Buy 1 call and 1 put with different strikes and the same expiration.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Expect a large move in either direction and/or higher implied volatility with lower upfront cost than a straddle.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Upside profit is unlimited and downside profit can be substantial if the move is large enough.",
        "max_loss_summary": "Maximum loss is limited to total premiums paid.",
        "breakeven_summary": "Two expiration breakevens: call strike plus premium and put strike minus premium.",
        "exercise_assignment_risk": "No short-leg assignment risk; in-the-money long legs can be exercised or auto-exercised at expiration.",
        "american_assignment_relevant": False,
        "common_use_case": "Cheaper long-volatility alternative to a straddle when a very large move is expected.",
        "complexity_level": "basic",
        "margin_notes": "Premium paid upfront; no additional option margin beyond the two long-option premiums.",
        "notes": "",
        "include_reason": "Pure long-premium volatility strategy using only purchased options.",
    },
    "protective put": {
        "aliases": ["married put", "long stock + long put"],
        "strategy_family": "combo",
        "classification": "hybrid_or_protective",
        "net_premium_type": "debit",
        "directional_bias": "bullish",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Hold long stock and buy 1 protective put against it.",
        "uses_calls": False,
        "uses_puts": True,
        "uses_stock": True,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Bullish or long-stock outlook with a desire to cap downside risk.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Stock upside remains open, reduced by the cost of the put.",
        "max_loss_summary": "Downside is capped below the put strike, adjusted for stock basis and put cost.",
        "breakeven_summary": "Breakeven is long-stock basis plus the put premium paid.",
        "exercise_assignment_risk": "No short-option assignment risk; the long put can be exercised or auto-exercised if in the money.",
        "american_assignment_relevant": False,
        "common_use_case": "Hedge an existing or simultaneous long stock position while keeping upside exposure.",
        "complexity_level": "intermediate",
        "margin_notes": "Requires capital for the long stock position plus the put premium; stock financing can dominate capital usage.",
        "notes": "Included as a named protective structure rather than a pure standalone premium-buying trade.",
        "include_reason": "Named protective structure with a purchased option and clear downside-hedging use case.",
    },
    "collar": {
        "aliases": ["protective collar"],
        "strategy_family": "collar",
        "classification": "hybrid_or_protective",
        "net_premium_type": "variable",
        "directional_bias": "bullish",
        "volatility_bias": "mixed",
        "time_decay_bias": "mixed",
        "legs_summary": "Hold long stock, buy 1 put, and sell 1 covered call.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": True,
        "min_legs": 3,
        "max_legs": 3,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Long-stock holder seeking downside protection while capping upside.",
        "entry_debit_or_credit": "variable",
        "max_profit_summary": "Upside is capped by the short call, adjusted for the net opening cash flow.",
        "max_loss_summary": "Downside is limited below the put strike, adjusted for stock basis and net opening cash flow.",
        "breakeven_summary": "Breakeven depends on the stock basis and whether the collar was opened for a net debit or net credit.",
        "exercise_assignment_risk": "The covered short call can be assigned early, especially around dividends; the long put is under the holder's control.",
        "american_assignment_relevant": True,
        "common_use_case": "Hedge a long stock position for a period while partially financing protection with a covered call.",
        "complexity_level": "intermediate",
        "margin_notes": "Stock position plus covered short call approval required; net cash flow can be a debit or a credit depending on strikes.",
        "notes": "Included as a hybrid/protective structure because it clearly contains a bought option and is explicitly documented as a named strategy.",
        "include_reason": "Named protective structure with a bought put that is useful to track separately from pure long-premium trades.",
        "manual_review_reason": "Hybrid stock-plus-options hedge with variable debit/credit economics, so keep separate from pure premium-buying definitions.",
    },
    "bull call spread": {
        "aliases": ["debit call spread", "long call vertical"],
        "strategy_family": "vertical",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "bullish",
        "volatility_bias": "mixed",
        "time_decay_bias": "mixed",
        "legs_summary": "Buy 1 call and sell 1 higher-strike call with the same expiration.",
        "uses_calls": True,
        "uses_puts": False,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Moderately bullish outlook with a desire to reduce upfront premium versus an outright long call.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is capped at strike width minus net debit.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Expiration breakeven is long-call strike plus net debit.",
        "exercise_assignment_risk": "The short call can be assigned early in American-style equity options, especially around dividends.",
        "american_assignment_relevant": True,
        "common_use_case": "Moderate upside trade with limited risk and lower premium outlay than a naked long call.",
        "complexity_level": "basic",
        "margin_notes": "Typically entered for a net debit; the long call defines risk on the short call as a spread.",
        "notes": "",
        "include_reason": "Common named debit spread in which purchased premium is the main exposure.",
    },
    "bear put spread": {
        "aliases": ["debit put spread", "long put vertical"],
        "strategy_family": "vertical",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "bearish",
        "volatility_bias": "mixed",
        "time_decay_bias": "mixed",
        "legs_summary": "Buy 1 put and sell 1 lower-strike put with the same expiration.",
        "uses_calls": False,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Moderately bearish outlook with lower upfront premium than an outright long put.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is capped at strike width minus net debit.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Expiration breakeven is long-put strike minus net debit.",
        "exercise_assignment_risk": "The short put can be assigned early in American-style equity options when it is deep in the money.",
        "american_assignment_relevant": True,
        "common_use_case": "Moderate downside trade with limited risk and lower cost than a naked long put.",
        "complexity_level": "basic",
        "margin_notes": "Typically entered for a net debit; the long put defines risk on the short put as a spread.",
        "notes": "",
        "include_reason": "Common named debit spread in which purchased premium is the main exposure.",
    },
    "long calendar spread": {
        "aliases": ["long call calendar spread", "call horizontal", "long put calendar spread", "put horizontal", "time spread", "horizontal spread", "long calendar spread with calls", "long calendar spread with puts"],
        "strategy_family": "calendar",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "mixed",
        "volatility_bias": "long_vol",
        "time_decay_bias": "mixed",
        "legs_summary": "Buy a longer-dated option and sell a shorter-dated option of the same type; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Neutral to modestly directional view toward the strike, with interest in front-month decay and/or higher implied volatility.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Profit tends to peak near the short strike around front-month expiration, but realized maximum depends on the remaining long-option value and volatility.",
        "max_loss_summary": "Maximum loss is generally limited to the net debit paid if the spread value collapses.",
        "breakeven_summary": "Breakeven is path-dependent and varies with underlying price, implied volatility, and time remaining in the long option.",
        "exercise_assignment_risk": "The short near-term option can be assigned early, potentially creating stock exposure before the long leg is exercised or the spread is closed.",
        "american_assignment_relevant": True,
        "common_use_case": "Seek positive short-leg theta while retaining longer-dated optionality and vega exposure.",
        "complexity_level": "advanced",
        "margin_notes": "Spread approval is typically required; assignment on the short leg can create temporary stock and margin exposure.",
        "notes": "Canonical row merges call and put variants because the sources document both as long calendar/time spreads.",
        "include_reason": "Common named net-debit spread with purchased longer-dated premium as the main exposure.",
        "manual_review_reason": "Merged call and put variants have different directional tilts and time-decay behavior away from the strike.",
    },
    "long diagonal spread": {
        "aliases": ["diagonal debit spread", "long diagonal spread with calls", "long diagonal spread with puts"],
        "strategy_family": "diagonal",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "mixed",
        "volatility_bias": "mixed",
        "time_decay_bias": "mixed",
        "legs_summary": "Buy a longer-dated option and sell a shorter-dated option at a different strike; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 2,
        "max_legs": 2,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Neutral to modestly directional view toward the short strike with a desire to harvest front-month decay.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Profit is generally best near the short strike around front expiration; realized maximum depends on the value of the long option.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid if the structure fails to retain value.",
        "breakeven_summary": "Breakeven is path-dependent and varies with strike placement, volatility, and time remaining in the long leg.",
        "exercise_assignment_risk": "The short option can be assigned early, potentially creating temporary stock exposure before adjustment or exercise of the long leg.",
        "american_assignment_relevant": True,
        "common_use_case": "Blend longer-dated optionality with short-term theta harvesting while leaning modestly bullish or bearish.",
        "complexity_level": "advanced",
        "margin_notes": "Spread approval is typically required; short-leg assignment can temporarily create stock and margin exposure.",
        "notes": "Primary public HTML source clearly covered calls; put-variant coverage came from Fidelity's public strategy-evaluator quickguide.",
        "include_reason": "Named net-debit spread with purchased longer-dated premium as the core exposure.",
        "manual_review_reason": "Merged call and put variants have different directional tilts and can behave more like theta spreads than pure long-premium trades.",
    },
    "double diagonal spread": {
        "aliases": [],
        "strategy_family": "diagonal",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "neutral",
        "volatility_bias": "mixed",
        "time_decay_bias": "positive_theta",
        "legs_summary": "Buy a longer-dated straddle and sell a shorter-dated strangle, or equivalently pair call and put diagonals.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 4,
        "max_legs": 4,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Neutral outlook between the short strangle strikes with limited-risk exposure if the stock moves sharply.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Profit is limited and typically best if the stock finishes near one of the short strikes around front-month expiration.",
        "max_loss_summary": "Maximum loss is limited to the net debit and is typically realized near the long straddle strike if held poorly.",
        "breakeven_summary": "Breakeven depends on the short and long expiries, volatility, and where the stock sits relative to the short strangle.",
        "exercise_assignment_risk": "Short front-month options can be assigned early and may require active adjustment of the long-dated hedges.",
        "american_assignment_relevant": True,
        "common_use_case": "Advanced neutral strategy seeking positive theta with limited risk compared with a short strangle.",
        "complexity_level": "advanced",
        "margin_notes": "Complex spread approval is typically required; assignment on short legs can create stock exposure before the long legs are exercised or sold.",
        "notes": "Observed in Fidelity's public strategy guide rather than OIC's broader library page.",
        "include_reason": "Named net-debit long-premium structure from a reputable public strategy guide with clear limited-risk treatment.",
        "manual_review_reason": "Advanced theta-focused debit structure that some researchers may prefer to separate from simpler long-premium trades.",
    },
    "long butterfly": {
        "aliases": ["long call butterfly", "long put butterfly", "long butterfly spread with calls", "long butterfly spread with puts"],
        "strategy_family": "butterfly",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "neutral",
        "volatility_bias": "short_vol",
        "time_decay_bias": "positive_theta",
        "legs_summary": "Buy 1 lower-strike option, sell 2 middle-strike options, and buy 1 higher-strike option; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 4,
        "max_legs": 4,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Neutral outlook centered on the body strike near expiration.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited and occurs near the middle strike at expiration.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Two breakevens around the body strike, adjusted by the net debit paid.",
        "exercise_assignment_risk": "Short body options create assignment and pin risk, especially near expiration.",
        "american_assignment_relevant": True,
        "common_use_case": "Range-bound trade seeking a low-cost neutral payoff shape with limited risk.",
        "complexity_level": "intermediate",
        "margin_notes": "Net-debit complex spread; pin risk around the short body can create temporary assignment exposure near expiration.",
        "notes": "Included because the user explicitly asked to track long butterflies even though they are often short-volatility, positive-theta trades.",
        "include_reason": "Named net-debit spread with purchased options and limited risk, explicitly requested for inclusion.",
        "manual_review_reason": "Debit entry does not imply long-volatility; this family is typically neutral and short-volatility despite being included.",
    },
    "long condor": {
        "aliases": ["long call condor", "long put condor", "long condor spread with calls", "long condor spread with puts"],
        "strategy_family": "condor",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "neutral",
        "volatility_bias": "short_vol",
        "time_decay_bias": "positive_theta",
        "legs_summary": "Buy the outer wings and sell the inner body using four same-expiration options; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 4,
        "max_legs": 4,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Neutral outlook with a wider target range than a standard butterfly.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited and usually occurs when the stock finishes between the short strikes.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Two breakevens around the inner range, adjusted by the net debit paid.",
        "exercise_assignment_risk": "Short inner options create assignment and pin risk near expiration.",
        "american_assignment_relevant": True,
        "common_use_case": "Neutral range trade that sacrifices peak payoff for a broader profitable zone than a butterfly.",
        "complexity_level": "advanced",
        "margin_notes": "Net-debit complex spread; pin risk around the short strikes can create temporary assignment exposure near expiration.",
        "notes": "Included because the user explicitly asked to track long condors if documented as debit structures.",
        "include_reason": "Named net-debit spread with purchased options and limited risk, explicitly requested for inclusion.",
        "manual_review_reason": "Debit entry does not imply long-volatility; this family is typically neutral and short-volatility despite being included.",
    },
    "long iron butterfly": {
        "aliases": ["long iron butterfly spread"],
        "strategy_family": "butterfly",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "volatility_up",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Combine a bear put spread and a bull call spread with long center strikes and short outer wings.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 4,
        "max_legs": 4,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Expect a large move away from the center strike by expiration.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited to wing width minus the net debit when the stock finishes outside the wings.",
        "max_loss_summary": "Maximum loss is limited to the net debit if the stock finishes at the center strike.",
        "breakeven_summary": "Two breakevens around the center strike, adjusted by the net debit paid.",
        "exercise_assignment_risk": "Short wing options can be assigned early in American-style equity options.",
        "american_assignment_relevant": True,
        "common_use_case": "Limited-risk long-volatility structure for event-driven or breakout expectations.",
        "complexity_level": "advanced",
        "margin_notes": "Net-debit complex spread; short wing assignment can create temporary stock exposure until the long center options are exercised or the spread is closed.",
        "notes": "",
        "include_reason": "Named long-volatility debit structure with purchased center options and limited risk.",
    },
    "long iron condor": {
        "aliases": ["long iron condor spread", "long condor"],
        "strategy_family": "condor",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "volatility_up",
        "volatility_bias": "long_vol",
        "time_decay_bias": "negative_theta",
        "legs_summary": "Combine a bear put spread and a bull call spread with long wings outside the short strikes.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 4,
        "max_legs": 4,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Expect a large move outside the long wings and/or rising implied volatility.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited to spread width minus the net debit when the stock finishes outside the outer strikes.",
        "max_loss_summary": "Maximum loss is limited to the net debit if the stock remains between the long strikes and the structure expires worthless.",
        "breakeven_summary": "Two breakevens outside the inner range, adjusted by the net debit paid.",
        "exercise_assignment_risk": "Short outer options can be assigned early in American-style equity options.",
        "american_assignment_relevant": True,
        "common_use_case": "Limited-risk breakout or event-volatility trade using a reverse iron condor structure.",
        "complexity_level": "advanced",
        "margin_notes": "Net-debit complex spread; short-option assignment can create temporary stock exposure before the spread is fully closed.",
        "notes": "OIC labels the same payoff family as 'Long Condor'; Fidelity labels it 'Long Iron Condor Spread'.",
        "include_reason": "Named long-volatility debit structure with purchased wings and limited risk, explicitly requested when documented as a debit.",
    },
    "long ratio backspread": {
        "aliases": ["long ratio call spread", "long ratio put spread", "1x2 ratio volatility spread with calls", "1x2 ratio volatility spread with puts", "call backspread", "put backspread"],
        "strategy_family": "backspread",
        "classification": "net_debit_spread",
        "net_premium_type": "variable",
        "directional_bias": "mixed",
        "volatility_bias": "long_vol",
        "time_decay_bias": "mixed",
        "legs_summary": "Sell 1 option and buy 2 further-out options of the same type; call and put backspread variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 3,
        "max_legs": 3,
        "defined_risk": True,
        "defined_reward": False,
        "typical_outlook": "Expect a sharp directional move and/or higher implied volatility with more convexity than an outright long option.",
        "entry_debit_or_credit": "variable",
        "max_profit_summary": "Call variants have unlimited upside profit; put variants have substantial downside profit if the move is large enough.",
        "max_loss_summary": "Risk is limited but can exceed the initial cash outlay, with the worst loss typically near the short strike.",
        "breakeven_summary": "Usually involves two breakevens whose exact values depend on the strike spacing and whether entry was for a debit or credit.",
        "exercise_assignment_risk": "The single short option can be assigned early and may create temporary stock exposure before the long wings are exercised or sold.",
        "american_assignment_relevant": True,
        "common_use_case": "Convex long-volatility trade designed to reduce upfront cost relative to simply buying options outright.",
        "complexity_level": "advanced",
        "margin_notes": "Spread approval is typically required; short-option assignment and variable debit/credit entry can create temporary stock and margin exposure.",
        "notes": "Included because reputable public sources explicitly describe these as backspread variants even when they may be opened for a small debit or credit.",
        "include_reason": "Named long backspread variant with two purchased options versus one short option, explicitly requested if found.",
        "manual_review_reason": "These structures can be opened for either a debit or a credit, so the 'buying strategy' label is broader here than pure debit-only definitions.",
    },
    "long christmas tree spread": {
        "aliases": ["long christmas tree spread with calls", "long christmas tree spread with puts"],
        "strategy_family": "butterfly",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "neutral",
        "volatility_bias": "short_vol",
        "time_decay_bias": "positive_theta",
        "legs_summary": "Six-leg butterfly-style structure using four strikes with long wings and three short options near the center; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 6,
        "max_legs": 6,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Neutral outlook near the short strikes with an expectation that implied volatility stays stable or falls.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited and generally occurs near the strike of the short options.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Breakevens depend on the exact strike geometry and the opening debit, and are wider than a standard butterfly's range.",
        "exercise_assignment_risk": "Multiple short options create assignment and pin risk, especially as expiration approaches.",
        "american_assignment_relevant": True,
        "common_use_case": "Advanced neutral debit structure seeking time-decay gains with a wider tent than a standard butterfly.",
        "complexity_level": "advanced",
        "margin_notes": "Complex multi-leg spread approval is typically required; multiple short contracts can create assignment-driven stock exposure near expiration.",
        "notes": "Observed in Fidelity's public strategy guide; not present on OIC's broader all-strategies index.",
        "include_reason": "Named public debit spread with bought options and limited risk from a reputable priority source.",
        "manual_review_reason": "Debit entry notwithstanding, this family is fundamentally a neutral short-volatility/theta structure rather than a pure long-vol trade.",
    },
    "long christmas tree spread variation": {
        "aliases": ["long christmas tree spread variation with calls", "long christmas tree spread variation with puts"],
        "strategy_family": "butterfly",
        "classification": "net_debit_spread",
        "net_premium_type": "debit",
        "directional_bias": "neutral",
        "volatility_bias": "short_vol",
        "time_decay_bias": "positive_theta",
        "legs_summary": "Six-leg butterfly-style variation using four strikes with two long lower wings, three short near-center options, and one far wing; call and put variants were both observed.",
        "uses_calls": True,
        "uses_puts": True,
        "uses_stock": False,
        "min_legs": 6,
        "max_legs": 6,
        "defined_risk": True,
        "defined_reward": True,
        "typical_outlook": "Neutral outlook near the short strikes with an expectation that implied volatility stays stable or falls.",
        "entry_debit_or_credit": "net debit",
        "max_profit_summary": "Maximum profit is limited and generally occurs near the strike of the short options.",
        "max_loss_summary": "Maximum loss is limited to the net debit paid.",
        "breakeven_summary": "Breakevens depend on the exact strike geometry and the opening debit.",
        "exercise_assignment_risk": "Multiple short options create assignment and pin risk, especially as expiration approaches.",
        "american_assignment_relevant": True,
        "common_use_case": "Advanced neutral debit structure designed to widen or reshape the butterfly profit tent while keeping risk capped.",
        "complexity_level": "advanced",
        "margin_notes": "Complex multi-leg spread approval is typically required; multiple short contracts can create assignment-driven stock exposure near expiration.",
        "notes": "Observed in Fidelity's public strategy guide; not present on OIC's broader all-strategies index.",
        "include_reason": "Named public debit spread with bought options and limited risk from a reputable priority source.",
        "manual_review_reason": "Debit entry notwithstanding, this family is fundamentally a neutral short-volatility/theta structure rather than a pure long-vol trade.",
    },
}


AMBIGUOUS_EXCLUDED = {
    "long skip-strike butterfly": "Documented as a long butterfly-style structure, but the public source example was not clearly a debit-only buying strategy.",
    "cash-backed call": "Bought-call acquire-stock variant, but its primary use case is stock acquisition rather than premium-buying exposure.",
}


SCHWAB_OBSERVATIONS = [
    {"strategy_name": "Protective Put", "source_name": "Schwab", "source_title": "Can Protective Puts Provide a Temporary Shield?", "source_url": "https://www.schwab.com/learn/story/can-protective-puts-provide-temporary-shield", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article used as a corroborating source for protective puts."},
    {"strategy_name": "Collar", "source_name": "Schwab", "source_title": "Collaring Your Stock for Temporary Protection", "source_url": "https://www.schwab.com/learn/story/collaring-your-stock-temporary-protection", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article used as a corroborating source for collars."},
    {"strategy_name": "Long Straddle", "source_name": "Schwab", "source_title": "Straddles vs. Strangles Options Strategies", "source_url": "https://www.schwab.com/learn/story/straddles-vs-strangles-options-strategies", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article discussing long straddles versus long strangles."},
    {"strategy_name": "Long Strangle", "source_name": "Schwab", "source_title": "Straddles vs. Strangles Options Strategies", "source_url": "https://www.schwab.com/learn/story/straddles-vs-strangles-options-strategies", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article discussing long straddles versus long strangles."},
    {"strategy_name": "Bull Call Spread", "source_name": "Schwab", "source_title": "How Could Vertical Spreads Help Your Strategy?", "source_url": "https://www.schwab.com/learn/story/how-could-vertical-spreads-help-your-strategy", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article covering vertical spreads, including bull call spreads."},
    {"strategy_name": "Bear Put Spread", "source_name": "Schwab", "source_title": "How Could Vertical Spreads Help Your Strategy?", "source_url": "https://www.schwab.com/learn/story/how-could-vertical-spreads-help-your-strategy", "source_type": "learning_article", "collection_method": "manual_article_mapping", "source_notes": "Accessible Schwab education article covering vertical spreads, including bear put spreads."},
]


CBOE_OBSERVATIONS = [
    {"strategy_name": "Long Call", "source_name": "Cboe", "source_title": "Strategy-based Margin", "source_url": "https://www.cboe.com/us/options/strategy_based_margin", "source_type": "benchmark_page", "collection_method": "manual_article_mapping", "source_notes": "Accessible Cboe reference page used primarily for long-option margin treatment notes."},
    {"strategy_name": "Long Put", "source_name": "Cboe", "source_title": "Strategy-based Margin", "source_url": "https://www.cboe.com/us/options/strategy_based_margin", "source_type": "benchmark_page", "collection_method": "manual_article_mapping", "source_notes": "Accessible Cboe reference page used primarily for long-option margin treatment notes."},
]


FIDELITY_MANUAL_OBSERVATIONS = [
    {"strategy_name": "Bull Call Spread", "source_name": "Fidelity", "source_title": "Bull Call Spread", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/bull-call-spread", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Bear Put Spread", "source_name": "Fidelity", "source_title": "Bear Put Spread", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/bear-put-spread", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Straddle", "source_name": "Fidelity", "source_title": "Long Straddle", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-straddle", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Strangle", "source_name": "Fidelity", "source_title": "Long Strangle", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-strangle", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Married Put", "source_name": "Fidelity", "source_title": "Married Put", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/married-put", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Collar", "source_name": "Fidelity", "source_title": "Collar", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/collar", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Calendar Spread with Calls", "source_name": "Fidelity", "source_title": "Long Calendar Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-calendar-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Calendar Spread with Puts", "source_name": "Fidelity", "source_title": "Long Calendar Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-calendar-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Diagonal Spread with Calls", "source_name": "Fidelity", "source_title": "Long Diagonal Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-diagonal-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Diagonal Spread with Puts", "source_name": "Fidelity", "source_title": "How to Use the Strategy Evaluator", "source_url": "https://www.fidelity.com/webcontent/ap002390-mlo-content/20.04/pdf/strategyEvaluatorHowTo.pdf", "source_type": "quickguide", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-evaluator quickguide explicitly listed the put diagonal variant."},
    {"strategy_name": "Double Diagonal Spread", "source_name": "Fidelity", "source_title": "Double Diagonal Spread", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/double-diagonal-spread", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Butterfly Spread with Calls", "source_name": "Fidelity", "source_title": "Long Butterfly Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-butterfly-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Butterfly Spread with Puts", "source_name": "Fidelity", "source_title": "Long Butterfly Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-butterfly-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Condor Spread with Calls", "source_name": "Fidelity", "source_title": "Long Condor Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-condor-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Condor Spread with Puts", "source_name": "Fidelity", "source_title": "Long Condor Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-condor-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Iron Butterfly Spread", "source_name": "Fidelity", "source_title": "Long Iron Butterfly Spread", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-iron-butterfly-spread", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Iron Condor Spread", "source_name": "Fidelity", "source_title": "Long Iron Condor Spread", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-iron-condor-spread", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "1x2 Ratio Volatility Spread with Calls", "source_name": "Fidelity", "source_title": "1x2 Ratio Volatility Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/1x2-ratio-volatility-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "1x2 Ratio Volatility Spread with Puts", "source_name": "Fidelity", "source_title": "1x2 Ratio Volatility Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/1x2-ratio-volatility-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Christmas Tree Spread with Calls", "source_name": "Fidelity", "source_title": "Long Christmas Tree Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-christmas-tree-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Christmas Tree Spread with Puts", "source_name": "Fidelity", "source_title": "Long Christmas Tree Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-christmas-tree-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Christmas Tree Spread Variation with Calls", "source_name": "Fidelity", "source_title": "Long Christmas Tree Spread Variation with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-christmas-tree-spread-variation-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Christmas Tree Spread Variation with Puts", "source_name": "Fidelity", "source_title": "Long Christmas Tree Spread Variation with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-christmas-tree-spread-variation-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; direct requests were bot-protected."},
    {"strategy_name": "Long Skip-Strike Butterfly Spread with Calls", "source_name": "Fidelity", "source_title": "Long Skip-Strike Butterfly Spread with Calls", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-skip-strike-butterfly-spread-calls", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; kept for manual-review audit because the economic profile is not clearly debit-only."},
    {"strategy_name": "Long Skip-Strike Butterfly Spread with Puts", "source_name": "Fidelity", "source_title": "Long Skip-Strike Butterfly Spread with Puts", "source_url": "https://www.fidelity.com/learning-center/investment-products/options/options-strategy-guide/long-skip-strike-butterfly-spread-puts", "source_type": "strategy_page", "collection_method": "manual_public_reference", "source_notes": "Public Fidelity strategy-guide URL discovered from search indexing; kept for manual-review audit because the economic profile is not clearly debit-only."},
]


def collect_oic_observations() -> list[dict[str, Any]]:
    soup = BeautifulSoup(fetch_with_cache("https://www.optionseducation.org/strategies/all-strategies-en"), "lxml")
    page_urls: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        if href.startswith("/strategies/all-strategies/"):
            url = urljoin("https://www.optionseducation.org", href)
            if url not in page_urls:
                page_urls.append(url)

    observations: list[dict[str, Any]] = []
    for url in page_urls:
        strategy_soup = BeautifulSoup(fetch_with_cache(url), "lxml")
        main = strategy_soup.select_one("main") or strategy_soup
        h1 = main.select_one("h1") or strategy_soup.select_one("h1")
        strategy_name = clean_text(h1.get_text(" ", strip=True))
        source_title = clean_text(strategy_soup.title.get_text(" ", strip=True) if strategy_soup.title else strategy_name)
        sections = parse_section_blocks(main)
        highlights = parse_highlights(sections.get("Strategy Highlights", ""))
        observations.append(
            {
                "strategy_name": strategy_name,
                "source_name": "OIC",
                "source_title": source_title,
                "source_url": url,
                "source_type": "strategy_page",
                "collection_method": "live_html_fetch",
                "is_live_fetched": True,
                "description": sections.get("Description", ""),
                "summary": sections.get("Summary", ""),
                "outlook": sections.get("Outlook", ""),
                "motivation": sections.get("Motivation", "") or highlights.get("Motivation", ""),
                "max_gain": sections.get("Max Gain", "") or highlights.get("Maximum Gain", ""),
                "max_loss": sections.get("Max Loss", "") or highlights.get("Maximum Loss", ""),
                "breakeven": sections.get("Breakeven", ""),
                "exercise_assignment_risk_text": highlights.get("Exercise/Assignment Risk", "") or highlights.get("Assignment Risk", ""),
                "time_decay_text": highlights.get("Time Decay", ""),
                "volatility_text": highlights.get("Volatility Impact", ""),
                "source_notes": "Primary live-fetched OIC strategy page used as the core inventory and detail source.",
            }
        )
    return observations


def collect_manual_observations() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in SCHWAB_OBSERVATIONS + CBOE_OBSERVATIONS + FIDELITY_MANUAL_OBSERVATIONS:
        copied = dict(item)
        copied.update(
            {
                "is_live_fetched": False,
                "description": "",
                "summary": "",
                "outlook": "",
                "motivation": "",
                "max_gain": "",
                "max_loss": "",
                "breakeven": "",
                "exercise_assignment_risk_text": "",
                "time_decay_text": "",
                "volatility_text": "",
            }
        )
        rows.append(copied)
    return rows


def enrich_observation(observation: dict[str, Any]) -> dict[str, Any]:
    row = dict(observation)
    row["canonical_name"] = canonical_from_name(row["strategy_name"])
    row["aliases"] = "; ".join(extract_parenthetical_aliases(row["strategy_name"]))
    row["strategy_family"] = family_from_name(row["strategy_name"])
    row["is_options_buying_strategy"] = row["canonical_name"] in INCLUDED_CANONICALS
    row["classification"] = CANONICAL_PROFILES[row["canonical_name"]]["classification"] if row["is_options_buying_strategy"] else "exclude"
    row["dedupe_key"] = slugify(row["canonical_name"])
    row["uses_calls"], row["uses_puts"], row["uses_stock"] = infer_uses(row["strategy_name"], row.get("summary", ""))
    row["min_legs"], row["max_legs"] = infer_legs(row["strategy_family"], row["strategy_name"], row["uses_stock"])
    row["time_decay_bias"] = parse_time_decay_bias(row.get("time_decay_text", ""))
    row["volatility_bias_inferred"] = parse_volatility_bias(row.get("volatility_text", ""))
    row["defined_risk"] = infer_defined_risk(row.get("max_loss", ""))
    row["defined_reward"] = infer_defined_reward(row.get("max_gain", ""))
    return row


def build_master_rows(raw_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in raw_rows:
        if row["is_options_buying_strategy"]:
            grouped[row["canonical_name"]].append(row)

    master_rows: list[dict[str, Any]] = []
    merge_notes: list[tuple[str, str]] = []
    for canonical_name, rows in sorted(grouped.items()):
        profile = CANONICAL_PROFILES[canonical_name]
        rep = choose_representative(rows)
        raw_strategy_names = sorted({clean_text(r["strategy_name"]) for r in rows})
        raw_aliases: list[str] = []
        for row in rows:
            raw_aliases.extend(split_alias_text(row.get("aliases", "")))
            raw_aliases.append(strip_parenthetical(row["strategy_name"]))
        aliases = merge_aliases(profile.get("aliases", []), raw_aliases)
        if len(raw_strategy_names) > 1:
            merge_notes.append((canonical_name, "; ".join(raw_strategy_names)))

        notes = [profile.get("notes", "").strip()]
        if len(raw_strategy_names) > 1:
            notes.append(f"Merged source variants: {'; '.join(raw_strategy_names)}.")
        if len({r['source_name'] for r in rows}) > 1:
            notes.append("Cross-checked on: " + ", ".join(sorted({r["source_name"] for r in rows})) + ".")
        if profile.get("manual_review_reason"):
            notes.append("Manual review note: " + profile["manual_review_reason"])

        master_rows.append(
            {
                "strategy_name": rep["strategy_name"],
                "canonical_name": canonical_name,
                "aliases": aliases,
                "source_name": rep["source_name"],
                "source_title": rep["source_title"],
                "source_url": rep["source_url"],
                "source_type": rep["source_type"],
                "strategy_family": profile["strategy_family"],
                "classification": profile["classification"],
                "net_premium_type": profile["net_premium_type"],
                "directional_bias": profile["directional_bias"],
                "volatility_bias": profile["volatility_bias"],
                "time_decay_bias": profile["time_decay_bias"],
                "legs_summary": profile["legs_summary"],
                "uses_calls": bool_text(profile["uses_calls"]),
                "uses_puts": bool_text(profile["uses_puts"]),
                "uses_stock": bool_text(profile["uses_stock"]),
                "min_legs": profile["min_legs"],
                "max_legs": profile["max_legs"],
                "defined_risk": bool_text(profile["defined_risk"]),
                "defined_reward": bool_text(profile["defined_reward"]),
                "typical_outlook": profile["typical_outlook"],
                "entry_debit_or_credit": profile["entry_debit_or_credit"],
                "max_profit_summary": profile["max_profit_summary"],
                "max_loss_summary": profile["max_loss_summary"],
                "breakeven_summary": profile["breakeven_summary"],
                "exercise_assignment_risk": profile["exercise_assignment_risk"],
                "american_assignment_relevant": bool_text(profile["american_assignment_relevant"]),
                "common_use_case": profile["common_use_case"],
                "complexity_level": profile["complexity_level"],
                "margin_notes": profile["margin_notes"],
                "notes": " ".join(part for part in notes if part),
                "dedupe_key": slugify(canonical_name),
                "is_options_buying_strategy": "true",
                "include_reason": profile["include_reason"],
                "exclude_reason": "",
            }
        )
    return master_rows, merge_notes


def build_excluded_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    excluded_rows: list[dict[str, Any]] = []
    for row in raw_rows:
        if row["is_options_buying_strategy"]:
            continue

        lowered = row["strategy_name"].lower()
        if "credit" in lowered or "short" in lowered:
            net_premium_type = "credit"
        elif "covered" in lowered or "cash-backed" in lowered:
            net_premium_type = "variable"
        else:
            net_premium_type = "unknown"

        exclude_reason = AMBIGUOUS_EXCLUDED.get(row["canonical_name"])
        if not exclude_reason:
            if any(token in lowered for token in ["covered call", "cash-secured put", "naked call", "naked put"]):
                exclude_reason = "Primarily premium-selling or income-oriented rather than an options-buying strategy."
            elif "synthetic" in lowered:
                exclude_reason = "Primarily synthetic stock exposure rather than a distinct options-buying strategy."
            elif "short" in lowered or "credit" in lowered:
                exclude_reason = "Primarily premium-selling or net-credit structure."
            elif "covered" in lowered or "cash-backed" in lowered:
                exclude_reason = "Documented options strategy, but not treated here as a core buying strategy because stock-acquisition or income mechanics dominate."
            else:
                exclude_reason = "Not classified as an options buying strategy under the conservative inclusion rules used for this catalog."

        notes = [row.get("source_notes", "")]
        if row["canonical_name"] in AMBIGUOUS_EXCLUDED:
            notes.append("Flagged for manual review instead of being silently dropped.")

        excluded_rows.append(
            {
                "strategy_name": row["strategy_name"],
                "canonical_name": row["canonical_name"],
                "aliases": row.get("aliases", ""),
                "source_name": row["source_name"],
                "source_title": row["source_title"],
                "source_url": row["source_url"],
                "source_type": row["source_type"],
                "strategy_family": row["strategy_family"],
                "classification": "exclude",
                "net_premium_type": net_premium_type,
                "directional_bias": normalize_direction_for_excluded(row["strategy_name"], row.get("outlook", "")),
                "volatility_bias": row.get("volatility_bias_inferred", "unknown"),
                "time_decay_bias": row.get("time_decay_bias", "unknown"),
                "legs_summary": row.get("summary") or row.get("description") or "",
                "uses_calls": bool_text(row["uses_calls"]),
                "uses_puts": bool_text(row["uses_puts"]),
                "uses_stock": bool_text(row["uses_stock"]),
                "min_legs": row["min_legs"],
                "max_legs": row["max_legs"],
                "defined_risk": bool_text(bool(row["defined_risk"])),
                "defined_reward": bool_text(bool(row["defined_reward"])),
                "typical_outlook": row.get("outlook", ""),
                "entry_debit_or_credit": net_premium_type,
                "max_profit_summary": row.get("max_gain", ""),
                "max_loss_summary": row.get("max_loss", ""),
                "breakeven_summary": row.get("breakeven", ""),
                "exercise_assignment_risk": row.get("exercise_assignment_risk_text", ""),
                "american_assignment_relevant": bool_text(any(token in lowered for token in ["short", "covered", "ratio", "calendar", "condor", "butterfly"])),
                "common_use_case": row.get("motivation", ""),
                "complexity_level": "advanced" if row["strategy_family"] in {"calendar", "diagonal", "butterfly", "condor", "backspread"} else "intermediate",
                "margin_notes": default_margin_notes(row["strategy_family"], False, row["uses_stock"]),
                "notes": " ".join(part for part in notes if part),
                "dedupe_key": row["dedupe_key"],
                "is_options_buying_strategy": "false",
                "include_reason": "",
                "exclude_reason": exclude_reason,
            }
        )
    return excluded_rows


def build_sources_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "strategy_name": row["strategy_name"],
            "canonical_name": row["canonical_name"],
            "source_name": row["source_name"],
            "source_title": row["source_title"],
            "source_url": row["source_url"],
            "source_type": row["source_type"],
            "collection_method": row["collection_method"],
            "is_live_fetched": bool_text(bool(row["is_live_fetched"])),
            "strategy_family": row["strategy_family"],
            "classification": row["classification"],
            "is_options_buying_strategy": bool_text(bool(row["is_options_buying_strategy"])),
            "dedupe_key": row["dedupe_key"],
            "source_notes": row.get("source_notes", ""),
        }
        for row in raw_rows
    ]


def render_summary(raw_rows: list[dict[str, Any]], master_rows: list[dict[str, Any]], excluded_rows: list[dict[str, Any]], merge_notes: list[tuple[str, str]]) -> str:
    source_counts = Counter(row["source_name"] for row in raw_rows)
    family_counts = Counter(row["strategy_family"] for row in master_rows)
    classification_counts = Counter([row["classification"] for row in master_rows] + [row["classification"] for row in excluded_rows])

    lines = [
        "# Options Buying Strategies Summary",
        "",
        "## Totals",
        f"- Total raw strategies found: {len(raw_rows)}",
        f"- Total included: {len(master_rows)}",
        f"- Total excluded: {len(excluded_rows)}",
        "",
        "## Counts by Source",
    ]
    for source_name, count in sorted(source_counts.items()):
        lines.append(f"- {source_name}: {count}")
    lines.extend(["", "## Counts by Strategy Family"])
    for family, count in sorted(family_counts.items()):
        lines.append(f"- {family}: {count}")
    lines.extend(["", "## Counts by Classification"])
    for classification, count in sorted(classification_counts.items()):
        lines.append(f"- {classification}: {count}")
    lines.extend(["", "## Duplicate / Alias Merges"])
    if merge_notes:
        for canonical_name, raw_names in merge_notes:
            lines.append(f"- `{canonical_name}` <= {raw_names}")
    else:
        lines.append("- None")
    lines.extend(["", "## Ambiguous Strategies Needing Manual Review"])
    for canonical_name, profile in CANONICAL_PROFILES.items():
        if profile.get("manual_review_reason"):
            lines.append(f"- `{canonical_name}`: {profile['manual_review_reason']}")
    for canonical_name, reason in AMBIGUOUS_EXCLUDED.items():
        lines.append(f"- `{canonical_name}`: {reason}")
    lines.extend(
        [
            "",
            "## Notes",
            "- OIC live strategy pages were used as the primary full inventory and detail source.",
            "- Schwab pages were added as accessible corroborating education articles.",
            "- Cboe's public strategy-based margin page was used for margin-context cross-checking.",
            "- Fidelity public strategy-guide URLs were recorded from search-indexed public pages because direct HTML requests were bot-protected in this environment.",
            "- The catalog is best-effort and intentionally conservative; it should not be read as literally every options strategy online.",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=columns)
    else:
        for column in columns:
            if column not in df.columns:
                df[column] = ""
        df = df[columns]
    df.to_csv(path, index=False)


def print_console_summary(master_rows: list[dict[str, Any]], excluded_rows: list[dict[str, Any]]) -> None:
    print("Files written:")
    print(f"- {MASTER_CSV}")
    print(f"- {EXCLUDED_CSV}")
    print(f"- {SOURCES_CSV}")
    print(f"- {SUMMARY_MD}")
    print("")
    print("Top 25 included strategies:")
    for row in master_rows[:25]:
        print(f"- {row['canonical_name']} | {row['classification']} | {row['strategy_family']} | {row['source_name']}")
    print("")
    print("Top 25 excluded but related strategies:")
    for row in excluded_rows[:25]:
        print(f"- {row['strategy_name']} | {row['strategy_family']} | {row['exclude_reason']}")
    print("")
    print("Ambiguous classifications needing review:")
    seen = set()
    for row in master_rows:
        if "Manual review note:" in row["notes"]:
            seen.add(row["canonical_name"])
            print(f"- {row['canonical_name']} | {row['notes'].split('Manual review note: ', 1)[1]}")
    for row in excluded_rows:
        if "Flagged for manual review" in row["notes"] and row["canonical_name"] not in seen:
            seen.add(row["canonical_name"])
            print(f"- {row['canonical_name']} | {row['exclude_reason']}")


def main() -> None:
    ensure_dirs()
    raw_rows = [enrich_observation(row) for row in collect_oic_observations() + collect_manual_observations()]
    master_rows, merge_notes = build_master_rows(raw_rows)
    excluded_rows = build_excluded_rows(raw_rows)
    sources_rows = build_sources_rows(raw_rows)

    master_rows.sort(key=lambda row: (row["canonical_name"], row["strategy_name"]))
    excluded_rows.sort(key=lambda row: (row["canonical_name"], row["strategy_name"], row["source_name"]))
    sources_rows.sort(key=lambda row: (row["source_name"], row["canonical_name"], row["strategy_name"]))

    write_csv(MASTER_CSV, master_rows, MASTER_COLUMNS)
    write_csv(EXCLUDED_CSV, excluded_rows, MASTER_COLUMNS)
    write_csv(SOURCES_CSV, sources_rows, SOURCE_COLUMNS)
    SUMMARY_MD.write_text(render_summary(raw_rows, master_rows, excluded_rows, merge_notes), encoding="utf-8")
    print_console_summary(master_rows, excluded_rows)


if __name__ == "__main__":
    main()
