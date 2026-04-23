from __future__ import annotations

import argparse
import json
import textwrap
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
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
DEFAULT_ZONE = "us-east1-b"
DEFAULT_LOCAL_OUTPUT_DIR = REPO_ROOT / "output" / "gcp_execution_vm_headless_validation"
DEFAULT_BASE_STARTUP_SCRIPT = textwrap.dedent(
    """\
    #!/bin/bash
    set -euxo pipefail

    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y python3 python3-venv git jq

    mkdir -p /opt/codexalpaca /var/lib/codexalpaca /var/log/codexalpaca
    cat >/var/lib/codexalpaca/validation_mode.json <<'JSON'
    {
      "stack": "codexalpaca",
      "plane": "execution",
      "mode": "paper",
      "stage": "validation_only"
    }
    JSON

    cat >/etc/motd <<'MOTD'
    codexalpaca execution VM
    mode: validation-only
    do not start trading until the governed readiness gate is clean
    MOTD

    touch /var/lib/codexalpaca/bootstrap_complete
    """
).strip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the execution VM validation gate through a governed headless startup-script run.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--control-bucket", default=DEFAULT_CONTROL_BUCKET)
    parser.add_argument("--date-prefix", default=DEFAULT_DATE_PREFIX)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--local-output-dir", default=str(DEFAULT_LOCAL_OUTPUT_DIR))
    return parser


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def mint_token(credentials_json: Path) -> str:
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_json),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    return str(credentials.token)


def request_json(method: str, url: str, token: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw_error_body": body}
        return exc.code, parsed


def read_instance(project_id: str, zone: str, instance_name: str, token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}"
    status, payload = request_json("GET", url, token)
    if status >= 400:
        raise RuntimeError(f"Unable to read instance `{instance_name}`: {status} {payload}")
    return payload


def wait_for_zone_operation(project_id: str, zone: str, operation_name: str, token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/operations/{operation_name}"
    for _ in range(180):
        status, payload = request_json("GET", url, token)
        if status >= 400:
            raise RuntimeError(f"Zone operation poll failed: {status} {payload}")
        if payload.get("status") == "DONE":
            if payload.get("error"):
                raise RuntimeError(f"Zone operation failed: {payload['error']}")
            return payload
        import time

        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for zone operation `{operation_name}`")


def set_instance_metadata(project_id: str, zone: str, instance_name: str, fingerprint: str, items: list[dict[str, str]], token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}/setMetadata"
    status, payload = request_json("POST", url, token, {"fingerprint": fingerprint, "items": items})
    if status >= 400:
        raise RuntimeError(f"Unable to set metadata on `{instance_name}`: {status} {payload}")
    return payload


def reset_instance(project_id: str, zone: str, instance_name: str, token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}/reset"
    status, payload = request_json("POST", url, token, {})
    if status >= 400:
        raise RuntimeError(f"Unable to reset instance `{instance_name}`: {status} {payload}")
    return payload


def render_headless_startup_script(
    *,
    existing_startup_script: str,
    validation_script_gs_uri: str,
    control_bucket: str,
    control_prefix: str,
    run_id: str,
) -> str:
    existing = existing_startup_script.rstrip() + "\n" if existing_startup_script.strip() else ""
    script = f"""#!/bin/bash
set -euxo pipefail

RUN_ID={shell_quote(run_id)}
VALIDATION_SCRIPT_GS_URI={shell_quote(validation_script_gs_uri)}
CONTROL_BUCKET={shell_quote(control_bucket)}
CONTROL_PREFIX={shell_quote(control_prefix)}
RUN_ROOT="/var/lib/codexalpaca/validation-launch"
RUN_DIR="$RUN_ROOT/$RUN_ID"
LOG_PATH="/var/log/codexalpaca/validation-$RUN_ID.log"
MARKER_PATH="$RUN_DIR/complete.marker"
export RUN_ID
export LOG_PATH

mkdir -p "$RUN_DIR" /var/log/codexalpaca

if [[ -f "$MARKER_PATH" ]]; then
  exit 0
fi

{existing}

metadata_token() {{
  curl -fsS -H "Metadata-Flavor: Google" \\
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \\
    | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}}

download_gcs() {{
  local gcs_uri="$1"
  local dest_path="$2"
  python3 - <<'PY'
import os
import urllib.parse
import urllib.request
from pathlib import Path

token = os.environ["TOKEN"]
gcs_uri = os.environ["GCS_URI"]
dest_path = Path(os.environ["DEST_PATH"])
if not gcs_uri.startswith("gs://"):
    raise SystemExit("Invalid GCS URI")
bucket_and_object = gcs_uri[5:]
bucket, object_name = bucket_and_object.split("/", 1)
encoded = urllib.parse.quote(object_name, safe="")
url = f"https://storage.googleapis.com/storage/v1/b/{{bucket}}/o/{{encoded}}?alt=media"
req = urllib.request.Request(url, headers={{"Authorization": f"Bearer {{token}}"}})
with urllib.request.urlopen(req, timeout=180) as resp:
    data = resp.read()
dest_path.parent.mkdir(parents=True, exist_ok=True)
dest_path.write_bytes(data)
PY
}}

upload_file() {{
  local local_path="$1"
  local gcs_uri="$2"
  if [[ ! -f "$local_path" ]]; then
    return 0
  fi
  python3 - <<'PY'
import os
import urllib.parse
import urllib.request
from pathlib import Path

token = os.environ["TOKEN"]
local_path = Path(os.environ["LOCAL_PATH"])
gcs_uri = os.environ["UPLOAD_GCS_URI"]
if not gcs_uri.startswith("gs://"):
    raise SystemExit("Invalid GCS URI")
bucket_and_object = gcs_uri[5:]
bucket, object_name = bucket_and_object.split("/", 1)
encoded = urllib.parse.quote(object_name, safe="")
url = f"https://storage.googleapis.com/upload/storage/v1/b/{{bucket}}/o?uploadType=media&name={{encoded}}"
data = local_path.read_bytes()
req = urllib.request.Request(
    url,
    data=data,
    headers={{
        "Authorization": f"Bearer {{token}}",
        "Content-Type": "application/octet-stream",
    }},
    method="POST",
)
with urllib.request.urlopen(req, timeout=180) as resp:
    resp.read()
PY
}}

TOKEN="$(metadata_token)"
export TOKEN

VALIDATION_SCRIPT_PATH="$RUN_DIR/execution_vm_validation.sh"
export GCS_URI="$VALIDATION_SCRIPT_GS_URI"
export DEST_PATH="$VALIDATION_SCRIPT_PATH"
download_gcs "$VALIDATION_SCRIPT_GS_URI" "$VALIDATION_SCRIPT_PATH"
chmod +x "$VALIDATION_SCRIPT_PATH"

set +e
bash "$VALIDATION_SCRIPT_PATH" >"$LOG_PATH" 2>&1
VALIDATION_EXIT=$?
set -e
export VALIDATION_EXIT

LAUNCH_RESULT_PATH="$RUN_DIR/launch_result.json"
export LAUNCH_RESULT_PATH

python3 - <<'PY'
import json
import os
from datetime import datetime
from pathlib import Path

run_id = os.environ["RUN_ID"]
launch_result_path = Path(os.environ["LAUNCH_RESULT_PATH"])
validation_status_path = Path("/var/lib/codexalpaca/validation/validation_status.json")
doctor_path = Path("/var/lib/codexalpaca/validation/doctor.json")
pytest_log_path = Path("/var/lib/codexalpaca/validation/pytest.log")
payload = {{
    "generated_at": datetime.now().astimezone().isoformat(),
    "run_id": run_id,
    "validation_exit_code": int(os.environ["VALIDATION_EXIT"]),
    "validation_status_present": validation_status_path.exists(),
    "doctor_present": doctor_path.exists(),
    "pytest_log_present": pytest_log_path.exists(),
    "log_path": os.environ["LOG_PATH"],
}}
if validation_status_path.exists():
    try:
        payload["validation_status"] = json.loads(validation_status_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        payload["validation_status_read_error"] = str(exc)
launch_result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY

BASE_GCS_PREFIX="gs://$CONTROL_BUCKET/$CONTROL_PREFIX/$RUN_ID"
export LOCAL_PATH="$LAUNCH_RESULT_PATH"
export UPLOAD_GCS_URI="$BASE_GCS_PREFIX/launch_result.json"
upload_file "$LAUNCH_RESULT_PATH" "$UPLOAD_GCS_URI"

export LOCAL_PATH="$LOG_PATH"
export UPLOAD_GCS_URI="$BASE_GCS_PREFIX/validation-run.log"
upload_file "$LOG_PATH" "$UPLOAD_GCS_URI"

export LOCAL_PATH="/var/lib/codexalpaca/validation/validation_status.json"
export UPLOAD_GCS_URI="$BASE_GCS_PREFIX/validation_status.json"
upload_file "$LOCAL_PATH" "$UPLOAD_GCS_URI"

export LOCAL_PATH="/var/lib/codexalpaca/validation/doctor.json"
export UPLOAD_GCS_URI="$BASE_GCS_PREFIX/doctor.json"
upload_file "$LOCAL_PATH" "$UPLOAD_GCS_URI"

export LOCAL_PATH="/var/lib/codexalpaca/validation/pytest.log"
export UPLOAD_GCS_URI="$BASE_GCS_PREFIX/pytest.log"
upload_file "$LOCAL_PATH" "$UPLOAD_GCS_URI"

touch "$MARKER_PATH"
exit "$VALIDATION_EXIT"
"""
    return textwrap.dedent(script).strip() + "\n"


def is_headless_composite_script(text: str) -> bool:
    return "RUN_ROOT=\"/var/lib/codexalpaca/validation-launch\"" in text


def upload_file(client: storage.Client, bucket_name: str, object_name: str, local_path: Path, content_type: str | None = None) -> None:
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
    lines: list[str] = []
    lines.append("# GCP Execution VM Headless Validation Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Zone: `{payload['zone']}`")
    lines.append(f"- Run ID: `{payload['run_id']}`")
    lines.append(f"- Launch state: `{payload['launch_state']}`")
    lines.append("")
    lines.append("## Audit Objects")
    lines.append("")
    lines.append(f"- Composite startup script (local): `{payload['local_startup_script_path']}`")
    lines.append(f"- Composite startup script (GCS): `{payload['startup_script_gs_uri']}`")
    lines.append(f"- Validation result prefix: `{payload['validation_result_gcs_prefix']}`")
    lines.append("")
    lines.append("## Trigger")
    lines.append("")
    lines.append(f"- Metadata operation: `{payload['metadata_operation_name']}`")
    lines.append(f"- Reset operation: `{payload['reset_operation_name']}`")
    lines.append("")
    lines.append("## Follow-Up")
    lines.append("")
    for item in list(payload.get("next_actions") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    credentials_json = Path(args.credentials_json).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    local_output_dir = Path(args.local_output_dir).resolve()
    local_output_dir.mkdir(parents=True, exist_ok=True)

    validation_status_path = report_dir / "gcp_execution_vm_validation_status.json"
    validation_payload = json.loads(validation_status_path.read_text(encoding="utf-8"))
    validation_script_gs_uri = str(validation_payload["validation_script_gs_uri"])

    token = mint_token(credentials_json)
    instance_payload = read_instance(args.project_id, args.zone, args.vm_name, token)
    metadata = instance_payload.get("metadata") or {}
    items = list(metadata.get("items") or [])
    fingerprint = str(metadata.get("fingerprint") or "")

    run_id = f"{args.vm_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    control_prefix = f"bootstrap/{args.date_prefix}/foundation-phase5-headless-validation"

    existing_startup_script = ""
    base_startup_script = ""
    other_items: list[dict[str, str]] = []
    for item in items:
        key = str(item.get("key") or "")
        value = str(item.get("value") or "")
        if key == "codexalpaca-base-startup-script":
            base_startup_script = value
            continue
        if key == "startup-script":
            existing_startup_script = value
            continue
        if key in {
            "codexalpaca-validation-run-id",
            "codexalpaca-validation-script-gs-uri",
            "codexalpaca-validation-control-prefix",
            "codexalpaca-validation-launch-mode",
        }:
            continue
        other_items.append({"key": key, "value": value})

    if not base_startup_script:
        if existing_startup_script and not is_headless_composite_script(existing_startup_script):
            base_startup_script = existing_startup_script
        else:
            base_startup_script = DEFAULT_BASE_STARTUP_SCRIPT

    composite_script_text = render_headless_startup_script(
        existing_startup_script=base_startup_script,
        validation_script_gs_uri=validation_script_gs_uri,
        control_bucket=args.control_bucket,
        control_prefix=control_prefix,
        run_id=run_id,
    )

    startup_script_name = f"execution_vm_headless_validation_startup_{args.vm_name}_{run_id}.sh"
    local_startup_script_path = local_output_dir / startup_script_name
    write_unix_text(local_startup_script_path, composite_script_text)
    startup_script_object = f"{control_prefix}/{startup_script_name}"

    creds = service_account.Credentials.from_service_account_file(str(credentials_json))
    client = storage.Client(project=args.project_id, credentials=creds)
    upload_file(client, args.control_bucket, startup_script_object, local_startup_script_path, "text/x-shellscript")

    updated_items = other_items + [
        {"key": "codexalpaca-base-startup-script", "value": base_startup_script},
        {"key": "startup-script", "value": composite_script_text},
        {"key": "codexalpaca-validation-run-id", "value": run_id},
        {"key": "codexalpaca-validation-script-gs-uri", "value": validation_script_gs_uri},
        {"key": "codexalpaca-validation-control-prefix", "value": f"gs://{args.control_bucket}/{control_prefix}/{run_id}"},
        {"key": "codexalpaca-validation-launch-mode", "value": "headless_startup"},
    ]

    metadata_operation = set_instance_metadata(
        args.project_id,
        args.zone,
        args.vm_name,
        fingerprint,
        updated_items,
        token,
    )
    metadata_operation_name = str(metadata_operation.get("name") or "")
    wait_for_zone_operation(args.project_id, args.zone, metadata_operation_name, token)

    reset_operation = reset_instance(args.project_id, args.zone, args.vm_name, token)
    reset_operation_name = str(reset_operation.get("name") or "")
    wait_for_zone_operation(args.project_id, args.zone, reset_operation_name, token)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "vm_name": args.vm_name,
        "zone": args.zone,
        "run_id": run_id,
        "launch_state": "headless_validation_triggered",
        "local_startup_script_path": str(local_startup_script_path),
        "startup_script_gs_uri": f"gs://{args.control_bucket}/{startup_script_object}",
        "validation_result_gcs_prefix": f"gs://{args.control_bucket}/{control_prefix}/{run_id}",
        "validation_script_gs_uri": validation_script_gs_uri,
        "metadata_operation_name": metadata_operation_name,
        "reset_operation_name": reset_operation_name,
        "next_actions": [
            "Wait a few minutes for the VM reset and startup script to complete.",
            f"Inspect the GCS result prefix at gs://{args.control_bucket}/{control_prefix}/{run_id} for launch_result.json, validation_status.json, doctor.json, and pytest.log.",
            "Only if the headless validation packet is clean should the next step move to a trusted validation session.",
        ],
    }

    json_path = report_dir / "gcp_execution_vm_headless_validation_status.json"
    md_path = report_dir / "gcp_execution_vm_headless_validation_status.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
