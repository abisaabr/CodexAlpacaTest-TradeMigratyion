from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CREDENTIALS_JSON = Path(r"C:\Users\rabisaab\Downloads\codexalpaca-1ebfbe0eaa7b.json")
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_REGION = "us-east1"
DEFAULT_BOOTSTRAP_BUCKET = "codexalpaca-transfer-922745393036"
CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a GCP foundation readiness registry for the codexalpaca project."
    )
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--bootstrap-bucket", default=DEFAULT_BOOTSTRAP_BUCKET)
    parser.add_argument("--region", default=DEFAULT_REGION)
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mint_access_token(credentials_json: Path) -> tuple[dict[str, Any], str | None]:
    info = read_json(credentials_json)
    summary = {
        "credentials_json": str(credentials_json),
        "project_id": info.get("project_id"),
        "client_email": info.get("client_email"),
        "credentials_present": credentials_json.exists(),
    }
    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_json),
            scopes=[CLOUD_PLATFORM_SCOPE],
        )
        credentials.refresh(Request())
        token = credentials.token
        expiry = credentials.expiry.isoformat() if credentials.expiry else None
        summary.update(
            {
                "token_mint_status": "ok",
                "token_expiry": expiry,
            }
        )
        return summary, token
    except Exception as exc:  # noqa: BLE001
        summary.update(
            {
                "token_mint_status": "failed",
                "token_error": str(exc),
            }
        )
        return summary, None


def api_get(url: str, token: str | None) -> dict[str, Any]:
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body else {}
            return {
                "success": True,
                "http_status": response.status,
                "payload": payload,
                "error_message": "",
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw_error_body": body}
        message = ""
        if isinstance(payload, dict):
            error_block = payload.get("error")
            if isinstance(error_block, dict):
                message = str(error_block.get("message") or "")
        return {
            "success": False,
            "http_status": exc.code,
            "payload": payload,
            "error_message": message or str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "http_status": None,
            "payload": {},
            "error_message": str(exc),
        }


def classify_check(response: dict[str, Any]) -> str:
    if response.get("success"):
        return "available"
    http_status = response.get("http_status")
    message = str(response.get("error_message") or "").lower()
    if http_status == 401:
        return "auth_failed"
    if http_status == 403:
        if "has not been used" in message or "is disabled" in message or "enable it" in message:
            return "api_disabled_or_not_enabled"
        return "permission_denied"
    if http_status == 404:
        return "not_found_or_unavailable"
    if http_status is None:
        return "network_or_client_error"
    return "error"


def response_summary(response: dict[str, Any]) -> str:
    if response.get("success"):
        return "API call succeeded."
    message = str(response.get("error_message") or "").strip()
    if message:
        return message
    return f"HTTP {response.get('http_status')}"


def build_checks(project_id: str, bootstrap_bucket: str, region: str, token: str | None) -> list[dict[str, Any]]:
    endpoint_specs = [
        {
            "capability_key": "project_metadata",
            "title": "Project metadata",
            "category": "control",
            "url": f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}",
            "success_requirement": "Read project metadata.",
        },
        {
            "capability_key": "cloud_storage_bucket_list",
            "title": "Cloud Storage bucket list",
            "category": "storage",
            "url": f"https://storage.googleapis.com/storage/v1/b?project={project_id}",
            "success_requirement": "List project buckets.",
        },
        {
            "capability_key": "bootstrap_bucket_access",
            "title": "Bootstrap transfer bucket access",
            "category": "storage",
            "url": f"https://storage.googleapis.com/storage/v1/b/{bootstrap_bucket}",
            "success_requirement": "Read bootstrap transfer bucket metadata.",
        },
        {
            "capability_key": "compute_engine",
            "title": "Compute Engine foundation access",
            "category": "execution",
            "url": f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks",
            "success_requirement": "Read or list Compute Engine network resources.",
        },
        {
            "capability_key": "secret_manager",
            "title": "Secret Manager access",
            "category": "secrets",
            "url": f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets",
            "success_requirement": "Read or list Secret Manager secrets.",
        },
        {
            "capability_key": "artifact_registry",
            "title": "Artifact Registry access",
            "category": "packaging",
            "url": f"https://artifactregistry.googleapis.com/v1/projects/{project_id}/locations/{region}/repositories",
            "success_requirement": "Read or list Artifact Registry repositories.",
        },
        {
            "capability_key": "cloud_batch",
            "title": "Cloud Batch access",
            "category": "research",
            "url": f"https://batch.googleapis.com/v1/projects/{project_id}/locations/{region}/jobs",
            "success_requirement": "Read or list Cloud Batch jobs.",
        },
        {
            "capability_key": "workflows",
            "title": "Workflows access",
            "category": "control",
            "url": f"https://workflows.googleapis.com/v1/projects/{project_id}/locations/{region}/workflows",
            "success_requirement": "Read or list Workflows resources.",
        },
        {
            "capability_key": "cloud_scheduler",
            "title": "Cloud Scheduler access",
            "category": "control",
            "url": f"https://cloudscheduler.googleapis.com/v1/projects/{project_id}/locations/{region}/jobs",
            "success_requirement": "Read or list Cloud Scheduler jobs.",
        },
    ]

    checks: list[dict[str, Any]] = []
    for spec in endpoint_specs:
        response = api_get(spec["url"], token)
        checks.append(
            {
                "capability_key": spec["capability_key"],
                "title": spec["title"],
                "category": spec["category"],
                "url": spec["url"],
                "success_requirement": spec["success_requirement"],
                "status": classify_check(response),
                "available": bool(response.get("success")),
                "http_status": response.get("http_status"),
                "summary": response_summary(response),
            }
        )
    return checks


def classify_foundation_status(checks: list[dict[str, Any]], token_summary: dict[str, Any]) -> str:
    if token_summary.get("token_mint_status") != "ok":
        return "credentials_blocked"

    available = {row["capability_key"] for row in checks if row.get("available")}
    storage_ok = {"cloud_storage_bucket_list", "bootstrap_bucket_access"}.issubset(available)
    core_foundation = {
        "compute_engine",
        "secret_manager",
        "artifact_registry",
        "cloud_batch",
        "workflows",
        "cloud_scheduler",
    }
    core_available = core_foundation.intersection(available)

    if storage_ok and not core_available:
        return "bootstrap_storage_only"
    if core_foundation.issubset(available):
        return "foundation_ready"
    if storage_ok and core_available:
        return "foundation_partial"
    return "foundation_blocked"


def build_next_actions(status: str, checks: list[dict[str, Any]], token_summary: dict[str, Any]) -> list[str]:
    blocked = [row for row in checks if not row.get("available")]
    blocked_keys = {row["capability_key"] for row in blocked}
    actions: list[str] = []

    if token_summary.get("token_mint_status") != "ok":
        actions.append("Fix the service-account key path or token-mint failure before trusting any cloud audit result.")
        return actions

    if status == "bootstrap_storage_only":
        actions.append("Treat the current service account as a storage/bootstrap principal, not as the foundation-provisioning identity.")
        actions.append("Use a higher-privilege human or bootstrap principal to create the VPC, execution VM, service accounts, Secret Manager resources, Artifact Registry, and orchestration services.")
    elif status == "foundation_partial":
        actions.append("Use the currently available capabilities for low-risk bootstrap work, but finish enabling the blocked foundation services before attempting cloud cutover.")
    elif status == "foundation_ready":
        actions.append("Proceed to Phase 0 foundation creation and then Phase 1 execution-plane cut-in.")
    else:
        actions.append("Do not attempt cloud cutover until the blocked cloud capabilities are resolved.")

    if "compute_engine" in blocked_keys:
        actions.append("Enable or grant access to Compute Engine so the execution VM and static IP can be provisioned.")
    if "secret_manager" in blocked_keys:
        actions.append("Enable or grant access to Secret Manager before moving Alpaca credentials out of workstation-local files.")
    if "artifact_registry" in blocked_keys:
        actions.append("Enable or grant access to Artifact Registry before containerizing research jobs for Batch.")
    if "cloud_batch" in blocked_keys:
        actions.append("Enable or grant access to Cloud Batch before migrating heavy research and backtests.")
    if "workflows" in blocked_keys or "cloud_scheduler" in blocked_keys:
        actions.append("Enable or grant access to Workflows and Cloud Scheduler before moving governed orchestration into GCP.")

    actions.append("Keep the bootstrap transfer bucket separate from the long-term data, artifacts, control, and backup buckets.")
    actions.append("Provision dedicated service accounts for execution, research, orchestration, and deployment rather than overloading the current bootstrap key.")
    return actions


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    project = dict(payload.get("project") or {})
    lines.append("# GCP Foundation Readiness")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Foundation status: `{payload['foundation_status']}`")
    lines.append(f"- Project ID: `{project.get('project_id')}`")
    lines.append(f"- Service account: `{project.get('client_email')}`")
    lines.append(f"- Token mint status: `{project.get('token_mint_status')}`")
    lines.append("")
    lines.append("## Available Capabilities")
    lines.append("")
    for item in list(payload.get("available_capabilities") or []):
        lines.append(f"- `{item}`")
    if not list(payload.get("available_capabilities") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Blocked Capabilities")
    lines.append("")
    for item in list(payload.get("blocked_capabilities") or []):
        lines.append(f"- `{item}`")
    if not list(payload.get("blocked_capabilities") or []):
        lines.append("- none")
    lines.append("")
    lines.append("## Capability Checks")
    lines.append("")
    for row in list(payload.get("checks") or []):
        lines.append(
            f"- `{row['capability_key']}`: status `{row['status']}`, http `{row['http_status']}`, summary `{row['summary']}`"
        )
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
    token_summary, token = mint_access_token(credentials_json)
    project_id = str(token_summary.get("project_id") or "")

    checks = build_checks(project_id, args.bootstrap_bucket, args.region, token) if project_id else []
    foundation_status = classify_foundation_status(checks, token_summary)
    available_capabilities = [row["capability_key"] for row in checks if row.get("available")]
    blocked_capabilities = [row["capability_key"] for row in checks if not row.get("available")]
    next_actions = build_next_actions(foundation_status, checks, token_summary)

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "foundation_status": foundation_status,
        "project": token_summary,
        "region": args.region,
        "bootstrap_bucket": args.bootstrap_bucket,
        "available_capabilities": available_capabilities,
        "blocked_capabilities": blocked_capabilities,
        "checks": checks,
        "next_actions": next_actions,
    }

    write_json(report_dir / "gcp_foundation_readiness.json", payload)
    write_markdown(report_dir / "gcp_foundation_readiness.md", payload)


if __name__ == "__main__":
    main()
