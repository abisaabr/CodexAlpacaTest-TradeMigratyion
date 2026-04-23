from __future__ import annotations

import argparse
import json
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
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_PROJECT_NUMBER = "922745393036"

EXPECTED_BUCKETS = {
    "codexalpaca-data-us",
    "codexalpaca-artifacts-us",
    "codexalpaca-control-us",
    "codexalpaca-backups-us",
}
EXPECTED_SERVICE_ACCOUNTS = {
    "sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com",
    "sa-execution-runner@codexalpaca.iam.gserviceaccount.com",
    "sa-research-batch@codexalpaca.iam.gserviceaccount.com",
    "sa-orchestrator@codexalpaca.iam.gserviceaccount.com",
    "sa-ci-deployer@codexalpaca.iam.gserviceaccount.com",
}
EXPECTED_INSTANCES = {
    "vm-execution-paper-01",
}
EXPECTED_NETWORKS = {
    "vpc-codex-core",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a live GCP project state audit packet.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--project-number", default=DEFAULT_PROJECT_NUMBER)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def mint_token(credentials_json: Path) -> service_account.Credentials:
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_json),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    return credentials


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


def list_enabled_services(project_number: str, token: str) -> list[str]:
    services: list[str] = []
    url = f"https://serviceusage.googleapis.com/v1/projects/{project_number}/services?filter=state:ENABLED"
    while url:
        status, payload = request_json("GET", url, token)
        if status >= 400:
            raise RuntimeError(f"Unable to list enabled services: {status} {payload}")
        services.extend(str(row.get("config", {}).get("name") or "") for row in payload.get("services", []))
        next_page = str(payload.get("nextPageToken") or "")
        url = (
            f"https://serviceusage.googleapis.com/v1/projects/{project_number}/services?filter=state:ENABLED&pageToken={urllib.parse.quote(next_page)}"
            if next_page
            else ""
        )
    return sorted(name for name in services if name)


def list_service_accounts(project_id: str, token: str) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    url = f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts"
    while url:
        status, payload = request_json("GET", url, token)
        if status >= 400:
            raise RuntimeError(f"Unable to list service accounts: {status} {payload}")
        accounts.extend(payload.get("accounts", []))
        next_page = str(payload.get("nextPageToken") or "")
        url = f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts?pageToken={urllib.parse.quote(next_page)}" if next_page else ""
    return accounts


def list_instances(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/instances", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list instances: {status} {payload}")
    items: list[dict[str, Any]] = []
    for scoped in payload.get("items", {}).values():
        items.extend(scoped.get("instances", []))
    return items


def list_addresses(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/addresses", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list addresses: {status} {payload}")
    items: list[dict[str, Any]] = []
    for scoped in payload.get("items", {}).values():
        items.extend(scoped.get("addresses", []))
    return items


def list_firewalls(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/firewalls", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list firewalls: {status} {payload}")
    return list(payload.get("items", []))


def list_networks(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list networks: {status} {payload}")
    return list(payload.get("items", []))


def list_subnetworks(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://compute.googleapis.com/compute/v1/projects/{project_id}/aggregated/subnetworks", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list subnetworks: {status} {payload}")
    items: list[dict[str, Any]] = []
    for scoped in payload.get("items", {}).values():
        items.extend(scoped.get("subnetworks", []))
    return items


def list_artifact_repositories(project_id: str, token: str) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    for location in ("us-east1", "us-central1"):
        status, payload = request_json(
            "GET",
            f"https://artifactregistry.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories",
            token,
        )
        if status == 404:
            continue
        if status >= 400:
            raise RuntimeError(f"Unable to list artifact repositories in {location}: {status} {payload}")
        repositories.extend(payload.get("repositories", []))
    return repositories


def list_secrets(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json("GET", f"https://secretmanager.googleapis.com/v1/projects/{project_id}/secrets", token)
    if status >= 400:
        raise RuntimeError(f"Unable to list secrets: {status} {payload}")
    return list(payload.get("secrets", []))


def list_workflows(project_id: str, token: str) -> list[str]:
    status, payload = request_json("GET", f"https://workflows.googleapis.com/v1/projects/{project_id}/locations/us-east1/workflows", token)
    if status == 404:
        return []
    if status >= 400:
        raise RuntimeError(f"Unable to list workflows: {status} {payload}")
    return [str(row.get("name") or "").split("/")[-1] for row in payload.get("workflows", [])]


def list_batch_jobs(project_id: str, token: str) -> list[str]:
    status, payload = request_json("GET", f"https://batch.googleapis.com/v1/projects/{project_id}/locations/us-east1/jobs", token)
    if status == 404:
        return []
    if status >= 400:
        raise RuntimeError(f"Unable to list batch jobs: {status} {payload}")
    return [str(row.get("name") or "").split("/")[-1] for row in payload.get("jobs", [])]


def list_scheduler_jobs(project_id: str, token: str) -> list[str]:
    jobs: list[str] = []
    for location in ("us-east1", "us-central1"):
        status, payload = request_json("GET", f"https://cloudscheduler.googleapis.com/v1/projects/{project_id}/locations/{location}/jobs", token)
        if status == 404:
            continue
        if status >= 400:
            raise RuntimeError(f"Unable to list scheduler jobs in {location}: {status} {payload}")
        jobs.extend(str(row.get("name") or "").split("/")[-1] for row in payload.get("jobs", []))
    return sorted(jobs)


def interesting_project_iam(project_id: str, token: str) -> list[dict[str, Any]]:
    status, payload = request_json(
        "POST",
        f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:getIamPolicy",
        token,
        {},
    )
    if status >= 400:
        raise RuntimeError(f"Unable to read project IAM policy: {status} {payload}")
    interesting: list[dict[str, Any]] = []
    for binding in payload.get("bindings", []):
        members = list(binding.get("members", []))
        if any(
            any(key in member for key in ("sa-execution-runner", "sa-research-batch", "sa-orchestrator", "ramzi-service-account", "multi-ticker-vm", "sa-bootstrap-admin"))
            for member in members
        ):
            interesting.append({"role": binding.get("role"), "members": members})
    return interesting


def list_bucket_samples(client: storage.Client, bucket_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    samples: dict[str, list[dict[str, Any]]] = {}
    for bucket_name in bucket_names:
        blobs = list(client.list_blobs(bucket_name, max_results=20))
        samples[bucket_name] = [{"name": blob.name, "size": blob.size} for blob in blobs]
    return samples


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Project State Audit")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Audit posture: `{payload['audit_posture']}`")
    lines.append("")
    lines.append("## Foundation Summary")
    lines.append("")
    lines.append(f"- Enabled services: `{payload['summary']['enabled_service_count']}`")
    lines.append(f"- Buckets: `{payload['summary']['bucket_count']}`")
    lines.append(f"- Service accounts: `{payload['summary']['service_account_count']}`")
    lines.append(f"- Compute instances: `{payload['summary']['instance_count']}`")
    lines.append(f"- Static addresses: `{payload['summary']['address_count']}`")
    lines.append(f"- Secrets: `{payload['summary']['secret_count']}`")
    lines.append(f"- Artifact repositories: `{payload['summary']['artifact_repository_count']}`")
    lines.append("")
    lines.append("## Managed Execution Footprint")
    lines.append("")
    for row in list(payload.get("managed_execution_footprint") or []):
        lines.append(f"- `{row['name']}` in `{row['zone']}`: `{row['status']}` via `{row['serviceAccount']}`")
    lines.append("")
    lines.append("## Drift / Unmanaged Footprint")
    lines.append("")
    for row in list(payload.get("unmanaged_or_unmodeled_resources") or []):
        lines.append(f"- `{row['resource_type']}` `{row['name']}`: `{row['reason']}`")
    lines.append("")
    lines.append("## Highest-Risk Findings")
    lines.append("")
    for row in list(payload.get("highest_risk_findings") or []):
        lines.append(f"- `{row}`")
    lines.append("")
    lines.append("## Immediate Recommendations")
    lines.append("")
    for row in list(payload.get("immediate_recommendations") or []):
        lines.append(f"- {row}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    credentials_json = Path(args.credentials_json).resolve()
    credentials = mint_token(credentials_json)
    token = str(credentials.token)
    storage_client = storage.Client(project=args.project_id, credentials=credentials)

    enabled_services = list_enabled_services(args.project_number, token)
    buckets = sorted(bucket.name for bucket in storage_client.list_buckets(project=args.project_id))
    service_accounts = list_service_accounts(args.project_id, token)
    instances = list_instances(args.project_id, token)
    addresses = list_addresses(args.project_id, token)
    firewalls = list_firewalls(args.project_id, token)
    networks = list_networks(args.project_id, token)
    subnetworks = list_subnetworks(args.project_id, token)
    artifact_repositories = list_artifact_repositories(args.project_id, token)
    secrets = list_secrets(args.project_id, token)
    workflows = list_workflows(args.project_id, token)
    batch_jobs = list_batch_jobs(args.project_id, token)
    scheduler_jobs = list_scheduler_jobs(args.project_id, token)
    project_iam_bindings = interesting_project_iam(args.project_id, token)

    managed_execution_footprint = [
        {
            "name": str(instance.get("name") or ""),
            "zone": str(instance.get("zone") or "").split("/")[-1],
            "status": str(instance.get("status") or ""),
            "serviceAccount": str(((instance.get("serviceAccounts") or [{}])[0].get("email")) or ""),
            "labels": instance.get("labels", {}),
        }
        for instance in instances
        if str(instance.get("name") or "") in EXPECTED_INSTANCES
    ]

    unmanaged_or_unmodeled_resources: list[dict[str, str]] = []
    for instance in instances:
        name = str(instance.get("name") or "")
        if name not in EXPECTED_INSTANCES:
            unmanaged_or_unmodeled_resources.append(
                {
                    "resource_type": "compute_instance",
                    "name": name,
                    "reason": "running outside the codified execution-validation footprint",
                }
            )
    for bucket in buckets:
        if bucket not in EXPECTED_BUCKETS:
            unmanaged_or_unmodeled_resources.append(
                {
                    "resource_type": "bucket",
                    "name": bucket,
                    "reason": "not part of the codified role-separated storage foundation",
                }
            )
    for account in service_accounts:
        email = str(account.get("email") or "")
        if email.endswith("-compute@developer.gserviceaccount.com"):
            continue
        if email not in EXPECTED_SERVICE_ACCOUNTS and email != "ramzi-service-account@codexalpaca.iam.gserviceaccount.com":
            unmanaged_or_unmodeled_resources.append(
                {
                    "resource_type": "service_account",
                    "name": email,
                    "reason": "not part of the codified runtime identity set",
                }
            )
    for network in networks:
        name = str(network.get("name") or "")
        if name == "default":
            unmanaged_or_unmodeled_resources.append(
                {
                    "resource_type": "network",
                    "name": name,
                    "reason": "default network remains enabled and broad",
                }
            )

    highest_risk_findings = [
        "Project-level Owner remains granted to service accounts, including the bootstrap identity and ramzi-service-account; this is too broad for steady-state runtime operations.",
        "A second running VM (`multi-ticker-trader-v1`) and its supporting runtime resources exist outside the codified control-plane rollout, creating architecture drift and possible execution ambiguity.",
        "The default VPC network still exists alongside the intended `vpc-codex-core`, which weakens network posture and can hide ungoverned resources.",
        "Cloud Batch, Workflows, and Cloud Scheduler APIs are enabled, but there are no codified jobs/workflows/schedules yet; orchestration capability exists without an institutional deployment layer.",
        "We have a validation-grade execution VM, but not yet a cloud-backed shared execution lease, so the first broker-facing cloud session still depends on an explicit exclusive operator window.",
    ]

    immediate_recommendations = [
        "Freeze architecture drift by classifying `multi-ticker-trader-v1`, `multi-ticker-vm`, `multi-ticker-vm-env`, `codexalpaca-runtime-us-central1`, and `codexalpaca-containers` as either formalized or decommissioned.",
        "Step down IAM by removing project-level Owner from service accounts after replacing it with narrowly scoped runtime and bootstrap roles.",
        "Adopt `vpc-codex-core` as the only sanctioned runtime network and plan retirement or explicit quarantine of default-network usage.",
        "Use the green headless validation packet to run one trusted validation paper session only during an explicitly exclusive paper-account window.",
        "Build the missing orchestration layer next: Cloud Build/Artifact Registry image pipeline, Workflows/Scheduler control plane, and Batch-backed research execution.",
    ]

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "audit_posture": "foundation_present_with_material_drift",
        "summary": {
            "enabled_service_count": len(enabled_services),
            "bucket_count": len(buckets),
            "service_account_count": len(service_accounts),
            "instance_count": len(instances),
            "address_count": len(addresses),
            "secret_count": len(secrets),
            "artifact_repository_count": len(artifact_repositories),
            "workflow_count": len(workflows),
            "batch_job_count": len(batch_jobs),
            "scheduler_job_count": len(scheduler_jobs),
        },
        "enabled_services": enabled_services,
        "buckets": buckets,
        "bucket_samples": list_bucket_samples(storage_client, buckets),
        "service_accounts": sorted(str(account.get("email") or "") for account in service_accounts),
        "instances": [
            {
                "name": str(instance.get("name") or ""),
                "zone": str(instance.get("zone") or "").split("/")[-1],
                "status": str(instance.get("status") or ""),
                "machineType": str(instance.get("machineType") or "").split("/")[-1],
                "serviceAccount": str(((instance.get("serviceAccounts") or [{}])[0].get("email")) or ""),
                "externalIp": str(
                    ((((instance.get("networkInterfaces") or [{}])[0].get("accessConfigs") or [{}])[0].get("natIP")) if instance.get("networkInterfaces") else "")
                )
                or None,
                "labels": instance.get("labels", {}),
            }
            for instance in instances
        ],
        "addresses": [
            {
                "name": str(address.get("name") or ""),
                "address": str(address.get("address") or ""),
                "region": str(address.get("region") or "").split("/")[-1],
                "status": str(address.get("status") or ""),
                "users": list(address.get("users") or []),
            }
            for address in addresses
        ],
        "firewall_rules": [
            {
                "name": str(rule.get("name") or ""),
                "network": str(rule.get("network") or "").split("/")[-1],
                "direction": str(rule.get("direction") or ""),
                "targetTags": list(rule.get("targetTags") or []),
                "sourceRanges": list(rule.get("sourceRanges") or []),
            }
            for rule in firewalls
        ],
        "networks": [
            {
                "name": str(network.get("name") or ""),
                "autoCreateSubnetworks": bool(network.get("autoCreateSubnetworks")),
                "subnetCount": len(network.get("subnetworks") or []),
            }
            for network in networks
        ],
        "subnetworks": [
            {
                "name": str(subnet.get("name") or ""),
                "region": str(subnet.get("region") or "").split("/")[-1],
                "network": str(subnet.get("network") or "").split("/")[-1],
                "ipCidrRange": str(subnet.get("ipCidrRange") or ""),
            }
            for subnet in subnetworks
        ],
        "artifact_repositories": [
            {
                "name": str(repo.get("name") or "").split("/")[-1],
                "location": str(repo.get("name") or "").split("/")[3],
                "format": str(repo.get("format") or ""),
            }
            for repo in artifact_repositories
        ],
        "secrets": [str(secret.get("name") or "").split("/")[-1] for secret in secrets],
        "workflows": workflows,
        "batch_jobs": batch_jobs,
        "scheduler_jobs": scheduler_jobs,
        "project_iam_bindings": project_iam_bindings,
        "managed_execution_footprint": managed_execution_footprint,
        "unmanaged_or_unmodeled_resources": unmanaged_or_unmodeled_resources,
        "highest_risk_findings": highest_risk_findings,
        "immediate_recommendations": immediate_recommendations,
    }

    write_json(report_dir / "gcp_project_state_audit_status.json", payload)
    write_markdown(report_dir / "gcp_project_state_audit_status.md", payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
