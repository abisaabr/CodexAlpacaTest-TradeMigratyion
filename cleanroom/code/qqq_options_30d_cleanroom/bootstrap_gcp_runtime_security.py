from __future__ import annotations

import argparse
import base64
import json
import time
import urllib.error
import urllib.parse
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
DEFAULT_ENV_PATH = Path(r"C:\Users\rabisaab\Downloads\codexalpaca_repo\.env")
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_REGION = "us-east1"

SECRET_SPECS = [
    {
        "secret_id": "execution-alpaca-paper-api-key",
        "env_keys": ["ALPACA_API_KEY", "APCA_API_KEY_ID"],
        "required": True,
        "accessors": ["sa-execution-runner@codexalpaca.iam.gserviceaccount.com"],
    },
    {
        "secret_id": "execution-alpaca-paper-secret-key",
        "env_keys": ["ALPACA_SECRET_KEY", "APCA_API_SECRET_KEY"],
        "required": True,
        "accessors": ["sa-execution-runner@codexalpaca.iam.gserviceaccount.com"],
    },
    {
        "secret_id": "notification-discord-webhook-url",
        "env_keys": ["DISCORD_WEBHOOK_URL"],
        "required": False,
        "accessors": ["sa-execution-runner@codexalpaca.iam.gserviceaccount.com"],
    },
    {
        "secret_id": "notification-ntfy-access-token",
        "env_keys": ["NTFY_ACCESS_TOKEN"],
        "required": False,
        "accessors": ["sa-execution-runner@codexalpaca.iam.gserviceaccount.com"],
    },
    {
        "secret_id": "notification-email-password",
        "env_keys": ["EMAIL_PASSWORD"],
        "required": False,
        "accessors": ["sa-execution-runner@codexalpaca.iam.gserviceaccount.com"],
    },
]

PROJECT_ROLE_BINDINGS = [
    ("roles/logging.logWriter", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
    ("roles/monitoring.metricWriter", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
    ("roles/logging.logWriter", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
    ("roles/monitoring.metricWriter", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
    ("roles/logging.logWriter", "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com"),
    ("roles/monitoring.metricWriter", "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com"),
    ("roles/artifactregistry.writer", "serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com"),
    ("roles/artifactregistry.reader", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
    ("roles/artifactregistry.reader", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
]

SECRET_ACCESSOR_ROLE = "roles/secretmanager.secretAccessor"

BUCKET_ROLE_BINDINGS = {
    "codexalpaca-data-us": [
        ("roles/storage.objectViewer", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
    ],
    "codexalpaca-artifacts-us": [
        ("roles/storage.objectAdmin", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
        ("roles/storage.objectAdmin", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
        ("roles/storage.objectViewer", "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com"),
    ],
    "codexalpaca-control-us": [
        ("roles/storage.objectAdmin", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
        ("roles/storage.objectAdmin", "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com"),
        ("roles/storage.objectViewer", "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com"),
    ],
    "codexalpaca-backups-us": [
        ("roles/storage.objectAdmin", "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com"),
        ("roles/storage.objectViewer", "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com"),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap Secret Manager and runtime IAM for codexalpaca.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--env-path", default=str(DEFAULT_ENV_PATH))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--region", default=DEFAULT_REGION)
    return parser


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
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw_error_body": body}
        return exc.code, parsed


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def secret_value(env: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        value = str(env.get(key) or "").strip()
        if value:
            return value
    return ""


def ensure_secret(project_id: str, secret_id: str, token: str) -> str:
    get_url = f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets/{secret_id}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return "existing"
    if status != 404:
        raise RuntimeError(f"Unable to inspect secret `{secret_id}`: {status} {payload}")
    create_url = f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets?secretId={urllib.parse.quote(secret_id)}"
    body = {"replication": {"automatic": {}}}
    status, payload = request_json("POST", create_url, token, body)
    if status in {200, 201}:
        return "created"
    raise RuntimeError(f"Unable to create secret `{secret_id}`: {status} {payload}")


def list_secret_versions(project_id: str, secret_id: str, token: str) -> list[dict[str, Any]]:
    url = f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets/{secret_id}/versions"
    status, payload = request_json("GET", url, token)
    if status == 404:
        return []
    if status >= 400:
        raise RuntimeError(f"Unable to list versions for `{secret_id}`: {status} {payload}")
    return [dict(row) for row in list(payload.get("versions") or []) if isinstance(row, dict)]


def add_secret_version(project_id: str, secret_id: str, value: str, token: str) -> str:
    url = f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets/{secret_id}:addVersion"
    body = {"payload": {"data": base64.b64encode(value.encode("utf-8")).decode("ascii")}}
    status, payload = request_json("POST", url, token, body)
    if status in {200, 201}:
        return str(payload.get("name") or "")
    raise RuntimeError(f"Unable to add secret version for `{secret_id}`: {status} {payload}")


def get_policy(url: str, token: str) -> dict[str, Any]:
    status, payload = request_json("POST", f"{url}:getIamPolicy", token, {})
    if status >= 400:
        raise RuntimeError(f"Unable to get IAM policy for `{url}`: {status} {payload}")
    payload.setdefault("bindings", [])
    return payload


def set_policy(url: str, token: str, policy: dict[str, Any]) -> None:
    status, payload = request_json("POST", f"{url}:setIamPolicy", token, {"policy": policy})
    if status >= 400:
        raise RuntimeError(f"Unable to set IAM policy for `{url}`: {status} {payload}")


def ensure_binding(policy: dict[str, Any], role: str, member: str) -> bool:
    bindings = list(policy.get("bindings") or [])
    for binding in bindings:
        if binding.get("role") != role:
            continue
        members = list(binding.get("members") or [])
        if member in members:
            return False
        members.append(member)
        binding["members"] = sorted(set(members))
        policy["bindings"] = bindings
        return True
    bindings.append({"role": role, "members": [member]})
    policy["bindings"] = bindings
    return True


def ensure_secret_accessor(project_id: str, secret_id: str, member: str, token: str) -> str:
    resource = f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets/{secret_id}"
    policy = get_policy(resource, token)
    changed = ensure_binding(policy, SECRET_ACCESSOR_ROLE, member)
    if changed:
        set_policy(resource, token, policy)
        return "bound"
    return "existing"


def should_fallback_secret_accessor(exc: RuntimeError) -> bool:
    text = str(exc)
    return "secretmanager.googleapis.com" in text and ":getIamPolicy" in text and "404" in text


def get_project_iam_policy(project_id: str, token: str) -> dict[str, Any]:
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:getIamPolicy"
    status, payload = request_json("POST", url, token, {})
    if status >= 400:
        raise RuntimeError(f"Unable to get project IAM policy: {status} {payload}")
    payload.setdefault("bindings", [])
    return payload


def set_project_iam_policy(project_id: str, token: str, policy: dict[str, Any]) -> None:
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:setIamPolicy"
    status, payload = request_json("POST", url, token, {"policy": policy})
    if status >= 400:
        raise RuntimeError(f"Unable to set project IAM policy: {status} {payload}")


def ensure_project_bindings(project_id: str, bindings: list[tuple[str, str]], token: str) -> list[dict[str, str]]:
    policy = get_project_iam_policy(project_id, token)
    results: list[dict[str, str]] = []
    changed_any = False
    for role, member in bindings:
        changed = ensure_binding(policy, role, member)
        results.append({"role": role, "member": member, "action": "bound" if changed else "existing"})
        changed_any = changed_any or changed
    if changed_any:
        set_project_iam_policy(project_id, token, policy)
    return results


def ensure_bucket_bindings(credentials_json: Path, bindings: dict[str, list[tuple[str, str]]], project_id: str) -> list[dict[str, str]]:
    client = storage.Client.from_service_account_json(str(credentials_json), project=project_id)
    results: list[dict[str, str]] = []
    for bucket_name, bucket_bindings in bindings.items():
        bucket = client.bucket(bucket_name)
        policy = bucket.get_iam_policy(requested_policy_version=3)
        changed_any = False
        for role, member in bucket_bindings:
            members = list(policy.get(role, []))
            if member in members:
                results.append({"bucket": bucket_name, "role": role, "member": member, "action": "existing"})
                continue
            members.append(member)
            policy[role] = sorted(set(members))
            results.append({"bucket": bucket_name, "role": role, "member": member, "action": "bound"})
            changed_any = True
        if changed_any:
            bucket.set_iam_policy(policy)
    return results


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Runtime Security Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Bootstrap service account: `{payload['bootstrap_service_account']}`")
    lines.append("")
    lines.append("## Secrets")
    lines.append("")
    for row in list(payload.get("secret_results") or []):
        lines.append(
            f"- `{row['secret_id']}`: secret `{row['secret_action']}`, seeded `{str(bool(row['seeded'])).lower()}`, version action `{row['version_action']}`"
        )
    if not list(payload.get("secret_results") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Secret Access Bindings")
    lines.append("")
    for row in list(payload.get("secret_access_results") or []):
        scope = str(row.get("scope") or "secret")
        lines.append(f"- `{row['secret_id']}` -> `{row['member']}`: `{row['action']}` at `{scope}` scope")
    if not list(payload.get("secret_access_results") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Project IAM")
    lines.append("")
    for row in list(payload.get("project_iam_results") or []):
        lines.append(f"- `{row['role']}` -> `{row['member']}`: `{row['action']}`")
    if not list(payload.get("project_iam_results") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Bucket IAM")
    lines.append("")
    for row in list(payload.get("bucket_iam_results") or []):
        lines.append(f"- `{row['bucket']}` `{row['role']}` -> `{row['member']}`: `{row['action']}`")
    if not list(payload.get("bucket_iam_results") or []):
        lines.append("- none")
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
    token = mint_token(credentials_json)
    env = parse_env(Path(args.env_path).resolve())

    secret_results: list[dict[str, Any]] = []
    secret_access_results: list[dict[str, str]] = []
    secret_accessor_fallback_bindings: set[tuple[str, str]] = set()
    for spec in SECRET_SPECS:
        secret_id = str(spec["secret_id"])
        value = secret_value(env, list(spec["env_keys"]))
        secret_action = ensure_secret(args.project_id, secret_id, token)
        versions = list_secret_versions(args.project_id, secret_id, token)
        if value and not versions:
            add_secret_version(args.project_id, secret_id, value, token)
            version_action = "seeded_initial_version"
        elif value:
            version_action = "existing_version_present"
        else:
            version_action = "pending_value"
        secret_results.append(
            {
                "secret_id": secret_id,
                "required": bool(spec["required"]),
                "secret_action": secret_action,
                "seeded": bool(value),
                "version_action": version_action,
            }
        )
        for accessor in list(spec["accessors"]):
            member = f"serviceAccount:{accessor}"
            try:
                action = ensure_secret_accessor(args.project_id, secret_id, member, token)
                secret_access_results.append(
                    {"secret_id": secret_id, "member": member, "action": action, "scope": "secret"}
                )
            except RuntimeError as exc:
                if not should_fallback_secret_accessor(exc):
                    raise
                secret_accessor_fallback_bindings.add((SECRET_ACCESSOR_ROLE, member))
                secret_access_results.append(
                    {
                        "secret_id": secret_id,
                        "member": member,
                        "action": "queued_project_scope_fallback",
                        "scope": "project",
                    }
                )

    project_role_bindings = list(PROJECT_ROLE_BINDINGS)
    for role, member in sorted(secret_accessor_fallback_bindings):
        project_role_bindings.append((role, member))

    project_iam_results = ensure_project_bindings(args.project_id, project_role_bindings, token)
    bucket_iam_results = ensure_bucket_bindings(credentials_json, BUCKET_ROLE_BINDINGS, args.project_id)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "bootstrap_service_account": read_project_email(credentials_json),
        "secret_results": secret_results,
        "secret_access_results": secret_access_results,
        "project_iam_results": project_iam_results,
        "bucket_iam_results": bucket_iam_results,
        "next_actions": [
            "Create the reserved execution static IP and the validation-only execution VM next.",
            "Teach the execution VM bootstrap to pull Secret Manager values into its runtime environment.",
            "Add Workflow and Batch-specific service-account impersonation bindings when the orchestrator resources are created.",
            "Sync the runtime security status packet into the control bucket and GitHub so the other machine can follow the exact cloud state.",
        ],
    }

    write_json(report_dir / "gcp_runtime_security_status.json", payload)
    write_markdown(report_dir / "gcp_runtime_security_status.md", payload)


def read_project_email(credentials_json: Path) -> str:
    payload = json.loads(credentials_json.read_text(encoding="utf-8"))
    return str(payload.get("client_email") or "")


if __name__ == "__main__":
    main()
