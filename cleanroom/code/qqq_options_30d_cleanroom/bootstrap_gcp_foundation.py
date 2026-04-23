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
DEFAULT_REGION = "us-east1"
DEFAULT_NETWORK = "vpc-codex-core"
DEFAULT_SUBNET = "subnet-us-east1-core"
DEFAULT_SUBNET_RANGE = "10.10.0.0/20"
DEFAULT_ARTIFACT_REPO = "trading"
SERVICE_ACCOUNT_SPECS = [
    ("sa-execution-runner", "Execution Runner", "Dedicated execution-plane runtime identity."),
    ("sa-research-batch", "Research Batch", "Research-plane Batch jobs identity."),
    ("sa-orchestrator", "Orchestrator", "Control-plane orchestration identity."),
    ("sa-ci-deployer", "CI Deployer", "Deployment and packaging identity."),
]
BUCKET_ROLE_SPECS = [
    ("data", "codexalpaca-data-us", {"versioning": False}),
    ("artifacts", "codexalpaca-artifacts-us", {"versioning": False}),
    ("control", "codexalpaca-control-us", {"versioning": True}),
    ("backups", "codexalpaca-backups-us", {"versioning": True}),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap the low-cost GCP foundation for codexalpaca.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--network-name", default=DEFAULT_NETWORK)
    parser.add_argument("--subnet-name", default=DEFAULT_SUBNET)
    parser.add_argument("--subnet-cidr", default=DEFAULT_SUBNET_RANGE)
    parser.add_argument("--artifact-repo", default=DEFAULT_ARTIFACT_REPO)
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


def wait_for_operation(operation_url: str, token: str, *, kind: str) -> dict[str, Any]:
    for _ in range(120):
        status, payload = request_json("GET", operation_url, token)
        if status >= 400:
            raise RuntimeError(f"{kind} operation poll failed: {status} {payload}")
        if payload.get("status") == "DONE" or payload.get("done") is True:
            if payload.get("error"):
                raise RuntimeError(f"{kind} operation failed: {payload['error']}")
            return payload
        time.sleep(2)
    raise TimeoutError(f"{kind} operation did not finish in time: {operation_url}")


def get_project_metadata(project_id: str, token: str) -> dict[str, Any]:
    status, payload = request_json("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}", token)
    if status >= 400:
        raise RuntimeError(f"Unable to read project metadata: {status} {payload}")
    return payload


def ensure_network(project_id: str, network_name: str, token: str) -> dict[str, Any]:
    get_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks/{network_name}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return {"resource": "network", "name": network_name, "action": "existing"}
    if status != 404:
        raise RuntimeError(f"Unable to inspect network `{network_name}`: {status} {payload}")
    insert_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/networks"
    body = {
        "name": network_name,
        "autoCreateSubnetworks": False,
        "routingConfig": {"routingMode": "REGIONAL"},
    }
    status, payload = request_json("POST", insert_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create network `{network_name}`: {status} {payload}")
    op_name = payload.get("name")
    wait_for_operation(
        f"https://compute.googleapis.com/compute/v1/projects/{project_id}/global/operations/{op_name}",
        token,
        kind="network",
    )
    return {"resource": "network", "name": network_name, "action": "created"}


def ensure_subnet(project_id: str, region: str, subnet_name: str, cidr: str, network_name: str, token: str) -> dict[str, Any]:
    get_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/subnetworks/{subnet_name}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return {"resource": "subnet", "name": subnet_name, "action": "existing", "cidr": cidr}
    if status != 404:
        raise RuntimeError(f"Unable to inspect subnet `{subnet_name}`: {status} {payload}")
    insert_url = f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/subnetworks"
    body = {
        "name": subnet_name,
        "ipCidrRange": cidr,
        "network": f"projects/{project_id}/global/networks/{network_name}",
        "privateIpGoogleAccess": True,
        "stackType": "IPV4_ONLY",
    }
    status, payload = request_json("POST", insert_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create subnet `{subnet_name}`: {status} {payload}")
    op_name = payload.get("name")
    wait_for_operation(
        f"https://compute.googleapis.com/compute/v1/projects/{project_id}/regions/{region}/operations/{op_name}",
        token,
        kind="subnet",
    )
    return {"resource": "subnet", "name": subnet_name, "action": "created", "cidr": cidr}


def bucket_insert(project_id: str, bucket_name: str, token: str, *, versioning: bool) -> tuple[int, dict[str, Any]]:
    url = f"https://storage.googleapis.com/storage/v1/b?project={urllib.parse.quote(project_id)}"
    body = {
        "name": bucket_name,
        "location": "US",
        "storageClass": "STANDARD",
        "iamConfiguration": {"uniformBucketLevelAccess": {"enabled": True}},
        "versioning": {"enabled": versioning},
    }
    return request_json("POST", url, token, body)


def ensure_bucket(project_id: str, project_number: str, desired_name: str, token: str, *, versioning: bool) -> dict[str, Any]:
    candidates = [desired_name, f"{desired_name}-{project_number}"]
    for candidate in candidates:
        status, payload = request_json("GET", f"https://storage.googleapis.com/storage/v1/b/{candidate}", token)
        if status == 200:
            return {"resource": "bucket", "name": candidate, "action": "existing", "versioning": versioning}
        if status == 404:
            create_status, create_payload = bucket_insert(project_id, candidate, token, versioning=versioning)
            if create_status in {200, 201}:
                return {"resource": "bucket", "name": candidate, "action": "created", "versioning": versioning}
            if create_status == 409:
                continue
            raise RuntimeError(f"Unable to create bucket `{candidate}`: {create_status} {create_payload}")
        if status == 403 and "does not have storage.buckets.get" in json.dumps(payload):
            create_status, create_payload = bucket_insert(project_id, candidate, token, versioning=versioning)
            if create_status in {200, 201}:
                return {"resource": "bucket", "name": candidate, "action": "created", "versioning": versioning}
            if create_status == 409:
                continue
            raise RuntimeError(f"Unable to create bucket `{candidate}`: {create_status} {create_payload}")
        raise RuntimeError(f"Unable to inspect bucket `{candidate}`: {status} {payload}")
    raise RuntimeError(f"Unable to secure a bucket name for `{desired_name}`")


def ensure_service_account(project_id: str, account_id: str, display_name: str, description: str, token: str) -> dict[str, Any]:
    create_url = f"https://iam.googleapis.com/v1/projects/{project_id}/serviceAccounts"
    body = {
        "accountId": account_id,
        "serviceAccount": {
            "displayName": display_name,
            "description": description,
        },
    }
    status, payload = request_json("POST", create_url, token, body)
    email = f"{account_id}@{project_id}.iam.gserviceaccount.com"
    if status in {200, 201}:
        return {"resource": "service_account", "name": email, "action": "created"}
    if status == 409:
        return {"resource": "service_account", "name": email, "action": "existing"}
    raise RuntimeError(f"Unable to create service account `{email}`: {status} {payload}")


def ensure_artifact_registry(project_id: str, region: str, repository_id: str, token: str) -> dict[str, Any]:
    encoded_repo = urllib.parse.quote(repository_id, safe="")
    get_url = f"https://artifactregistry.googleapis.com/v1/projects/{project_id}/locations/{region}/repositories/{encoded_repo}"
    status, payload = request_json("GET", get_url, token)
    if status == 200:
        return {"resource": "artifact_registry", "name": repository_id, "action": "existing", "region": region}
    if status != 404:
        raise RuntimeError(f"Unable to inspect Artifact Registry repo `{repository_id}`: {status} {payload}")
    insert_url = (
        f"https://artifactregistry.googleapis.com/v1/projects/{project_id}/locations/{region}/repositories"
        f"?repositoryId={urllib.parse.quote(repository_id)}"
    )
    body = {
        "format": "DOCKER",
        "description": "Institutional trading and research container images.",
    }
    status, payload = request_json("POST", insert_url, token, body)
    if status >= 400:
        raise RuntimeError(f"Unable to create Artifact Registry repo `{repository_id}`: {status} {payload}")
    op_name = payload.get("name")
    wait_for_operation(f"https://artifactregistry.googleapis.com/v1/{op_name}", token, kind="artifact_registry")
    return {"resource": "artifact_registry", "name": repository_id, "action": "created", "region": region}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP Foundation Bootstrap Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Project number: `{payload['project_number']}`")
    lines.append(f"- Bootstrap service account: `{payload['bootstrap_service_account']}`")
    lines.append(f"- Region: `{payload['region']}`")
    lines.append("")
    lines.append("## Resource Results")
    lines.append("")
    for row in list(payload.get("resource_results") or []):
        detail = []
        if row.get("cidr"):
            detail.append(f"cidr `{row['cidr']}`")
        if row.get("versioning") is not None:
            detail.append(f"versioning `{str(bool(row['versioning'])).lower()}`")
        if row.get("region"):
            detail.append(f"region `{row['region']}`")
        extra = f" ({', '.join(detail)})" if detail else ""
        lines.append(f"- `{row['resource']}` `{row['name']}`: `{row['action']}`{extra}")
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
    project_metadata = get_project_metadata(args.project_id, token)
    project_number = str(project_metadata.get("projectNumber") or "")

    resource_results: list[dict[str, Any]] = []
    resource_results.append(ensure_network(args.project_id, args.network_name, token))
    resource_results.append(
        ensure_subnet(args.project_id, args.region, args.subnet_name, args.subnet_cidr, args.network_name, token)
    )
    for _, desired_bucket_name, options in BUCKET_ROLE_SPECS:
        resource_results.append(
            ensure_bucket(
                args.project_id,
                project_number,
                desired_bucket_name,
                token,
                versioning=bool(options.get("versioning")),
            )
        )
    for account_id, display_name, description in SERVICE_ACCOUNT_SPECS:
        resource_results.append(ensure_service_account(args.project_id, account_id, display_name, description, token))
    resource_results.append(ensure_artifact_registry(args.project_id, args.region, args.artifact_repo, token))

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "project_number": project_number,
        "bootstrap_service_account": read_project_email(credentials_json),
        "region": args.region,
        "resource_results": resource_results,
        "next_actions": [
            "Reserve the execution static IP and create the validation-only execution VM next.",
            "Create runtime secrets in Secret Manager before cloud execution cut-in.",
            "Sync the current control-plane packet into the long-term control bucket.",
            "Rerun the GCP foundation readiness audit after any IAM or resource changes.",
        ],
    }

    write_json(report_dir / "gcp_foundation_bootstrap_status.json", payload)
    write_markdown(report_dir / "gcp_foundation_bootstrap_status.md", payload)


def read_project_email(credentials_json: Path) -> str:
    payload = json.loads(credentials_json.read_text(encoding="utf-8"))
    return str(payload.get("client_email") or "")


if __name__ == "__main__":
    main()
