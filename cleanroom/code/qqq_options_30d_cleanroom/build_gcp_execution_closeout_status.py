from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_GCS_PREFIX = "gs://codexalpaca-control-us/gcp_foundation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the exclusive-window closeout packet for the sanctioned GCP trusted validation session."
    )
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--gcs-prefix", default=DEFAULT_GCS_PREFIX)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_payload(
    *,
    report_dir: Path,
    vm_name: str,
    gcs_prefix: str,
    exclusive_window_status: dict[str, Any],
    trusted_validation_status: dict[str, Any],
    launch_pack: dict[str, Any],
    assimilation_status: dict[str, Any],
) -> dict[str, Any]:
    attestation_path = Path(
        str(
            exclusive_window_status.get("attestation_json_path")
            or report_dir / "gcp_execution_exclusive_window_attestation.json"
        )
    )
    attestation_present = attestation_path.exists()
    assimilation_ready = str(assimilation_status.get("status") or "") == "ready_for_post_session_assimilation"
    exclusive_window_state = str(exclusive_window_status.get("exclusive_window_state") or "missing")
    exclusive_window_status_value = str(exclusive_window_status.get("exclusive_window_status") or "missing")
    trusted_readiness = str(trusted_validation_status.get("trusted_validation_readiness") or "missing")
    launch_pack_state = str(launch_pack.get("launch_pack_state") or "missing")

    closeout_status = "blocked"
    operator_actions: list[str] = []
    if not attestation_present:
        closeout_status = "window_already_closed"
        operator_actions = [
            "The live exclusive-window attestation is already absent.",
            "Keep the sanctioned VM idle until a fresh bounded window is armed for the next broker-facing session.",
            "Use the post-session assimilation packet and morning brief to drive review instead of re-arming automatically.",
        ]
    elif assimilation_ready:
        closeout_status = "ready_to_close_window"
        operator_actions = [
            "Archive and remove the live exclusive-window attestation after the sanctioned VM session ends.",
            "Rebuild the exclusive-window, trusted-validation, and launch-pack packets immediately after closeout.",
            "Mirror the refreshed closeout packet set to the GCS control bucket so the cloud control surface no longer shows an armed window.",
        ]
    else:
        operator_actions = [
            "Do not close the exclusive window yet because the governed post-session assimilation lane is not ready.",
            "Repair the assimilation path first, then disarm the window and refresh the control-plane packets.",
        ]

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "closeout_status": closeout_status,
        "vm_name": vm_name,
        "gcs_prefix": gcs_prefix,
        "attestation_json_path": str(attestation_path),
        "attestation_present": attestation_present,
        "exclusive_window_state": exclusive_window_state,
        "exclusive_window_status": exclusive_window_status_value,
        "trusted_validation_readiness": trusted_readiness,
        "launch_pack_state": launch_pack_state,
        "assimilation_status": str(assimilation_status.get("status") or "missing"),
        "operator_actions": operator_actions,
        "guardrails": [
            "Do not leave a stale exclusive-window attestation armed after the sanctioned VM session is over.",
            "Do not auto-rearm the next session window during closeout.",
            "Do not skip the post-session assimilation review before deciding whether another bounded window should be opened.",
        ],
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Closeout Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Closeout status: `{payload['closeout_status']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Attestation present: `{payload['attestation_present']}`",
        f"- Exclusive window state: `{payload['exclusive_window_state']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Trusted validation readiness: `{payload['trusted_validation_readiness']}`",
        f"- Launch pack state: `{payload['launch_pack_state']}`",
        f"- Assimilation status: `{payload['assimilation_status']}`",
        f"- GCS prefix: `{payload['gcs_prefix']}`",
        "",
        "## Operator Actions",
        "",
    ]
    for action in list(payload.get("operator_actions") or []):
        lines.append(f"- {action}")
    lines.extend(["", "## Guardrails", ""])
    for item in list(payload.get("guardrails") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution Closeout Handoff",
        "",
        f"- Closeout status: `{payload['closeout_status']}`",
        f"- Attestation present: `{payload['attestation_present']}`",
        f"- Exclusive window status: `{payload['exclusive_window_status']}`",
        f"- Assimilation status: `{payload['assimilation_status']}`",
        "",
        "## Operator Rule",
        "",
        "- After the sanctioned VM session ends, archive and remove the exclusive-window attestation before treating the lane as idle again.",
        "- Refresh the control-plane packets and mirror them to GCS so the cloud control surface shows the closed state.",
        "- Do not open another broker-facing session until a fresh bounded window is armed.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(
        report_dir=report_dir,
        vm_name=args.vm_name,
        gcs_prefix=args.gcs_prefix,
        exclusive_window_status=read_json(report_dir / "gcp_execution_exclusive_window_status.json"),
        trusted_validation_status=read_json(report_dir / "gcp_execution_trusted_validation_session_status.json"),
        launch_pack=read_json(report_dir / "gcp_execution_trusted_validation_launch_pack.json"),
        assimilation_status=read_json(report_dir / "gcp_post_session_assimilation_status.json"),
    )
    write_json(report_dir / "gcp_execution_closeout_status.json", payload)
    write_markdown(report_dir / "gcp_execution_closeout_status.md", payload)
    write_handoff(report_dir / "gcp_execution_closeout_handoff.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
