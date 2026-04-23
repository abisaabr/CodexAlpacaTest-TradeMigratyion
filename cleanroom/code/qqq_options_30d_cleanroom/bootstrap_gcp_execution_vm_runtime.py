from __future__ import annotations

import argparse
import hashlib
import json
import os
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import storage
from google.oauth2 import service_account


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CREDENTIALS_JSON = Path(r"C:\Users\rabisaab\Downloads\codexalpaca-7bcb9ac9a02d.json")
DEFAULT_RUNTIME_REPO = Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo")
DEFAULT_ENV_PATH = DEFAULT_RUNTIME_REPO / ".env"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_LOCAL_OUTPUT_DIR = REPO_ROOT / "output" / "gcp_execution_vm_runtime"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_CONTROL_BUCKET = "codexalpaca-control-us"
DEFAULT_BACKUP_BUCKET = "codexalpaca-backups-us"
DEFAULT_DATE_PREFIX = "2026-04-23"
DEFAULT_VM_NAME = "vm-execution-paper-01"
DEFAULT_EXECUTION_REPO_DIR = "/opt/codexalpaca/codexalpaca_repo"

SECRET_SPECS = [
    ("ALPACA_API_KEY", "execution-alpaca-paper-api-key", True),
    ("ALPACA_SECRET_KEY", "execution-alpaca-paper-secret-key", True),
    ("DISCORD_WEBHOOK_URL", "notification-discord-webhook-url", False),
    ("NTFY_ACCESS_TOKEN", "notification-ntfy-access-token", False),
    ("EMAIL_PASSWORD", "notification-email-password", False),
]

EXCLUDED_TOP_LEVEL = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "reports",
    "data",
    "repo_archives",
    "__pycache__",
}
EXCLUDED_NAMES = {
    ".env",
    "__pycache__",
}
UNIX_NORMALIZED_SUFFIXES = {
    ".sh",
    ".bash",
}
NON_SECRET_ENV_EXCLUDE = {name for name, _, _ in SECRET_SPECS} | {
    "APCA_API_KEY_ID",
    "APCA_API_SECRET_KEY",
    "MULTI_TICKER_MACHINE_LABEL",
    "MULTI_TICKER_OWNERSHIP_ENABLED",
    "MULTI_TICKER_OWNERSHIP_LEASE_PATH",
    "MULTI_TICKER_OWNERSHIP_TTL_SECONDS",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare the execution VM runtime bootstrap bundle for codexalpaca.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--runtime-repo-root", default=str(DEFAULT_RUNTIME_REPO))
    parser.add_argument("--env-path", default=str(DEFAULT_ENV_PATH))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--control-bucket", default=DEFAULT_CONTROL_BUCKET)
    parser.add_argument("--backup-bucket", default=DEFAULT_BACKUP_BUCKET)
    parser.add_argument("--date-prefix", default=DEFAULT_DATE_PREFIX)
    parser.add_argument("--vm-name", default=DEFAULT_VM_NAME)
    parser.add_argument("--execution-repo-dir", default=DEFAULT_EXECUTION_REPO_DIR)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--local-output-dir", default=str(DEFAULT_LOCAL_OUTPUT_DIR))
    return parser


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def secret_value(env: dict[str, str], key: str) -> str:
    return str(env.get(key) or "").strip()


def should_include(path: Path, repo_root: Path) -> bool:
    relative = path.relative_to(repo_root)
    if not relative.parts:
        return False
    if relative.parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    if any(part in EXCLUDED_NAMES for part in relative.parts):
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    return True


def build_source_bundle(repo_root: Path, output_zip: Path) -> tuple[int, str]:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    file_count = 0
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(repo_root.rglob("*")):
            if not path.is_file():
                continue
            if not should_include(path, repo_root):
                continue
            relative = path.relative_to(repo_root)
            data = path.read_bytes()
            archive_data = data
            if path.suffix.lower() in UNIX_NORMALIZED_SUFFIXES:
                archive_data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            zf.writestr(relative.as_posix(), archive_data)
            hasher.update(relative.as_posix().encode("utf-8"))
            hasher.update(b"\0")
            hasher.update(archive_data)
            file_count += 1
    return file_count, hasher.hexdigest()


def rendered_non_secret_env(env: dict[str, str], vm_name: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for key in sorted(env.keys()):
        if key in NON_SECRET_ENV_EXCLUDE:
            continue
        value = str(env[key]).strip()
        if not value:
            continue
        results.append((key, value))
    results.append(("MULTI_TICKER_MACHINE_LABEL", vm_name))
    results.append(("MULTI_TICKER_OWNERSHIP_ENABLED", "false"))
    return results


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def render_bootstrap_script(
    *,
    backup_bucket: str,
    bundle_object: str,
    control_bucket: str,
    status_object: str,
    execution_repo_dir: str,
    vm_name: str,
    non_secret_env: list[tuple[str, str]],
    secret_specs: list[tuple[str, str, bool]],
) -> str:
    env_lines = "\n".join(
        f"printf '%s=%s\\n' {shell_quote(key)} {shell_quote(value)} >> \"$ENV_PATH\""
        for key, value in non_secret_env
    )

    secret_block_lines: list[str] = []
    for env_key, secret_id, required in secret_specs:
        required_flag = "true" if required else "false"
        secret_block_lines.append(
            f'write_secret_env "{env_key}" "{secret_id}" "{required_flag}"'
        )
    secret_block = "\n".join(secret_block_lines)

    script = f"""#!/usr/bin/env bash
set -euo pipefail

VM_NAME={shell_quote(vm_name)}
EXECUTION_REPO_DIR={shell_quote(execution_repo_dir)}
BUNDLE_BUCKET={shell_quote(backup_bucket)}
BUNDLE_OBJECT={shell_quote(bundle_object)}
CONTROL_BUCKET={shell_quote(control_bucket)}
STATUS_OBJECT={shell_quote(status_object)}
WORK_DIR="/var/lib/codexalpaca/runtime-bootstrap"
STAGING_DIR="$WORK_DIR/staging"
ARCHIVE_PATH="$WORK_DIR/runtime_bundle.zip"
STATUS_PATH="$WORK_DIR/runtime_bootstrap_status.json"
ENV_PATH="$EXECUTION_REPO_DIR/.env"
export EXECUTION_REPO_DIR
export STAGING_DIR
export ARCHIVE_PATH

mkdir -p "$WORK_DIR" "$STAGING_DIR" "$(dirname "$EXECUTION_REPO_DIR")"

metadata_token() {{
  curl -fsS -H "Metadata-Flavor: Google" \\
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \\
    | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])"
}}

TOKEN="$(metadata_token)"

gcs_download() {{
  local bucket="$1"
  local object="$2"
  local dest="$3"
  local encoded_object
  encoded_object="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=\"\"))' "$object")"
  curl -fsS -H "Authorization: Bearer $TOKEN" \\
    "https://storage.googleapis.com/storage/v1/b/${{bucket}}/o/${{encoded_object}}?alt=media" \\
    -o "$dest"
}}

secret_access() {{
  local secret_id="$1"
  curl -fsS -H "Authorization: Bearer $TOKEN" \\
    "https://secretmanager.googleapis.com/v1/projects/codexalpaca/secrets/${{secret_id}}/versions/latest:access" \\
    | python3 -c "import sys, json, base64; print(base64.b64decode(json.load(sys.stdin)['payload']['data']).decode('utf-8'))"
}}

write_secret_env() {{
  local env_key="$1"
  local secret_id="$2"
  local required="$3"
  local value=""
  if value="$(secret_access "$secret_id" 2>/dev/null)"; then
    printf '%s=%s\\n' "$env_key" "$value" >> "$ENV_PATH"
    return 0
  fi
  if [[ "$required" == "true" ]]; then
    echo "Required secret $secret_id could not be accessed" >&2
    exit 1
  fi
}}

python3_ready() {{
  python3 - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}}

ensure_supported_python() {{
  if python3_ready; then
    return 0
  fi

  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  if ! apt-get install -y python3.11 python3.11-venv; then
    apt-get install -y software-properties-common
    add-apt-repository ppa:deadsnakes/ppa -y
    apt-get update
    apt-get install -y python3.11 python3.11-venv
  fi
  ln -sf /usr/bin/python3.11 /usr/local/bin/python3
}}

gcs_download "$BUNDLE_BUCKET" "$BUNDLE_OBJECT" "$ARCHIVE_PATH"
rm -rf "$STAGING_DIR" "$EXECUTION_REPO_DIR"
mkdir -p "$STAGING_DIR"
python3 - <<'PY'
import os
import zipfile
from pathlib import Path

archive_path = Path(os.environ["ARCHIVE_PATH"])
staging_dir = Path(os.environ["STAGING_DIR"])
with zipfile.ZipFile(archive_path, "r") as zf:
    zf.extractall(staging_dir)
PY
mv "$STAGING_DIR" "$EXECUTION_REPO_DIR"

ensure_supported_python

cat /dev/null > "$ENV_PATH"
{env_lines}
{secret_block}

cd "$EXECUTION_REPO_DIR"
bash ./scripts/bootstrap_linux.sh

python3 - <<'PY'
from pathlib import Path
import json
from datetime import datetime
status = {{
    "generated_at": datetime.now().astimezone().isoformat(),
    "vm_name": {json.dumps(vm_name)},
    "repo_dir": {json.dumps(execution_repo_dir)},
    "validation_only": True,
    "env_path": str(Path({json.dumps(execution_repo_dir)}) / ".env"),
    "bootstrap_complete": True,
}}
Path({json.dumps(str(Path("/var/lib/codexalpaca/runtime-bootstrap/runtime_bootstrap_status.json")))}).write_text(json.dumps(status, indent=2), encoding="utf-8")
PY

echo "validation bootstrap complete on $VM_NAME"
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
    lines.append("# GCP Execution VM Runtime Bootstrap Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Runtime repo root: `{payload['runtime_repo_root']}`")
    lines.append("")
    lines.append("## Bundle")
    lines.append("")
    lines.append(f"- Local bundle: `{payload['local_bundle_path']}`")
    lines.append(f"- Backup bucket URI: `{payload['bundle_gs_uri']}`")
    lines.append(f"- Included files: `{payload['bundle_file_count']}`")
    lines.append(f"- Bundle SHA256: `{payload['bundle_sha256']}`")
    lines.append("")
    lines.append("## Bootstrap Script")
    lines.append("")
    lines.append(f"- Local script: `{payload['local_bootstrap_script_path']}`")
    lines.append(f"- Control bucket URI: `{payload['bootstrap_script_gs_uri']}`")
    lines.append("")
    lines.append("## Validation Config")
    lines.append("")
    for row in list(payload.get("non_secret_env_keys") or []):
        lines.append(f"- `{row}`")
    if not list(payload.get("non_secret_env_keys") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Secret Mappings")
    lines.append("")
    for row in list(payload.get("secret_mappings") or []):
        req = "required" if row.get("required") else "optional"
        seeded = "present_locally" if row.get("present_locally") else "pending_locally"
        lines.append(f"- `{row['env_key']}` -> `{row['secret_id']}`: `{req}`, `{seeded}`")
    lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for action in list(payload.get("next_actions") or []):
        lines.append(f"- {action}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    credentials_json = Path(args.credentials_json).resolve()
    runtime_repo_root = Path(args.runtime_repo_root).resolve()
    env_path = Path(args.env_path).resolve()
    report_dir = Path(args.report_dir).resolve()
    local_output_dir = Path(args.local_output_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    local_output_dir.mkdir(parents=True, exist_ok=True)

    env = parse_env(env_path)
    non_secret_env = rendered_non_secret_env(env, args.vm_name)

    bundle_name = f"codexalpaca_repo_source_{args.vm_name}_{args.date_prefix.replace('-', '')}.zip"
    bundle_local_path = local_output_dir / bundle_name
    bundle_file_count, bundle_sha256 = build_source_bundle(runtime_repo_root, bundle_local_path)

    bundle_object = f"bootstrap/{args.date_prefix}/execution-vm/{bundle_name}"
    bootstrap_script_name = f"execution_vm_runtime_bootstrap_{args.vm_name}_{args.date_prefix.replace('-', '')}.sh"
    bootstrap_script_local_path = local_output_dir / bootstrap_script_name
    status_object = f"bootstrap/{args.date_prefix}/execution-vm/runtime-bootstrap-status.json"
    control_prefix = f"bootstrap/{args.date_prefix}/foundation-phase2-runtime"
    bootstrap_script_object = f"{control_prefix}/{bootstrap_script_name}"

    secret_mappings = [
        {
            "env_key": env_key,
            "secret_id": secret_id,
            "required": required,
            "present_locally": bool(secret_value(env, env_key)),
        }
        for env_key, secret_id, required in SECRET_SPECS
    ]

    script_text = render_bootstrap_script(
        backup_bucket=args.backup_bucket,
        bundle_object=bundle_object,
        control_bucket=args.control_bucket,
        status_object=status_object,
        execution_repo_dir=args.execution_repo_dir,
        vm_name=args.vm_name,
        non_secret_env=non_secret_env,
        secret_specs=SECRET_SPECS,
    )
    write_unix_text(bootstrap_script_local_path, script_text)

    creds = service_account.Credentials.from_service_account_file(str(credentials_json))
    client = storage.Client(project=args.project_id, credentials=creds)
    upload_file(client, args.backup_bucket, bundle_object, bundle_local_path, "application/zip")
    upload_file(client, args.control_bucket, bootstrap_script_object, bootstrap_script_local_path, "text/x-shellscript")

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "vm_name": args.vm_name,
        "runtime_repo_root": str(runtime_repo_root),
        "local_bundle_path": str(bundle_local_path),
        "bundle_gs_uri": f"gs://{args.backup_bucket}/{bundle_object}",
        "bundle_file_count": bundle_file_count,
        "bundle_sha256": bundle_sha256,
        "local_bootstrap_script_path": str(bootstrap_script_local_path),
        "bootstrap_script_gs_uri": f"gs://{args.control_bucket}/{bootstrap_script_object}",
        "non_secret_env_keys": [key for key, _ in non_secret_env],
        "secret_mappings": secret_mappings,
        "next_actions": [
            "Use OS Login and IAP to connect to the validation VM before running the bootstrap script.",
            "Run the bootstrap script on the VM in validation-only mode and confirm scripts/bootstrap_linux.sh completes cleanly.",
            "Run doctor and test validation on the VM before attempting any paper-runner session.",
            "Keep ownership leasing disabled on the VM until promotion to canonical execution is intentional.",
        ],
    }

    write_json(report_dir / "gcp_execution_vm_runtime_bootstrap_status.json", payload)
    write_markdown(report_dir / "gcp_execution_vm_runtime_bootstrap_status.md", payload)


if __name__ == "__main__":
    main()
