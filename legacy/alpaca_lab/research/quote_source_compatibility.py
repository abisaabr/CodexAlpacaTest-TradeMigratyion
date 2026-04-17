from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import pandas as pd

from alpaca_lab.brokers.alpaca import AlpacaBrokerAdapter
from alpaca_lab.config import load_settings
from alpaca_lab.data.chunking import market_session_bounds

_OPTION_SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,6}\d{6}[CP]\d{8}$")
_SURFACE_ROWS: tuple[dict[str, Any], ...] = (
    {
        "surface_name": "option_contract_lookup",
        "endpoint_pattern": "/v2/options/contracts/{symbol_or_id}",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": False,
        "supports_quotes": False,
        "supports_latest_only": False,
        "supports_contract_symbol_lookup": True,
        "doc_url": "https://docs.alpaca.markets/reference/get-options-contracts",
        "notes": "Canonical trading/options contract metadata lookup by symbol or contract id.",
    },
    {
        "surface_name": "option_contract_list",
        "endpoint_pattern": "/v2/options/contracts",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": False,
        "supports_quotes": False,
        "supports_latest_only": False,
        "supports_contract_symbol_lookup": True,
        "doc_url": "https://docs.alpaca.markets/reference/get-options-contracts",
        "notes": "Canonical contract discovery surface for expiration, strike, and type filtering.",
    },
    {
        "surface_name": "historical_option_bars",
        "endpoint_pattern": "/v1beta1/options/bars",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": True,
        "supports_quotes": False,
        "supports_latest_only": False,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/reference/optionbars",
        "notes": "Official historical options inventory clearly documents bars.",
    },
    {
        "surface_name": "historical_option_trades",
        "endpoint_pattern": "/v1beta1/options/trades",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": True,
        "supports_quotes": False,
        "supports_latest_only": False,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/docs/options-trading-overview",
        "notes": "Official options inventory lists historical trades.",
    },
    {
        "surface_name": "latest_option_quotes",
        "endpoint_pattern": "/v1beta1/options/quotes/latest",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": False,
        "supports_quotes": True,
        "supports_latest_only": True,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/reference/optionlatestquotes",
        "notes": "Official latest-quote surface for options.",
    },
    {
        "surface_name": "option_snapshots",
        "endpoint_pattern": "/v1beta1/options/snapshots",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": False,
        "supports_quotes": True,
        "supports_latest_only": True,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/v1.1/reference/optionchain",
        "notes": "Snapshot surface exposes latest trade, latest quote, and greeks.",
    },
    {
        "surface_name": "option_chain_snapshots",
        "endpoint_pattern": "/v1beta1/options/snapshots/{underlying_symbol}",
        "official_status": "documented",
        "documented_or_inferred": "documented",
        "supports_historical": False,
        "supports_quotes": True,
        "supports_latest_only": True,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/v1.1/reference/optionchain",
        "notes": "Underlying chain snapshot surface is documented as a latest snapshot view.",
    },
    {
        "surface_name": "historical_option_quotes_attempted",
        "endpoint_pattern": "/v1beta1/options/quotes",
        "official_status": "not_clearly_documented",
        "documented_or_inferred": "inferred_from_connector_attempt",
        "supports_historical": False,
        "supports_quotes": True,
        "supports_latest_only": False,
        "supports_contract_symbol_lookup": False,
        "doc_url": "https://docs.alpaca.markets/docs/historical-option-data",
        "notes": "Repo attempts this endpoint, but current official options inventory highlights historical bars/trades plus latest quotes/snapshots, not a clearly documented historical quote operation.",
    },
)


def build_alpaca_option_quote_surface_matrix() -> pd.DataFrame:
    return pd.DataFrame(_SURFACE_ROWS)


def build_alpaca_option_quote_surface_summary_markdown(surface_matrix: pd.DataFrame) -> str:
    if surface_matrix.empty:
        return "# Alpaca Option Quote Surface Summary\n\nNo surface metadata was generated.\n"
    rows = surface_matrix.drop_duplicates(subset=["surface_name", "endpoint_pattern"]).copy()
    documented = int(rows["documented_or_inferred"].astype("string").eq("documented").sum())
    historical_quote_rows = rows[
        rows["surface_name"].astype("string").eq("historical_option_quotes_attempted")
    ].copy()
    lines = [
        "# Alpaca Option Quote Surface Summary",
        "",
        f"- Documented surfaces tracked: `{documented}`",
        f"- Historical quote surface row present: `{not historical_quote_rows.empty}`",
    ]
    if not historical_quote_rows.empty:
        history_row = historical_quote_rows.iloc[0]
        lines.append(
            "- Historical quote audit status: "
            f"`{history_row['official_status']}` via `{history_row['endpoint_pattern']}`"
        )
        lines.append(f"- Notes: {history_row['notes']}")
    lines.extend(
        [
            "",
            "## Documented Historical Surfaces",
            "",
            "- Historical option bars: documented.",
            "- Historical option trades: documented.",
            "",
            "## Latest-Only Quote Surfaces",
            "",
            "- Latest option quotes: documented.",
            "- Option snapshots / chain snapshots: documented latest views.",
            "",
            "## Connector Assumption Under Test",
            "",
            "- Historical option quotes are attempted through `/v1beta1/options/quotes`, but this surface is not clearly documented in the current options inventory table the repo relies on.",
            "",
        ]
    )
    return "\n".join(lines)


def build_option_quote_request_examples(audit_frame: pd.DataFrame, *, max_examples: int = 24) -> dict[str, Any]:
    if audit_frame.empty:
        return {"examples": []}
    example_columns = [
        "underlying",
        "timeframe",
        "option_contract_symbol",
        "trade_date",
        "request_surface",
        "request_shape_variant",
        "request_endpoint",
        "request_params_hash",
        "status_code",
        "response_class",
        "response_reason",
        "quote_request_success",
        "prepared_url",
    ]
    subset = audit_frame.loc[:, [column for column in example_columns if column in audit_frame.columns]].copy()
    subset = subset.head(max(int(max_examples), 1)).reset_index(drop=True)
    return {"examples": subset.to_dict(orient="records")}


def select_quote_contract_samples(
    lineage_events: pd.DataFrame,
    *,
    max_per_underlying: int = 4,
) -> pd.DataFrame:
    if lineage_events.empty:
        return pd.DataFrame()
    sample = lineage_events[
        [
            "underlying",
            "timeframe",
            "signal_family",
            "structure_name",
            "expression_type",
            "trade_date",
            "timestamp_utc",
            "event_stage",
            "option_contract_symbol",
            "option_type",
            "dte",
            "dte_bucket",
            "strike_price",
        ]
    ].copy()
    sample["timestamp_utc"] = pd.to_datetime(sample["timestamp_utc"], utc=True, errors="coerce")
    sample["event_stage_rank"] = sample["event_stage"].astype("string").map({"entry": 0, "exit": 1}).fillna(9)
    sample["symbol_shape_valid"] = sample["option_contract_symbol"].astype("string").map(_symbol_shape_valid)
    sample = sample.sort_values(
        ["underlying", "event_stage_rank", "trade_date", "timestamp_utc", "option_contract_symbol"],
        ascending=[True, True, False, False, True],
    )
    sample = sample.drop_duplicates(subset=["underlying", "option_contract_symbol"], keep="first").reset_index(drop=True)
    selected_indices: list[int] = []
    for _, group in sample.groupby("underlying", dropna=False, sort=False):
        chosen: list[int] = []
        seen_types: set[str] = set()
        seen_buckets: set[str] = set()
        for index, row in group.iterrows():
            option_type = str(row.get("option_type", "") or "").lower()
            dte_bucket = str(row.get("dte_bucket", "") or "")
            novelty = int(option_type not in seen_types) + int(dte_bucket not in seen_buckets)
            if len(chosen) < 2 or novelty > 0:
                chosen.append(int(index))
                if option_type:
                    seen_types.add(option_type)
                if dte_bucket:
                    seen_buckets.add(dte_bucket)
            if len(chosen) >= max(int(max_per_underlying), 1):
                break
        if len(chosen) < max(int(max_per_underlying), 1):
            for index, _row in group.iterrows():
                if int(index) in chosen:
                    continue
                chosen.append(int(index))
                if len(chosen) >= max(int(max_per_underlying), 1):
                    break
        selected_indices.extend(chosen)
    selected = sample.loc[selected_indices].copy().reset_index(drop=True)
    selected["sample_selection_reason"] = selected.apply(
        lambda row: (
            f"replay_selected_contract;event_stage={row.get('event_stage', '')};"
            f"option_type={row.get('option_type', '')};dte_bucket={row.get('dte_bucket', '')}"
        ),
        axis=1,
    )
    return selected


def build_quote_contract_symbol_truth_table(
    sample_frame: pd.DataFrame,
    *,
    contract_master: pd.DataFrame,
    adapter: AlpacaBrokerAdapter | None,
    adapter_status: str,
) -> pd.DataFrame:
    if sample_frame.empty:
        return pd.DataFrame()
    local_master = contract_master.copy()
    if not local_master.empty:
        local_master["symbol"] = local_master["symbol"].astype("string")
    rows: list[dict[str, Any]] = []
    for sample in sample_frame.to_dict(orient="records"):
        symbol = str(sample.get("option_contract_symbol", "") or "")
        local_matches = (
            local_master[local_master["symbol"].astype("string").eq(symbol)].copy()
            if not local_master.empty and "symbol" in local_master.columns
            else pd.DataFrame()
        )
        local_match = local_matches.iloc[0].to_dict() if not local_matches.empty else {}
        lookup_success = False
        lookup_id = ""
        lookup_status_code: int | None = None
        lookup_reason = str(adapter_status)
        payload: dict[str, Any] = {}
        if adapter is not None:
            try:
                payload = adapter.get_option_contract(symbol)
                lookup_success = bool(payload)
                lookup_id = str(payload.get("id", "") or "")
                request_audit = payload.get("request_audit", [])
                if isinstance(request_audit, list) and request_audit:
                    lookup_status_code = int(request_audit[0].get("status_code", 0) or 0) or None
                lookup_reason = "lookup_by_symbol_succeeded" if lookup_success else "lookup_returned_empty_payload"
            except Exception as exc:  # noqa: BLE001
                lookup_status_code = _status_code_from_exception(exc)
                lookup_reason = _truncate_text(str(exc), max_length=200)
        expiration_date = (
            _safe_date_text(payload.get("expiration_date"))
            or _safe_date_text(local_match.get("expiration_date"))
            or str(sample.get("trade_date", "") or "")
        )
        strike_price = _safe_float(
            payload.get("strike_price", local_match.get("strike_price", sample.get("strike_price"))),
            float("nan"),
        )
        option_type = (
            str(payload.get("type", "") or "")
            or str(local_match.get("option_type", "") or "")
            or str(sample.get("option_type", "") or "")
        ).lower()
        symbol_shape_valid = _symbol_shape_valid(symbol)
        local_contract_master_match = bool(not local_matches.empty)
        if lookup_success:
            truth_reason = "valid_symbol_remote_contract_lookup"
        elif local_contract_master_match and symbol_shape_valid:
            truth_reason = "valid_symbol_local_contract_master_only"
        elif symbol_shape_valid:
            truth_reason = "symbol_shape_valid_remote_lookup_failed"
        else:
            truth_reason = "invalid_symbol_shape"
        rows.append(
            {
                "underlying_symbol": str(sample.get("underlying", "") or ""),
                "timeframe": str(sample.get("timeframe", "") or ""),
                "option_contract_symbol": symbol,
                "trade_date": str(sample.get("trade_date", "") or ""),
                "event_stage": str(sample.get("event_stage", "") or ""),
                "contract_lookup_success": bool(lookup_success),
                "contract_lookup_id": lookup_id,
                "expiration_date": expiration_date,
                "strike_price": strike_price,
                "option_type": option_type,
                "symbol_shape_valid": bool(symbol_shape_valid),
                "local_contract_master_match": bool(local_contract_master_match),
                "contract_lookup_status_code": lookup_status_code,
                "contract_lookup_reason": lookup_reason,
                "symbol_truth_reason": truth_reason,
            }
        )
    return pd.DataFrame(rows)


def build_option_quote_request_audit(
    sample_frame: pd.DataFrame,
    *,
    adapter: AlpacaBrokerAdapter | None,
    adapter_status: str,
) -> pd.DataFrame:
    if sample_frame.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for sample in sample_frame.to_dict(orient="records"):
        symbol = str(sample.get("option_contract_symbol", "") or "")
        trade_date = str(sample.get("trade_date", "") or "")
        if not symbol or not trade_date:
            continue
        session_start, session_end = market_session_bounds(pd.Timestamp(trade_date).date())
        request_specs = [
            {
                "request_surface": "historical_option_quotes",
                "request_shape_variant": "historical_quotes_default",
                "request_endpoint": "/v1beta1/options/quotes",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "limit": 5,
                },
            },
            {
                "request_surface": "historical_option_quotes",
                "request_shape_variant": "historical_quotes_indicative",
                "request_endpoint": "/v1beta1/options/quotes",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "limit": 5,
                    "feed": "indicative",
                },
            },
            {
                "request_surface": "historical_option_quotes",
                "request_shape_variant": "historical_quotes_opra",
                "request_endpoint": "/v1beta1/options/quotes",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "limit": 5,
                    "feed": "opra",
                },
            },
            {
                "request_surface": "historical_option_bars_reference",
                "request_shape_variant": "historical_bars_reference",
                "request_endpoint": "/v1beta1/options/bars",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "timeframe": "1Min",
                    "limit": 5,
                },
            },
            {
                "request_surface": "historical_option_trades_reference",
                "request_shape_variant": "historical_trades_reference",
                "request_endpoint": "/v1beta1/options/trades",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                    "start": session_start.isoformat(),
                    "end": session_end.isoformat(),
                    "limit": 5,
                },
            },
            {
                "request_surface": "latest_option_quotes_reference",
                "request_shape_variant": "latest_quotes_reference",
                "request_endpoint": "/v1beta1/options/quotes/latest",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                },
            },
            {
                "request_surface": "option_snapshots_reference",
                "request_shape_variant": "snapshots_reference",
                "request_endpoint": "/v1beta1/options/snapshots",
                "request_api": "data",
                "request_params": {
                    "symbols": symbol,
                },
            },
        ]
        for spec in request_specs:
            rows.append(
                {
                    "underlying": str(sample.get("underlying", "") or ""),
                    "timeframe": str(sample.get("timeframe", "") or ""),
                    "signal_family": str(sample.get("signal_family", "") or ""),
                    "structure_name": str(sample.get("structure_name", "") or ""),
                    "expression_type": str(sample.get("expression_type", "") or ""),
                    "trade_date": trade_date,
                    "event_stage": str(sample.get("event_stage", "") or ""),
                    "timestamp_utc": str(sample.get("timestamp_utc", "") or ""),
                    "option_contract_symbol": symbol,
                    **_execute_request_variant(
                        adapter,
                        adapter_status=adapter_status,
                        request_endpoint=str(spec["request_endpoint"]),
                        request_api=str(spec["request_api"]),
                        request_surface=str(spec["request_surface"]),
                        request_shape_variant=str(spec["request_shape_variant"]),
                        request_params=dict(spec["request_params"]),
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_option_quote_compatibility_verdicts(
    sample_frame: pd.DataFrame,
    *,
    truth_table: pd.DataFrame,
    request_audit: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if sample_frame.empty:
        empty = pd.DataFrame()
        return empty, empty
    truth_lookup = (
        truth_table.set_index(["underlying_symbol", "option_contract_symbol"]).to_dict(orient="index")
        if not truth_table.empty
        else {}
    )
    verdict_rows: list[dict[str, Any]] = []
    for sample in sample_frame.to_dict(orient="records"):
        underlying = str(sample.get("underlying", "") or "")
        symbol = str(sample.get("option_contract_symbol", "") or "")
        truth = truth_lookup.get((underlying, symbol), {})
        audit_slice = (
            request_audit[
                request_audit["option_contract_symbol"].astype("string").eq(symbol)
                & request_audit["underlying"].astype("string").eq(underlying)
                & request_audit["trade_date"].astype("string").eq(str(sample.get("trade_date", "") or ""))
            ].copy()
            if not request_audit.empty
            else pd.DataFrame()
        )
        historical_quotes = audit_slice[
            audit_slice["request_surface"].astype("string").eq("historical_option_quotes")
        ].copy()
        historical_bars = audit_slice[
            audit_slice["request_surface"].astype("string").eq("historical_option_bars_reference")
        ].copy()
        historical_trades = audit_slice[
            audit_slice["request_surface"].astype("string").eq("historical_option_trades_reference")
        ].copy()
        latest_quotes = audit_slice[
            audit_slice["request_surface"].astype("string").eq("latest_option_quotes_reference")
        ].copy()
        snapshots = audit_slice[
            audit_slice["request_surface"].astype("string").eq("option_snapshots_reference")
        ].copy()
        hist_classes = set(historical_quotes.get("response_class", pd.Series(dtype="string")).astype(str).tolist())
        reference_supported = any(
            not frame.empty
            and frame["response_class"].astype("string").isin(["success", "empty_but_supported"]).any()
            for frame in (historical_bars, historical_trades, latest_quotes, snapshots)
        )
        hist_success = "success" in hist_classes
        hist_empty = "empty_but_supported" in hist_classes
        hist_not_found = "not_found" in hist_classes
        hist_auth = "auth_or_subscription_error" in hist_classes
        hist_validation = "validation_error" in hist_classes
        symbol_valid = bool(truth.get("symbol_shape_valid", False)) and (
            bool(truth.get("local_contract_master_match", False))
            or bool(truth.get("contract_lookup_success", False))
        )
        if not bool(truth.get("symbol_shape_valid", False)):
            verdict = "invalid_symbol_shape"
            reason = str(truth.get("symbol_truth_reason", "invalid_symbol_shape"))
        elif hist_auth:
            verdict = "valid_symbol_but_feed_or_auth_blocked"
            reason = "historical_quote_requests_returned_auth_or_subscription_error"
        elif hist_validation:
            verdict = "valid_symbol_but_request_shape_wrong"
            reason = "historical_quote_requests_returned_validation_error"
        elif hist_success:
            verdict = "valid_symbol_and_historical_quote_supported"
            reason = "historical_quote_request_returned_quote_rows"
        elif hist_empty:
            verdict = "valid_symbol_but_empty_response"
            reason = "historical_quote_requests_returned_empty_payload"
        elif hist_not_found and reference_supported and symbol_valid:
            verdict = "valid_symbol_but_historical_quote_surface_missing"
            reason = "historical_quote_requests_404_while_other_documented_surfaces_succeed"
        elif hist_not_found and symbol_valid:
            verdict = "valid_symbol_but_date_or_time_unsupported"
            reason = "historical_quote_requests_404_with_valid_symbol_but_no_reference_confirmation"
        elif symbol_valid:
            verdict = "inconclusive"
            reason = "valid_symbol_without_decisive_quote_surface_response"
        else:
            verdict = "invalid_symbol_shape"
            reason = str(truth.get("symbol_truth_reason", "invalid_symbol_shape"))
        verdict_rows.append(
            {
                "underlying": underlying,
                "timeframe": str(sample.get("timeframe", "") or ""),
                "signal_family": str(sample.get("signal_family", "") or ""),
                "structure_name": str(sample.get("structure_name", "") or ""),
                "expression_type": str(sample.get("expression_type", "") or ""),
                "trade_date": str(sample.get("trade_date", "") or ""),
                "option_contract_symbol": symbol,
                "contract_lookup_success": bool(truth.get("contract_lookup_success", False)),
                "symbol_shape_valid": bool(truth.get("symbol_shape_valid", False)),
                "local_contract_master_match": bool(truth.get("local_contract_master_match", False)),
                "historical_quote_success_count": int(
                    historical_quotes["response_class"].astype("string").eq("success").sum()
                ) if not historical_quotes.empty else 0,
                "historical_quote_empty_count": int(
                    historical_quotes["response_class"].astype("string").eq("empty_but_supported").sum()
                ) if not historical_quotes.empty else 0,
                "historical_quote_not_found_count": int(
                    historical_quotes["response_class"].astype("string").eq("not_found").sum()
                ) if not historical_quotes.empty else 0,
                "historical_quote_auth_error_count": int(
                    historical_quotes["response_class"].astype("string").eq("auth_or_subscription_error").sum()
                ) if not historical_quotes.empty else 0,
                "historical_quote_validation_error_count": int(
                    historical_quotes["response_class"].astype("string").eq("validation_error").sum()
                ) if not historical_quotes.empty else 0,
                "bars_reference_supported": bool(reference_supported),
                "latest_quote_reference_supported": bool(
                    not latest_quotes.empty
                    and latest_quotes["response_class"].astype("string").isin(["success", "empty_but_supported"]).any()
                ),
                "compatibility_verdict": verdict,
                "compatibility_reason": reason,
            }
        )
    verdicts = pd.DataFrame(verdict_rows)
    by_symbol = rollup_option_quote_compatibility_by_symbol(verdicts)
    return verdicts, by_symbol


def rollup_option_quote_compatibility_by_symbol(verdicts: pd.DataFrame) -> pd.DataFrame:
    if verdicts.empty:
        return pd.DataFrame()
    grouped = (
        verdicts.groupby("underlying", dropna=False)
        .agg(
            audited_contract_count=("option_contract_symbol", "nunique"),
            sample_event_count=("option_contract_symbol", "size"),
            contract_lookup_success_count=("contract_lookup_success", "sum"),
            historical_quote_success_count=("historical_quote_success_count", "sum"),
            historical_quote_empty_count=("historical_quote_empty_count", "sum"),
            historical_quote_not_found_count=("historical_quote_not_found_count", "sum"),
            historical_quote_auth_error_count=("historical_quote_auth_error_count", "sum"),
            dominant_compatibility_verdict=("compatibility_verdict", _dominant_text),
        )
        .reset_index()
    )
    grouped["historical_quote_support_rate"] = grouped.apply(
        lambda row: float(
            round(
                _safe_ratio(int(row["historical_quote_success_count"]), max(int(row["sample_event_count"]), 1)),
                6,
            )
        ),
        axis=1,
    )
    return grouped


def build_quote_source_next_actions(
    by_symbol: pd.DataFrame,
    *,
    verdicts: pd.DataFrame,
) -> pd.DataFrame:
    if by_symbol.empty:
        return pd.DataFrame(
            [
                {
                    "underlying": "ALL",
                    "recommendation_category": "inconclusive",
                    "dominant_compatibility_verdict": "inconclusive",
                    "primary_next_step": "keep_options_replay_research_only_until_new_quote_source_exists",
                    "recommended_action": "No compatibility verdicts were produced.",
                    "exact_next_batch_recommended": "connector_quote_surface_recheck",
                }
            ]
        )
    primary_next_step = _primary_next_step(verdicts)
    rows: list[dict[str, Any]] = []
    for row in by_symbol.to_dict(orient="records"):
        verdict = str(row.get("dominant_compatibility_verdict", "") or "")
        rows.append(
            {
                "underlying": str(row.get("underlying", "") or ""),
                "recommendation_category": _recommendation_category(verdict),
                "dominant_compatibility_verdict": verdict,
                "primary_next_step": primary_next_step,
                "recommended_action": _recommended_action(primary_next_step, verdict),
                "exact_next_batch_recommended": primary_next_step,
            }
        )
    rows.append(
        {
            "underlying": "ALL",
            "recommendation_category": _recommendation_category(
                _dominant_text(verdicts.get("compatibility_verdict", pd.Series(dtype="string")))
            ),
            "dominant_compatibility_verdict": _dominant_text(
                verdicts.get("compatibility_verdict", pd.Series(dtype="string"))
            ),
            "primary_next_step": primary_next_step,
            "recommended_action": _recommended_action(
                primary_next_step,
                _dominant_text(verdicts.get("compatibility_verdict", pd.Series(dtype="string"))),
            ),
            "exact_next_batch_recommended": primary_next_step,
        }
    )
    return pd.DataFrame(rows)


def build_quote_source_compatibility_recommendations_markdown(
    next_actions: pd.DataFrame,
    *,
    by_symbol: pd.DataFrame,
    verdicts: pd.DataFrame,
) -> str:
    if next_actions.empty:
        return "# Quote Source Compatibility Recommendations\n\nNo quote-source compatibility recommendation was generated.\n"
    overall = next_actions[next_actions["underlying"].astype("string").eq("ALL")]
    overall_row = overall.iloc[0].to_dict() if not overall.empty else next_actions.iloc[0].to_dict()
    lines = [
        "# Quote Source Compatibility Recommendations",
        "",
        f"- Primary next step: `{overall_row.get('primary_next_step', '')}`",
        f"- Dominant verdict: `{overall_row.get('dominant_compatibility_verdict', '')}`",
        f"- Action: {overall_row.get('recommended_action', '')}",
        "",
        "## By Symbol",
        "",
    ]
    for row in by_symbol.to_dict(orient="records"):
        lines.extend(
            [
                f"### {row.get('underlying', '')}",
                "",
                f"- Dominant verdict: `{row.get('dominant_compatibility_verdict', '')}`",
                f"- Audited contracts: `{row.get('audited_contract_count', 0)}`",
                f"- Historical quote successes: `{row.get('historical_quote_success_count', 0)}`",
                f"- Historical quote 404s: `{row.get('historical_quote_not_found_count', 0)}`",
                "",
            ]
        )
    return "\n".join(lines)
