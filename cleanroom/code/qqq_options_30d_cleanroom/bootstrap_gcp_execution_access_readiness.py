from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CREDENTIALS_JSON = Path(r"C:\Users\rabisaab\Downloads\codexalpaca-7bcb9ac9a02d.json")
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_ZONE = "us-east1-b"
DEFAULT_INSTANCE_NAME = "vm-execution-paper-01"
DEFAULT_FIREWALL_RULE = "fw-allow-iap-ssh-execution"
DEFAULT_SERVICE_ACCOUNT = "sa-execution-runner@codexalpaca.iam.gserviceaccount.com"

REQUIRED_SERVICES = [
    "iap.googleapis.com",
    "oslogin.googleapis.com",
]

PROJECT_ACCESS_ROLE_BINDINGS = [
    "roles/iap.tunnelResourceAccessor",
    "roles/compute.osAdminLogin",
    "roles/compute.viewer",
]
SERVICE_ACCOUNT_ACCESS_ROLE = "roles/iam.serviceAccountUser"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare GCP execution access readiness for OS Login and IAP.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--instance-name", default=DEFAULT_INSTANCE_NAME)
    parser.add_argument("--firewall-rule-name", default=DEFAULT_FIREWALL_RULE)
    parser.add_argument("--execution-service-account-email", default=DEFAULT_SERVICE_ACCOUNT)
    parser.add_argument("--operator-principal", default="")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
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
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"raw_error_body": body}
        return exc.code, parsed


def wait_for_operation(operation_name: str, token: str) -> dict[str, Any]:
    url = f"https://serviceusage.googleapis.com/v1/{operation_name}"
    for _ in range(180):
        status, payload = request_json("GET", url, token)
        if status >= 400:
            raise RuntimeError(f"Service Usage operation poll failed: {status} {payload}")
        if payload.get("done") is True:
            if payload.get("error"):
                raise RuntimeError(f"Service Usage operation failed: {payload['error']}")
            return payload
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for Service Usage operation `{operation_name}`")


def read_project(credentials_json: Path, token: str, project_id: str) -> dict[str, Any]:
    status, payload = request_json("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}", token)
    if status >= 400:
        raise RuntimeError(f"Unable to read project metadata: {status} {payload}")
    return payload


def ensure_service_enabled(project_number: str, service_name: str, token: str) -> dict[str, str]:
    get_url = f"https://serviceusage.googleapis.com/v1/projects/{project_number}/services/{service_name}"
    status, payload = request_json("GET", get_url, token)
    if status >= 400:
        raise RuntimeError(f"Unable to inspect service `{service_name}`: {status} {payload}")
    state = str(payload.get("state") or "")
    if state == "ENABLED":
        return {"service": service_name, "action": "existing"}
    enable_url = f"https://serviceusage.googleapis.com/v1/projects/{project_number}/services/{service_name}:enable"
    status, payload = request_json("POST", enable_url, token, {})
    if status >= 400:
        raise RuntimeError(f"Unable to enable service `{service_name}`: {status} {payload}")
    operation_name = str(payload.get("name") or "")
    wait_for_operation(operation_name, token)
    return {"service": service_name, "action": "enabled"}


def read_instance(project_id: str, zone: str, instance_name: str, token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}"
    status, payload = request_json("GET", url, token)
    if status >= 400:
        raise RuntimeError(f"Unable to read instance `{instance_name}`: {status} {payload}")
    return payload


def read_firewall_rule(project_id: str, firewall_rule_name: str, token: str) -> dict[str, Any]:
    url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/firewalls/{firewall_rule_name}"
    status, payload = request_json("GET", url, token)
    if status >= 400:
        raise RuntimeError(f"Unable to read firewall rule `{firewall_rule_name}`: {status} {payload}")
    return payload


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


def ensure_project_bindings(project_id: str, member: str, token: str) -> list[dict[str, str]]:
    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    policy = get_policy(url, token)
    results: list[dict[str, str]] = []
    changed = False
    for role in PROJECT_ACCESS_ROLE_BINDINGS:
        did_change = ensure_binding(policy, role, member)
        results.append({"scope": "project", "role": role, "member": member, "action": "bound" if did_change else "existing"})
        changed = changed or did_change
    if changed:
        set_policy(url, token, policy)
    return results


def ensure_service_account_binding(project_id: str, service_account_email: str, member: str, token: str) -> dict[str, str]:
    encoded_email = urllib.parse.quote(service_account_email, safe="")
    url = f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts/{encoded_email}"
    policy = get_policy(url, token)
    changed = ensure_binding(policy, SERVICE_ACCOUNT_ACCESS_ROLE, member)
    if changed:
        set_policy(url, token, policy)
    return {
        "scope": "service_account",
        "role": SERVICE_ACCOUNT_ACCESS_ROLE,
        "member": member,
        "resource": service_account_email,
        "action": "bound" if changed else "existing",
    }


def read_project_email(credentials_json: Path) -> str:
    payload = json.loads(credentials_json.read_text(encoding="utf-8"))
    return str(payload.get("client_email") or "")


def metadata_map(instance_payload: dict[str, Any]) -> dict[str, str]:
    items = list(((instance_payload.get("metadata") or {}).get("items")) or [])
    mapping: dict[str, str] = {}
    for row in items:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "")
        if not key:
            continue
        mapping[key] = str(row.get("value") or "")
    return mapping


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Execution Access Readiness Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- VM: `{payload['instance_name']}`")
    lines.append(f"- Zone: `{payload['zone']}`")
    lines.append(f"- Bootstrap service account: `{payload['bootstrap_service_account']}`")
    lines.append(f"- Access readiness: `{payload['access_readiness']}`")
    lines.append("")
    lines.append("## API Readiness")
    lines.append("")
    for row in list(payload.get("service_results") or []):
        lines.append(f"- `{row['service']}`: `{row['action']}`")
    lines.append("")
    lines.append("## VM / Firewall Checks")
    lines.append("")
    for row in list(payload.get("vm_checks") or []):
        lines.append(f"- `{row['check']}`: `{row['status']}`")
    lines.append("")
    if payload.get("operator_principal"):
        lines.append("## Operator IAM")
        lines.append("")
        for row in list(payload.get("iam_results") or []):
            resource = f" on `{row['resource']}`" if row.get("resource") else ""
            lines.append(f"- `{row['scope']}` `{row['role']}` -> `{row['member']}`: `{row['action']}`{resource}")
        lines.append("")
    else:
        lines.append("## Operator IAM")
        lines.append("")
        lines.append("- operator principal not provided; IAM access grant remains pending")
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

    project = read_project(credentials_json, token, args.project_id)
    project_number = str(project.get("projectNumber") or "")

    service_results = [ensure_service_enabled(project_number, service, token) for service in REQUIRED_SERVICES]

    instance_payload = read_instance(args.project_id, args.zone, args.instance_name, token)
    firewall_payload = read_firewall_rule(args.project_id, args.firewall_rule_name, token)
    metadata = metadata_map(instance_payload)
    tags = set((instance_payload.get("tags") or {}).get("items") or [])
    source_ranges = set(firewall_payload.get("sourceRanges") or [])

    vm_checks = [
        {
            "check": "enable_oslogin",
            "status": "ok" if metadata.get("enable-oslogin", "").upper() == "TRUE" else "missing",
        },
        {
            "check": "block_project_ssh_keys",
            "status": "ok" if metadata.get("block-project-ssh-keys", "").upper() == "TRUE" else "missing",
        },
        {
            "check": "iap_ssh_tag",
            "status": "ok" if "iap-ssh" in tags else "missing",
        },
        {
            "check": "iap_firewall_source_range",
            "status": "ok" if "35.235.240.0/20" in source_ranges else "missing",
        },
    ]

    iam_results: list[dict[str, str]] = []
    operator_principal = str(args.operator_principal or "").strip()
    if operator_principal:
        iam_results.extend(ensure_project_bindings(args.project_id, operator_principal, token))
        iam_results.append(
            ensure_service_account_binding(
                args.project_id,
                args.execution_service_account_email,
                operator_principal,
                token,
            )
        )

    access_readiness = "ready_for_grant" if not operator_principal else "ready_for_operator_validation"
    if any(row["status"] != "ok" for row in vm_checks):
        access_readiness = "blocked_vm_access_prereq"

    next_actions = []
    if not operator_principal:
        next_actions.append(
            "Provide the Google principal that should operate the VM so OS Login, IAP tunnel access, and serviceAccountUser can be granted explicitly."
        )
    else:
        next_actions.append("Use the new operator principal to connect through gcloud compute ssh with --tunnel-through-iap.")
    next_actions.extend(
        [
            "Keep inbound SSH restricted to IAP and do not open port 22 to the internet.",
            "Use the validation gate packet next, not ad hoc SSH commands, before trusting the VM for execution.",
        ]
    )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "project_number": project_number,
        "instance_name": args.instance_name,
        "zone": args.zone,
        "bootstrap_service_account": read_project_email(credentials_json),
        "operator_principal": operator_principal,
        "service_results": service_results,
        "vm_checks": vm_checks,
        "iam_results": iam_results,
        "access_readiness": access_readiness,
        "next_actions": next_actions,
    }

    write_json(report_dir / "gcp_execution_access_readiness_status.json", payload)
    write_markdown(report_dir / "gcp_execution_access_readiness_status.md", payload)


if __name__ == "__main__":
    main()
