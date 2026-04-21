from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize a chained tournament conveyor into a single JSON/Markdown report."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the summary artifacts should be written.",
    )
    parser.add_argument(
        "--wave",
        action="append",
        default=[],
        help="Wave specification in the form name=research_dir",
    )
    parser.add_argument(
        "--status-file",
        action="append",
        default=[],
        help="Status specification in the form name=status_file",
    )
    return parser


def parse_mapping(values: list[str]) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"expected name=path mapping, got: {value}")
        name, raw_path = value.split("=", 1)
        mapping[name.strip()] = Path(raw_path.strip()).resolve()
    return mapping


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def count_promoted_strategies(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        import yaml

        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        strategies = payload.get("strategies", [])
        return len(strategies) if isinstance(strategies, list) else None
    except Exception:
        return None


def render_failed_tickers(values: Any) -> str | None:
    if not values:
        return None
    rendered: list[str] = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                ticker = item.get("ticker")
                message = item.get("message")
                error_type = item.get("error_type")
                parts = [str(ticker)] if ticker else []
                if error_type:
                    parts.append(str(error_type))
                if message:
                    parts.append(str(message))
                rendered.append(": ".join(parts) if parts else json.dumps(item, sort_keys=True))
            else:
                rendered.append(str(item))
    else:
        rendered.append(str(values))
    return "; ".join(rendered) if rendered else None


def summarize_wave(name: str, research_dir: Path) -> dict[str, Any]:
    master_summary_path = research_dir / "master_summary.json"
    promoted_yaml_path = research_dir / "promoted_strategies.yaml"
    shard_summary_path = research_dir / "shard_run_summary.json"
    master = load_json(master_summary_path)
    shard_summary = load_json(shard_summary_path)
    shared = (master or {}).get("shared_account") or {}
    family_rankings = (master or {}).get("family_rankings") or {}
    leading_bucket = None
    buckets = family_rankings.get("shared_account_buckets") or []
    if buckets:
        leading_bucket = buckets[0]
    return {
        "name": name,
        "research_dir": str(research_dir),
        "master_summary_exists": master_summary_path.exists(),
        "shard_summary_exists": shard_summary_path.exists(),
        "promoted_strategies_exists": promoted_yaml_path.exists(),
        "promoted_strategy_count": count_promoted_strategies(promoted_yaml_path),
        "strategy_set": (master or {}).get("strategy_set"),
        "tickers": (master or {}).get("tickers") or (shard_summary or {}).get("tickers"),
        "successful_tickers": (master or {}).get("successful_tickers") or (shard_summary or {}).get("successful_tickers"),
        "failed_tickers": (master or {}).get("failed_tickers") or (shard_summary or {}).get("failed_tickers"),
        "shared_account_final_equity": shared.get("final_equity"),
        "shared_account_total_return_pct": shared.get("total_return_pct"),
        "shared_account_trade_count": shared.get("trade_count"),
        "shared_account_max_drawdown_pct": shared.get("max_drawdown_pct"),
        "leading_family_bucket": leading_bucket,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Tournament Conveyor Summary")
    lines.append("")
    lines.append("## Status Files")
    for name, payload in summary["status_files"].items():
        lines.append(
            f"- `{name}`: phase=`{payload.get('phase')}` message=`{payload.get('message')}`"
        )
    lines.append("")
    lines.append("## Waves")
    for wave in summary["waves"]:
        lines.append(f"### {wave['name']}")
        lines.append(f"- research dir: `{wave['research_dir']}`")
        lines.append(f"- master summary exists: `{wave['master_summary_exists']}`")
        lines.append(f"- shard summary exists: `{wave['shard_summary_exists']}`")
        lines.append(f"- promoted strategies exists: `{wave['promoted_strategies_exists']}`")
        if wave["promoted_strategy_count"] is not None:
            lines.append(f"- promoted strategy count: `{wave['promoted_strategy_count']}`")
        if wave["tickers"]:
            lines.append(f"- tickers: `{', '.join(wave['tickers'])}`")
        if wave["successful_tickers"]:
            lines.append(f"- successful tickers: `{', '.join(wave['successful_tickers'])}`")
        if wave["failed_tickers"]:
            rendered_failed = render_failed_tickers(wave["failed_tickers"])
            if rendered_failed:
                lines.append(f"- failed tickers: `{rendered_failed}`")
        if wave["shared_account_final_equity"] is not None:
            lines.append(f"- shared-account final equity: `{wave['shared_account_final_equity']}`")
        if wave["shared_account_total_return_pct"] is not None:
            lines.append(f"- shared-account total return pct: `{wave['shared_account_total_return_pct']}`")
        if wave["shared_account_max_drawdown_pct"] is not None:
            lines.append(f"- shared-account max drawdown pct: `{wave['shared_account_max_drawdown_pct']}`")
        if wave["leading_family_bucket"]:
            bucket = wave["leading_family_bucket"]
            lines.append(
                f"- leading family bucket: `{bucket.get('family_bucket')}` pnl=`{bucket.get('portfolio_net_pnl')}` trades=`{bucket.get('trade_count')}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    wave_mapping = parse_mapping(args.wave)
    status_mapping = parse_mapping(args.status_file)

    summary = {
        "status_files": {
            name: load_json(path) or {"phase": "missing", "message": f"Missing status file: {path}"}
            for name, path in status_mapping.items()
        },
        "waves": [summarize_wave(name, path) for name, path in wave_mapping.items()],
    }

    json_path = output_dir / "tournament_conveyor_summary.json"
    md_path = output_dir / "tournament_conveyor_summary.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps({"summary_json": str(json_path), "summary_md": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()

