from __future__ import annotations

import argparse
import json
import textwrap
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
DEFAULT_REGION = "us-east1"
DEFAULT_ZONE = "us-east1-b"
DEFAULT_NETWORK = "vpc-codex-core"
DEFAULT_SUBNET = "subnet-us-east1-core"
DEFAULT_ADDRESS_NAME = "ip-execution-paper-us-east1"
DEFAULT_INSTANCE_NAME = "vm-execution-paper-01"
DEFAULT_MACHINE_TYPE = "e2-standard-4"
DEFAULT_BOOT_DISK_SIZE_GB = 100
DEFAULT_SERVICE_ACCOUNT = "sa-execution-runner@codexalpaca.iam.gserviceaccount.com"
DEFAULT_FIREWALL_RULE = "fw-allow-iap-ssh-execution"
DEFAULT_IAP_SOURCE_RANGE = "35.235.240.0/20"
DEFAULT_STARTUP_PACKAGES = ["python3", "python3-venv", "git", "jq"]
DEFAULT_TAGS = ["execution-runner", "paper-runner", "validation-only", "iap-ssh"]
DEFAULT_LABELS = {
    "plane": "execution",
    "mode": "paper",
    "stage": "validation",
    "stack": "codexalpaca",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the validation-only GCP execution VM for codexalpaca.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--zone", default=DEFAULT_ZONE)
    parser.add_argument("--network-name", default=DEFAULT_NETWORK)
    parser.add_argument("--subnet-name", default=DEFAULT_SUBNET)
    parser.add_argument("--address-name", default=DEFAULT_ADDRESS_NAME)
    parser.add_argument("--instance-name", default=DEFAULT_INSTANCE_NAME)
    parser.add_argument("--machine-type", default=DEFAULT_MACHINE_TYPE)
    parser.add_argument("--boot-disk-size-gb", type=int, default=DEFAULT_BOOT_DISK_SIZE_GB)
    parser.add_argument("--service-account-email", default=DEFAULT_SERVICE_ACCOUNT)
    parser.add_argument("--firewall-rule-name", default=DEFAULT_FIREWALL_RULE)
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


def wait_for_operation(operation_url: str, token: str, *, kind: str) -> dict[str, Any]:
    for _ in range(180):
        status, payload = request_json("GET", operation_url, token)
        if status >= 400:
            raise RuntimeError(f"{kind} operation poll failed: {status} {payload}")
        if payload.get("status") == "DONE":
            if payload.get("error"):
                raise RuntimeError(f"{kind} operation failed: {payload['error']}")
            return payload
        time.sleep(2)
    raise TimeoutError(f"{kind} operation did not finish in time: {operation_url}")


def read_project_email(credentials_json: Path) -> str:
    payload = json.loads(credentials_json.read_text(encoding="utf-8"))
    return str(payload.get("client_email") or "")


def ensure_static_ip(project_id: str, region: str, address_name: str, token: str) -> dict[str, Any]:
    get_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/addresses/{address_name}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return {
            "resource": "static_ip",
            "name": address_name,
            "action": "existing",
            "address": payload.get("address"),
            "status": payload.get("status"),
            "region": region,
        }
    if status != 404:
        raise RuntimeError(f"Unable to inspect static IP `{address_name}`: {status} {payload}")
    create_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/addresses"
    body = {
        "name": address_name,
        "addressType": "EXTERNAL",
        "networkTier": "PREMIUM",
        "description": "Reserved static IP for the codexalpaca paper execution VM.",
    }
    status, payload = request_json("POST", create_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create static IP `{address_name}`: {status} {payload}")
    op_name = str(payload.get("name") or "")
    wait_for_operation(
        f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/operations/{op_name}",
        token,
        kind="static_ip",
    )
    status, payload = request_json("GET", get_url, token)
    if status != 200:
        raise RuntimeError(f"Static IP `{address_name}` did not become readable after create: {status} {payload}")
    return {
        "resource": "static_ip",
        "name": address_name,
        "action": "created",
        "address": payload.get("address"),
        "status": payload.get("status"),
        "region": region,
    }


def ensure_iap_ssh_firewall_rule(
    project_id: str,
    firewall_rule_name: str,
    network_name: str,
    token: str,
) -> dict[str, Any]:
    get_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/firewalls/{firewall_rule_name}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return {
            "resource": "firewall_rule",
            "name": firewall_rule_name,
            "action": "existing",
            "network": network_name,
            "source_ranges": DEFAULT_IAP_SOURCE_RANGE,
        }
    if status != 404:
        raise RuntimeError(f"Unable to inspect firewall rule `{firewall_rule_name}`: {status} {payload}")
    create_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/firewalls"
    body = {
        "name": firewall_rule_name,
        "network": f"projects/{project_id}/global/networks/{network_name}",
        "direction": "INGRESS",
        "priority": 1000,
        "sourceRanges": [DEFAULT_IAP_SOURCE_RANGE],
        "targetTags": ["iap-ssh"],
        "allowed": [{"IPProtocol": "tcp", "ports": ["22"]}],
        "description": "Allow IAP TCP forwarding for SSH to the validation execution VM.",
    }
    status, payload = request_json("POST", create_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create firewall rule `{firewall_rule_name}`: {status} {payload}")
    op_name = str(payload.get("name") or "")
    wait_for_operation(
        f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/operations/{op_name}",
        token,
        kind="firewall_rule",
    )
    return {
        "resource": "firewall_rule",
        "name": firewall_rule_name,
        "action": "created",
        "network": network_name,
        "source_ranges": DEFAULT_IAP_SOURCE_RANGE,
    }


def startup_script() -> str:
    packages = " ".join(DEFAULT_STARTUP_PACKAGES)
    script = f"""#!/bin/bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y {packages}

mkdir -p /opt/codexalpaca /var/lib/codexalpaca /var/log/codexalpaca
cat >/var/lib/codexalpaca/validation_mode.json <<'JSON'
{{
  "stack": "codexalpaca",
  "plane": "execution",
  "mode": "paper",
  "stage": "validation_only"
}}
JSON

cat >/etc/motd <<'MOTD'
codexalpaca execution VM
mode: validation-only
do not start trading until the governed readiness gate is clean
MOTD

touch /var/lib/codexalpaca/bootstrap_complete
"""
    return textwrap.dedent(script).strip() + "\n"


def build_instance_body(
    project_id: str,
    region: str,
    zone: str,
    network_name: str,
    subnet_name: str,
    address_value: str,
    instance_name: str,
    machine_type: str,
    boot_disk_size_gb: int,
    service_account_email: str,
) -> dict[str, Any]:
    metadata_items = [
        {"key": "enable-oslogin", "value": "TRUE"},
        {"key": "block-project-ssh-keys", "value": "TRUE"},
        {"key": "serial-port-enable", "value": "TRUE"},
        {"key": "codexalpaca-validation-only", "value": "true"},
        {"key": "startup-script", "value": startup_script()},
    ]
    return {
        "name": instance_name,
        "description": "Institutional validation-only paper execution VM for codexalpaca.",
        "machineType": f"zones/{zone}/machineTypes/{machine_type}",
        "canIpForward": False,
        "deletionProtection": False,
        "labels": dict(DEFAULT_LABELS),
        "tags": {"items": list(DEFAULT_TAGS)},
        "metadata": {"items": metadata_items},
        "shieldedInstanceConfig": {
            "enableSecureBoot": True,
            "enableVtpm": True,
            "enableIntegrityMonitoring": True,
        },
        "networkInterfaces": [
            {
                "network": f"projects/{project_id}/global/networks/{network_name}",
                "subnetwork": f"regions/{region}/subnetworks/{subnet_name}",
                "accessConfigs": [
                    {
                        "name": "External NAT",
                        "type": "ONE_TO_ONE_NAT",
                        "networkTier": "PREMIUM",
                        "natIP": address_value,
                    }
                ],
            }
        ],
        "disks": [
            {
                "boot": True,
                "autoDelete": False,
                "type": "PERSISTENT",
                "initializeParams": {
                    "diskSizeGb": str(boot_disk_size_gb),
                    "diskType": f"zones/{zone}/diskTypes/pd-ssd",
                    "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts",
                    "labels": dict(DEFAULT_LABELS),
                },
            }
        ],
        "serviceAccounts": [
            {
                "email": service_account_email,
                "scopes": ["https://www.googleapis.com/auth/cloud-platform"],
            }
        ],
        "scheduling": {
            "automaticRestart": True,
            "onHostMaintenance": "MIGRATE",
            "provisioningModel": "STANDARD",
        },
    }


def ensure_instance(
    project_id: str,
    region: str,
    zone: str,
    network_name: str,
    subnet_name: str,
    address_value: str,
    instance_name: str,
    machine_type: str,
    boot_disk_size_gb: int,
    service_account_email: str,
    token: str,
) -> dict[str, Any]:
    get_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances/{instance_name}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        nic = (payload.get("networkInterfaces") or [{}])[0]
        access = (nic.get("accessConfigs") or [{}])[0]
        return {
            "resource": "instance",
            "name": instance_name,
            "action": "existing",
            "zone": zone,
            "status": payload.get("status"),
            "machine_type": payload.get("machineType", "").split("/")[-1],
            "service_account": ((payload.get("serviceAccounts") or [{}])[0]).get("email"),
            "external_ip": access.get("natIP"),
        }
    if status != 404:
        raise RuntimeError(f"Unable to inspect instance `{instance_name}`: {status} {payload}")
    create_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/instances"
    body = build_instance_body(
        project_id,
        region,
        zone,
        network_name,
        subnet_name,
        address_value,
        instance_name,
        machine_type,
        boot_disk_size_gb,
        service_account_email,
    )
    status, payload = request_json("POST", create_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create instance `{instance_name}`: {status} {payload}")
    op_name = str(payload.get("name") or "")
    wait_for_operation(
        f"https://compute.googleapis.com/compute/v1/projects/{project_id}/zones/{zone}/operations/{op_name}",
        token,
        kind="instance",
    )
    status, payload = request_json("GET", get_url, token)
    if status != 200:
        raise RuntimeError(f"Instance `{instance_name}` did not become readable after create: {status} {payload}")
    nic = (payload.get("networkInterfaces") or [{}])[0]
    access = (nic.get("accessConfigs") or [{}])[0]
    return {
        "resource": "instance",
        "name": instance_name,
        "action": "created",
        "zone": zone,
        "status": payload.get("status"),
        "machine_type": payload.get("machineType", "").split("/")[-1],
        "service_account": ((payload.get("serviceAccounts") or [{}])[0]).get("email"),
        "external_ip": access.get("natIP"),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Execution Validation VM Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Bootstrap service account: `{payload['bootstrap_service_account']}`")
    lines.append(f"- Region: `{payload['region']}`")
    lines.append(f"- Zone: `{payload['zone']}`")
    lines.append("")
    lines.append("## Resource Results")
    lines.append("")
    for row in list(payload.get("resource_results") or []):
        details: list[str] = []
        if row.get("address"):
            details.append(f"address `{row['address']}`")
        if row.get("status"):
            details.append(f"status `{row['status']}`")
        if row.get("machine_type"):
            details.append(f"machine `{row['machine_type']}`")
        if row.get("service_account"):
            details.append(f"service account `{row['service_account']}`")
        if row.get("external_ip"):
            details.append(f"external IP `{row['external_ip']}`")
        if row.get("network"):
            details.append(f"network `{row['network']}`")
        if row.get("source_ranges"):
            details.append(f"source ranges `{row['source_ranges']}`")
        extra = f" ({', '.join(details)})" if details else ""
        lines.append(f"- `{row['resource']}` `{row['name']}`: `{row['action']}`{extra}")
    lines.append("")
    lines.append("## Phase Plan")
    lines.append("")
    for phase in list(payload.get("phase_plan") or []):
        lines.append(f"- `{phase['phase']}`: {phase['summary']}")
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

    resource_results: list[dict[str, Any]] = []
    static_ip_result = ensure_static_ip(args.project_id, args.region, args.address_name, token)
    resource_results.append(static_ip_result)
    resource_results.append(
        ensure_iap_ssh_firewall_rule(args.project_id, args.firewall_rule_name, args.network_name, token)
    )
    resource_results.append(
        ensure_instance(
            args.project_id,
            args.region,
            args.zone,
            args.network_name,
            args.subnet_name,
            str(static_ip_result.get("address") or ""),
            args.instance_name,
            args.machine_type,
            args.boot_disk_size_gb,
            args.service_account_email,
            token,
        )
    )

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "bootstrap_service_account": read_project_email(credentials_json),
        "region": args.region,
        "zone": args.zone,
        "resource_results": resource_results,
        "phase_plan": [
            {"phase": "1", "summary": "Reserve the execution static IP and keep it attached to the validation VM."},
            {"phase": "2", "summary": "Keep the VM validation-only with OS Login, Shielded VM, and IAP-only SSH."},
            {
                "phase": "3",
                "summary": "Teach the VM bootstrap to pull runtime credentials from Secret Manager instead of workstation .env.",
            },
            {
                "phase": "4",
                "summary": "Run a trusted validation session and require a full runner evidence packet before cutover.",
            },
            {
                "phase": "5",
                "summary": "Promote the VM to canonical execution only after the governed readiness gate is clean.",
            },
        ],
        "next_actions": [
            "Teach the execution VM bootstrap to restore code and pull runtime secrets from Secret Manager.",
            "Grant operator access with OS Login / IAP before interactive administration is needed.",
            "Run validation-only checks on the VM and confirm outbound traffic uses the reserved static IP.",
            "Keep the current workstation runner available until the VM clears the full trusted-session gate.",
        ],
    }

    write_json(report_dir / "gcp_execution_validation_vm_status.json", payload)
    write_markdown(report_dir / "gcp_execution_validation_vm_status.md", payload)


if __name__ == "__main__":
    main()
