from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REGISTRY_JSON = REPO_ROOT / "docs" / "gcp_foundation" / "gcp_foundation_readiness.json"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a concise handoff from the GCP foundation readiness registry."
    )
    parser.add_argument("--registry-json", default=str(DEFAULT_REGISTRY_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Foundation Readiness Handoff")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Foundation status: `{payload['foundation_status']}`")
    lines.append(f"- Recommended rollout mode: `{payload['recommended_rollout_mode']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Service account: `{payload['service_account']}`")
    lines.append("")
    lines.append("## Available Now")
    lines.append("")
    for item in list(payload.get("available_now") or []):
        lines.append(f"- `{item}`")
    if not list(payload.get("available_now") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Blocked Now")
    lines.append("")
    for item in list(payload.get("blocked_now") or []):
        lines.append(f"- `{item}`")
    if not list(payload.get("blocked_now") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for item in list(payload.get("next_actions") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    registry = read_json(Path(args.registry_json).resolve())
    project = dict(registry.get("project") or {})
    foundation_status = str(registry.get("foundation_status") or "unknown")
    if foundation_status == "foundation_ready":
        rollout_mode = "provision_foundation_now"
    elif foundation_status == "foundation_partial":
        rollout_mode = "finish_permissions_then_provision"
    elif foundation_status == "bootstrap_storage_only":
        rollout_mode = "storage_bootstrap_only"
    else:
        rollout_mode = "blocked"

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "foundation_status": foundation_status,
        "recommended_rollout_mode": rollout_mode,
        "project_id": project.get("project_id"),
        "service_account": project.get("client_email"),
        "available_now": list(registry.get("available_capabilities") or []),
        "blocked_now": list(registry.get("blocked_capabilities") or []),
        "next_actions": list(registry.get("next_actions") or []),
    }

    write_json(report_dir / "gcp_foundation_readiness_handoff.json", payload)
    write_markdown(report_dir / "gcp_foundation_readiness_handoff.md", payload)


if __name__ == "__main__":
    main()
