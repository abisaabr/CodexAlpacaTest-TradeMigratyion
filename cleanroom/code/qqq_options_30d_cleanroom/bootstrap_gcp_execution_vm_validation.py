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
DEFAULT_LOCAL_OUTPUT_DIR = REPO_ROOT / "output" / "gcp_execution_vm_validation"
DEFAULT_ZONE = "us-east1-b"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the execution VM validation script and status packet.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--control-bucket", default=DEFAULT_CONTROL_BUCKET)
    parser.add_argument("--date-prefix", default=DEFAULT_DATE_PREFIX)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--expected-static-ip", default=DEFAULT_EXPECTED_STATIC_IP)
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
) -> str:
    script = f"""#!/usr/bin/env bash
set -euo pipefail

VM_NAME={shell_quote(vm_name)}
EXPECTED_STATIC_IP={shell_quote(expected_static_ip)}
RUNTIME_BOOTSTRAP_SCRIPT_GS_URI={shell_quote(runtime_bootstrap_script_gs_uri)}
WORK_DIR="/var/lib/codexalpaca/validation"
RUNTIME_BOOTSTRAP_PATH="$WORK_DIR/runtime_bootstrap.sh"
STATUS_PATH="$WORK_DIR/validation_status.json"
DOCTOR_PATH="$WORK_DIR/doctor.json"
PYTEST_LOG_PATH="$WORK_DIR/pytest.log"

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
import os, urllib.parse, urllib.request

token = os.environ["TOKEN"]
gcs_uri = {json.dumps(runtime_bootstrap_script_gs_uri)}
dest = {json.dumps("/var/lib/codexalpaca/validation/runtime_bootstrap.sh")}
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
./.venv/bin/python scripts/doctor.py --skip-connectivity --json > "$DOCTOR_PATH"
set +e
./.venv/bin/python -m pytest -q > "$PYTEST_LOG_PATH" 2>&1
PYTEST_EXIT=$?
set -e
export PYTEST_EXIT

python3 - <<'PY'
import os
from pathlib import Path
from datetime import datetime
import json

doctor_path = Path("/var/lib/codexalpaca/validation/doctor.json")
pytest_log_path = Path("/var/lib/codexalpaca/validation/pytest.log")
status_path = Path("/var/lib/codexalpaca/validation/validation_status.json")

doctor_payload = json.loads(doctor_path.read_text(encoding="utf-8"))
payload = {{
    "generated_at": datetime.now().astimezone().isoformat(),
    "vm_name": {json.dumps(vm_name)},
    "expected_static_ip": {json.dumps(expected_static_ip)},
    "observed_external_ip": os.environ["OBSERVED_EXTERNAL_IP"],
    "runtime_bootstrap_complete": True,
    "doctor_path": str(doctor_path),
    "doctor_paper_only_repo_lock": doctor_payload.get("paper_only_repo_lock"),
    "doctor_using_project_venv": doctor_payload.get("using_project_venv"),
    "doctor_python_ok": doctor_payload.get("python_ok"),
    "pytest_log_path": str(pytest_log_path),
    "pytest_exit_code": int(os.environ["PYTEST_EXIT"]),
}}
status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
PY
"""
    return textwrap.dedent(script).strip() + "\n"


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
    lines.append("# GCP Execution VM Validation Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Zone: `{payload['zone']}`")
    lines.append(f"- Expected static IP: `{payload['expected_static_ip']}`")
    lines.append("")
    lines.append("## Validation Script")
    lines.append("")
    lines.append(f"- Local path: `{payload['local_validation_script_path']}`")
    lines.append(f"- Control bucket URI: `{payload['validation_script_gs_uri']}`")
    lines.append(f"- Runtime bootstrap script URI: `{payload['runtime_bootstrap_script_gs_uri']}`")
    lines.append("")
    lines.append("## Operator Commands")
    lines.append("")
    lines.append(f"- IAP SSH: `{payload['iap_ssh_command']}`")
    lines.append("- On-VM validation fetch/run:")
    lines.append("```bash")
    lines.append(str(payload["vm_validation_run_command"]))
    lines.append("```")
    lines.append("")
    lines.append("## Validation Gate")
    lines.append("")
    for row in list(payload.get("required_checks") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for action in list(payload.get("next_actions") or []):
        lines.append(f"- {action}")
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

    validation_script_name = f"execution_vm_validation_{args.vm_name}_{args.date_prefix.replace('-', '')}.sh"
    local_validation_script_path = local_output_dir / validation_script_name
    validation_script_object = f"bootstrap/{args.date_prefix}/foundation-phase3-validation/{validation_script_name}"

    script_text = render_validation_script(
        vm_name=args.vm_name,
        expected_static_ip=args.expected_static_ip,
        runtime_bootstrap_script_gs_uri=runtime_bootstrap_script_gs_uri,
    )
    write_unix_text(local_validation_script_path, script_text)

    creds = service_account.Credentials.from_service_account_file(str(credentials_json))
    client = storage.Client(project=args.project_id, credentials=creds)
    upload_file(client, args.control_bucket, validation_script_object, local_validation_script_path, "text/x-shellscript")

    iap_ssh_command = (
        f"gcloud compute ssh {args.vm_name} --project {args.project_id} --zone {args.zone} --tunnel-through-iap"
    )
    vm_validation_run_command = textwrap.dedent(
        f"""\
        TOKEN=$(curl -fsS -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
        OBJECT={shell_quote(validation_script_object)}
        ENCODED_OBJECT=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$OBJECT")
        curl -fsS -H "Authorization: Bearer $TOKEN" "https://storage.googleapis.com/storage/v1/b/{args.control_bucket}/o/$ENCODED_OBJECT?alt=media" -o /tmp/execution_vm_validation.sh
        bash /tmp/execution_vm_validation.sh
        """
    ).strip()

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "vm_name": args.vm_name,
        "zone": args.zone,
        "expected_static_ip": args.expected_static_ip,
        "local_validation_script_path": str(local_validation_script_path),
        "validation_script_gs_uri": f"gs://{args.control_bucket}/{validation_script_object}",
        "runtime_bootstrap_script_gs_uri": runtime_bootstrap_script_gs_uri,
        "iap_ssh_command": iap_ssh_command,
        "vm_validation_run_command": vm_validation_run_command,
        "required_checks": [
            "Observed VM external IP matches the reserved execution static IP.",
            "Runtime bootstrap script completes successfully.",
            "scripts/doctor.py --skip-connectivity --json completes and reports paper-only lock compatibility.",
            "python -m pytest -q exits 0.",
            "/var/lib/codexalpaca/validation/validation_status.json exists on the VM.",
        ],
        "next_actions": [
            "Connect to the VM through OS Login and IAP.",
            "Run the published validation script on the VM.",
            "Inspect /var/lib/codexalpaca/validation/validation_status.json and pytest.log on the VM.",
            "Only after this gate is clean should the next step move toward a trusted validation session.",
        ],
    }

    write_json(report_dir / "gcp_execution_vm_validation_status.json", payload)
    write_markdown(report_dir / "gcp_execution_vm_validation_status.md", payload)


if __name__ == "__main__":
    main()
