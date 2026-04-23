from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import storage
from google.oauth2 import service_account


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CREDENTIALS_JSON = Path(r"C:\Users\rabisaab\Downloads\codexalpaca-7bcb9ac9a02d.json")
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_CONTROL_BUCKET = "codexalpaca-control-us"
DEFAULT_DATE_PREFIX = "2026-04-23"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_EXPECTED_STATIC_IP = "34.139.193.220"
DEFAULT_ZONE = "us-east1-b"
DEFAULT_GCS_LEASE_URI = "gs://codexalpaca-control-us/leases/paper-execution/lease.json"
DEFAULT_LOCAL_OUTPUT_DIR = REPO_ROOT / "output" / "gcp_execution_vm_lease_dry_run_validation"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare the execution VM lease dry-run validation script and status packet."
    )
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--control-bucket", default=DEFAULT_CONTROL_BUCKET)
    parser.add_argument("--date-prefix", default=DEFAULT_DATE_PREFIX)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--expected-static-ip", default=DEFAULT_EXPECTED_STATIC_IP)
    parser.add_argument("--gcs-lease-uri", default=DEFAULT_GCS_LEASE_URI)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--local-output-dir", default=str(DEFAULT_LOCAL_OUTPUT_DIR))
    return parser


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def render_validation_script(
    *,
    vm_name: str,
    expected_static_ip: str,
    runtime_bootstrap_script_gs_uri: str,
    gcs_lease_uri: str,
) -> str:
    script = f"""#!/usr/bin/env bash
set -euo pipefail

VM_NAME={shell_quote(vm_name)}
EXPECTED_STATIC_IP={shell_quote(expected_static_ip)}
RUNTIME_BOOTSTRAP_SCRIPT_GS_URI={shell_quote(runtime_bootstrap_script_gs_uri)}
GCS_LEASE_URI={shell_quote(gcs_lease_uri)}
WORK_DIR="/var/lib/codexalpaca/lease-validation"
RUNTIME_BOOTSTRAP_PATH="$WORK_DIR/runtime_bootstrap.sh"
STATUS_PATH="$WORK_DIR/lease_validation_status.json"
LEASE_LOG_PATH="$WORK_DIR/lease_validation.log"
DOCTOR_PATH="$WORK_DIR/doctor.json"
PYTEST_LOG_PATH="$WORK_DIR/pytest_targeted.log"

mkdir -p "$WORK_DIR"

metadata_token() {{
  curl -fsS -H "Metadata-Flavor: Google" \\
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \\
    | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}}

metadata_external_ip() {{
  curl -fsS -H "Metadata-Flavor: Google" \\
    "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip"
}}

TOKEN="$(metadata_token)"
OBSERVED_EXTERNAL_IP="$(metadata_external_ip)"
export TOKEN
export OBSERVED_EXTERNAL_IP

if [[ "$OBSERVED_EXTERNAL_IP" != "$EXPECTED_STATIC_IP" ]]; then
  echo "Expected static IP $EXPECTED_STATIC_IP but observed $OBSERVED_EXTERNAL_IP" >&2
  exit 1
fi

python3 - <<'PY'
import os
import urllib.parse
import urllib.request

token = os.environ["TOKEN"]
gcs_uri = {json.dumps(runtime_bootstrap_script_gs_uri)}
dest = {json.dumps("/var/lib/codexalpaca/lease-validation/runtime_bootstrap.sh")}
if not gcs_uri.startswith("gs://"):
    raise SystemExit("Invalid GCS URI")
bucket_and_object = gcs_uri[5:]
bucket, object_name = bucket_and_object.split("/", 1)
encoded = urllib.parse.quote(object_name, safe="")
url = f"https://storage.googleapis.com/storage/v1/b/{{bucket}}/o/{{encoded}}?alt=media"
req = urllib.request.Request(url, headers={{"Authorization": f"Bearer {{token}}"}})
with urllib.request.urlopen(req, timeout=120) as resp:
    data = resp.read()
with open(dest, "wb") as fh:
    fh.write(data)
PY

chmod +x "$RUNTIME_BOOTSTRAP_PATH"
bash "$RUNTIME_BOOTSTRAP_PATH"

cd /opt/codexalpaca/codexalpaca_repo
./.venv/bin/python -m pip install -e '.[dev,gcp]'
./.venv/bin/python scripts/doctor.py --skip-connectivity --json > "$DOCTOR_PATH"
set +e
./.venv/bin/python -m pytest -q tests/test_execution_ownership.py tests/test_multi_ticker_portfolio.py > "$PYTEST_LOG_PATH" 2>&1
TARGETED_PYTEST_EXIT=$?
set -e
export TARGETED_PYTEST_EXIT

export MULTI_TICKER_OWNERSHIP_ENABLED=true
export MULTI_TICKER_OWNERSHIP_LEASE_BACKEND=gcs_generation_match
export MULTI_TICKER_OWNERSHIP_GCS_LEASE_URI="$GCS_LEASE_URI"
export MULTI_TICKER_MACHINE_LABEL="$VM_NAME"
export MULTI_TICKER_OWNERSHIP_TTL_SECONDS=180

set +e
./.venv/bin/python - <<'PY' > "$LEASE_LOG_PATH" 2>&1
import json
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from alpaca_lab.config import load_settings
from alpaca_lab.execution import ownership as ownership_module
from alpaca_lab.execution.ownership import GenerationMatchOwnershipLease
from alpaca_lab.multi_ticker_portfolio import MultiTickerPortfolioPaperTrader, load_portfolio_config

status_path = Path("/var/lib/codexalpaca/lease-validation/lease_validation_status.json")
lease_uri = {json.dumps(gcs_lease_uri)}
base_time = datetime(2026, 4, 23, 20, 0, tzinfo=UTC)
role_name = "portfolio_trader"
results: dict[str, object] = {{
    "generated_at": datetime.now().astimezone().isoformat(),
    "vm_name": {json.dumps(vm_name)},
    "lease_uri": lease_uri,
    "expected_static_ip": {json.dumps(expected_static_ip)},
    "observed_external_ip": None,
    "targeted_pytest_exit_code": None,
}}


def env(name: str) -> str:
    import os
    return str(os.environ[name])


results["observed_external_ip"] = env("OBSERVED_EXTERNAL_IP")
results["targeted_pytest_exit_code"] = int(env("TARGETED_PYTEST_EXIT"))


def pack(status):
    return {{
        "enabled": bool(status.enabled),
        "acquired": bool(status.acquired),
        "held_by_self": bool(status.held_by_self),
        "owner_id": status.owner_id,
        "owner_label": status.owner_label,
        "blocked_by_owner_id": status.blocked_by_owner_id,
        "blocked_by_owner_label": status.blocked_by_owner_label,
        "lease_path": status.lease_path,
        "heartbeat_at": status.heartbeat_at,
        "expires_at": status.expires_at,
        "generation": status.generation,
        "roles": status.roles,
    }}


def git_commit(repo_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--short=12", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    return (result.stdout or "").strip() or None


cleanup_steps: list[str] = []
original_now = ownership_module._now_utc
trader = None
try:
    settings = load_settings()
    cfg = load_portfolio_config("config/multi_ticker_paper_portfolio.yaml")
    trader = MultiTickerPortfolioPaperTrader(
        settings,
        cfg,
        broker=object(),
        submit_paper_orders=False,
    )
    results["lease_backend"] = cfg.ownership.lease_backend
    results["machine_label"] = cfg.ownership.machine_label
    results["trader_submit_paper_orders"] = trader.submit_paper_orders
    results["ownership_lease_class"] = trader.ownership_lease.__class__.__name__
    if not isinstance(trader.ownership_lease, GenerationMatchOwnershipLease):
        raise RuntimeError(
            f"Expected GenerationMatchOwnershipLease but got {{trader.ownership_lease.__class__.__name__}}"
        )

    store = trader.ownership_lease.store
    initial_record = store.read()
    results["initial_record_present"] = initial_record is not None
    if initial_record is not None:
        results["initial_record"] = {{
            "generation": initial_record.generation,
            "payload": initial_record.payload,
        }}
        raise RuntimeError("Lease object already existed before dry-run validation started.")

    ownership_module._now_utc = lambda: base_time
    acquired = trader.acquire_runtime_ownership(role=role_name)
    if not acquired.acquired:
        raise RuntimeError(f"Initial lease acquire failed: {{pack(acquired)}}")

    blocked_owner = GenerationMatchOwnershipLease(
        store=store,
        lease_path=lease_uri,
        owner_id="blocked-owner",
        owner_label="blocked-owner@desktop",
        ttl_seconds=cfg.ownership.lease_ttl_seconds,
        machine_label="desktop-blocked",
        runner_path=str(Path.cwd()),
        git_commit=git_commit(Path.cwd()),
        audit_context={{"plane": "execution", "environment": "paper", "source": "workstation", "validation": "lease_dry_run"}},
    )
    blocked = blocked_owner.acquire(role=role_name, metadata={{"phase": "blocked_attempt"}})
    renewed = trader.acquire_runtime_ownership(role=role_name)
    if not renewed.acquired:
        raise RuntimeError(f"Renewal failed: {{pack(renewed)}}")

    ownership_module._now_utc = lambda: base_time + timedelta(minutes=10)
    takeover_owner = GenerationMatchOwnershipLease(
        store=store,
        lease_path=lease_uri,
        owner_id="takeover-owner",
        owner_label="takeover-owner@desktop",
        ttl_seconds=cfg.ownership.lease_ttl_seconds,
        machine_label="desktop-takeover",
        runner_path=str(Path.cwd()),
        git_commit=git_commit(Path.cwd()),
        audit_context={{"plane": "execution", "environment": "paper", "source": "workstation", "validation": "lease_dry_run"}},
    )
    takeover = takeover_owner.acquire(role=role_name, metadata={{"phase": "takeover"}})
    if not takeover.acquired or takeover.owner_id != "takeover-owner":
        raise RuntimeError(f"Stale takeover failed: {{pack(takeover)}}")

    takeover_renewed = takeover_owner.renew(role=role_name, metadata={{"phase": "takeover_renew"}})
    released = takeover_owner.release(role=role_name)
    final_record = store.read()

    results.update(
        {{
            "acquired": pack(acquired),
            "blocked": pack(blocked),
            "renewed": pack(renewed),
            "takeover": pack(takeover),
            "takeover_renewed": pack(takeover_renewed),
            "released": pack(released),
            "final_record_present": final_record is not None,
            "final_record": None if final_record is None else {{
                "generation": final_record.generation,
                "payload": final_record.payload,
            }},
            "lease_dry_run_passed": (
                blocked.blocked
                and blocked.blocked_by_owner_id == trader.ownership_lease.owner_id
                and takeover.acquired
                and final_record is None
            ),
        }}
    )
except Exception as exc:  # noqa: BLE001
    results["lease_dry_run_passed"] = False
    results["error"] = str(exc)
finally:
    ownership_module._now_utc = original_now
    try:
        if trader is not None and isinstance(getattr(trader, "ownership_lease", None), GenerationMatchOwnershipLease):
            cleanup_result = trader.ownership_lease.release(role=role_name)
            cleanup_steps.append(f"trader_release={{json.dumps(pack(cleanup_result), sort_keys=True)}}")
    except Exception as exc:  # noqa: BLE001
        cleanup_steps.append(f"trader_release_error={{exc}}")
    try:
        store = None if trader is None or not isinstance(getattr(trader, "ownership_lease", None), GenerationMatchOwnershipLease) else trader.ownership_lease.store
        if store is not None:
            cleanup_steps.append(f"post_cleanup_record_present={{store.read() is not None}}")
    except Exception as exc:  # noqa: BLE001
        cleanup_steps.append(f"post_cleanup_record_error={{exc}}")
    results["cleanup_steps"] = cleanup_steps
    status_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    if not results.get("lease_dry_run_passed"):
        raise SystemExit(1)
PY
LEASE_EXIT=$?
set -e
export LEASE_EXIT

python3 - <<'PY'
import json
import os
from pathlib import Path
from datetime import datetime

status_path = Path("/var/lib/codexalpaca/lease-validation/lease_validation_status.json")
if not status_path.exists():
    payload = {{
        "generated_at": datetime.now().astimezone().isoformat(),
        "vm_name": os.environ["VM_NAME"],
        "lease_uri": os.environ["GCS_LEASE_URI"],
        "expected_static_ip": os.environ["EXPECTED_STATIC_IP"],
        "observed_external_ip": os.environ["OBSERVED_EXTERNAL_IP"],
        "lease_dry_run_passed": False,
        "lease_exit_code": int(os.environ["LEASE_EXIT"]),
        "targeted_pytest_exit_code": int(os.environ["TARGETED_PYTEST_EXIT"]),
        "error": "lease_validation_status.json was not produced",
    }}
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
else:
    payload = json.loads(status_path.read_text(encoding="utf-8"))
    payload["lease_exit_code"] = int(os.environ["LEASE_EXIT"])
    payload["targeted_pytest_exit_code"] = int(os.environ["TARGETED_PYTEST_EXIT"])
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

if [[ "$TARGETED_PYTEST_EXIT" -ne 0 ]]; then
  echo "Targeted VM lease tests failed before lease dry-run." >&2
  exit "$TARGETED_PYTEST_EXIT"
fi

exit "$LEASE_EXIT"
"""
    return textwrap.dedent(script).strip() + "\n"


def upload_file(
    client: storage.Client,
    bucket_name: str,
    object_name: str,
    local_path: Path,
    content_type: str | None = None,
) -> None:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    if content_type:
        blob.upload_from_filename(str(local_path), content_type=content_type)
    else:
        blob.upload_from_filename(str(local_path))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_unix_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution VM Lease Dry-Run Validation Status",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Project ID: `{payload['project_id']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Zone: `{payload['zone']}`",
        f"- Expected static IP: `{payload['expected_static_ip']}`",
        f"- Lease URI: `{payload['gcs_lease_uri']}`",
        "",
        "## Validation Script",
        "",
        f"- Local path: `{payload['local_validation_script_path']}`",
        f"- Control bucket URI: `{payload['validation_script_gs_uri']}`",
        f"- Runtime bootstrap script URI: `{payload['runtime_bootstrap_script_gs_uri']}`",
        "",
        "## Guardrails",
        "",
    ]
    for row in list(payload.get("guardrails") or []):
        lines.append(f"- {row}")
    lines.extend(["", "## Validation Gate", ""])
    for row in list(payload.get("required_checks") or []):
        lines.append(f"- `{row}`")
    lines.extend(["", "## Next Actions", ""])
    for action in list(payload.get("next_actions") or []):
        lines.append(f"- {action}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution VM Lease Dry-Run Validation Handoff",
        "",
        f"- Validation phase: `{payload['validation_phase']}`",
        f"- Validation state: `{payload['validation_state']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Lease URI: `{payload['gcs_lease_uri']}`",
        f"- Script URI: `{payload['validation_script_gs_uri']}`",
        "",
        "## What This Validates",
        "",
        "- Runtime bootstrap refreshes the sanctioned VM from the current runner bundle.",
        "- The runner can install the optional `gcp` dependency path on-VM.",
        "- The trader can build the GCS generation-match ownership lease through explicit non-default config.",
        "- Acquire, renew, blocked contention, stale takeover, and release can be exercised without starting a broker-facing session.",
        "",
        "## Operator Rule",
        "",
        "- Do not treat the shared execution lease as broker-facing ready until the headless lease dry-run review passes.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    credentials_json = Path(args.credentials_json).resolve()
    local_output_dir = Path(args.local_output_dir).resolve()
    local_output_dir.mkdir(parents=True, exist_ok=True)

    runtime_status_path = report_dir / "gcp_execution_vm_runtime_bootstrap_status.json"
    runtime_payload = json.loads(runtime_status_path.read_text(encoding="utf-8"))
    runtime_bootstrap_script_gs_uri = str(runtime_payload["bootstrap_script_gs_uri"])

    validation_script_name = (
        f"execution_vm_lease_dry_run_validation_{args.vm_name}_{args.date_prefix.replace('-', '')}.sh"
    )
    local_validation_script_path = local_output_dir / validation_script_name
    validation_script_object = (
        f"bootstrap/{args.date_prefix}/foundation-phase17-lease-dry-run-validation/{validation_script_name}"
    )

    script_text = render_validation_script(
        vm_name=args.vm_name,
        expected_static_ip=args.expected_static_ip,
        runtime_bootstrap_script_gs_uri=runtime_bootstrap_script_gs_uri,
        gcs_lease_uri=args.gcs_lease_uri,
    )
    write_unix_text(local_validation_script_path, script_text)

    creds = service_account.Credentials.from_service_account_file(str(credentials_json))
    client = storage.Client(project=args.project_id, credentials=creds)
    upload_file(client, args.control_bucket, validation_script_object, local_validation_script_path, "text/x-shellscript")

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "validation_phase": "foundation-phase17-lease-dry-run-validation",
        "validation_state": "script_published",
        "vm_name": args.vm_name,
        "zone": args.zone,
        "expected_static_ip": args.expected_static_ip,
        "gcs_lease_uri": args.gcs_lease_uri,
        "local_validation_script_path": str(local_validation_script_path),
        "validation_script_gs_uri": f"gs://{args.control_bucket}/{validation_script_object}",
        "runtime_bootstrap_script_gs_uri": runtime_bootstrap_script_gs_uri,
        "required_checks": [
            "Observed VM external IP matches the reserved execution static IP.",
            "Runtime bootstrap completes from the current sanctioned runner bundle.",
            "The VM can install the optional gcp dependency path.",
            "Targeted ownership and trader tests pass on-VM.",
            "Trader-side GCS lease wiring acquires, renews, blocks contention, steals after expiry, and releases cleanly.",
            "The shared lease object is absent again after release.",
        ],
        "guardrails": [
            "The validation script is non-broker-facing: it does not call trader.run() and constructs the trader with broker=object().",
            "Ownership remains enabled only inside the validation process through session-scoped env overrides.",
            "The dry-run aborts immediately if the lease object already exists before validation starts.",
            "The default runner path remains on the file lease until a later promotion step explicitly changes it.",
        ],
        "next_actions": [
            "Launch this validation through the governed headless VM reset path.",
            "Wait for the result prefix to contain launch_result.json, lease_validation_status.json, doctor.json, pytest_targeted.log, lease_validation.log, and validation-run.log.",
            "Only if the review packet passes should the next step move toward broker-facing trusted validation.",
        ],
    }

    json_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_status.json"
    md_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_status.md"
    handoff_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_handoff.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_handoff(handoff_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
