from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2 import service_account


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_CREDENTIALS_JSON = Path(r"C:\Users\rabisaab\Downloads\codexalpaca-7bcb9ac9a02d.json")
DEFAULT_PROJECT_ID = "codexalpaca"
DEFAULT_REPORT_DIR = REPO_ROOT / "docs" / "gcp_foundation"

TRACKED_PRINCIPALS = [
    "serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com",
    "serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com",
    "user:abisaabr19@gmail.com",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GCP IAM hardening packet from the live project policy.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    return parser


def mint_token(credentials_json: Path) -> str:
    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_json),
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    credentials.refresh(Request())
    return credentials.token


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
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, json.loads(body) if body else {}


def get_project_iam(project_id: str, token: str) -> dict[str, Any]:
    status, payload = request_json(
        "POST",
        f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}:getIamPolicy",
        token,
        {},
    )
    if status >= 400:
        raise RuntimeError(f"Unable to read project IAM policy: {status} {payload}")
    return payload


def principal_roles(policy: dict[str, Any]) -> dict[str, list[str]]:
    result = {principal: [] for principal in TRACKED_PRINCIPALS}
    for binding in policy.get("bindings", []):
        role = str(binding.get("role") or "")
        for member in binding.get("members", []):
            if member in result:
                result[member].append(role)
    return {principal: sorted(roles) for principal, roles in result.items()}


def build_payload(project_id: str, roles_by_principal: dict[str, list[str]]) -> dict[str, Any]:
    generated_at = datetime.now().astimezone().isoformat()
    owners = sorted(principal for principal, roles in roles_by_principal.items() if "roles/owner" in roles)
    hardening_required = bool(owners)

    recommendations = [
        {
            "principal": "serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "operator_access_only",
            "recommended_roles": [
                "roles/iap.tunnelResourceAccessor",
                "roles/compute.osAdminLogin",
                "roles/compute.viewer",
            ],
            "must_remove": ["roles/owner"],
            "rationale": "This principal is acting like an operator identity and should not keep project-wide Owner in steady state.",
        },
        {
            "principal": "serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "break_glass_only",
            "recommended_roles": [],
            "must_remove": ["roles/owner"],
            "rationale": "Bootstrap power should not remain standing after foundation setup. Preserve only as a documented break-glass path if still needed.",
        },
        {
            "principal": "serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:sa-execution-runner@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "runtime_scoped",
            "recommended_roles": [
                "roles/artifactregistry.reader",
                "roles/logging.logWriter",
                "roles/monitoring.metricWriter",
                "roles/secretmanager.secretAccessor",
            ],
            "must_remove": [],
            "rationale": "This is the sanctioned runtime identity and should remain narrowly scoped to execution runtime needs.",
        },
        {
            "principal": "serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:sa-research-batch@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "research_scoped",
            "recommended_roles": [
                "roles/artifactregistry.reader",
                "roles/logging.logWriter",
                "roles/monitoring.metricWriter",
            ],
            "must_remove": [],
            "rationale": "This is the sanctioned research runtime identity and should stay limited to research execution needs.",
        },
        {
            "principal": "serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:sa-orchestrator@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "orchestration_scoped",
            "recommended_roles": [
                "roles/logging.logWriter",
                "roles/monitoring.metricWriter",
            ],
            "must_remove": [],
            "rationale": "This identity should grow only through codified Workflows/Scheduler/Batch orchestration, not bootstrap privilege.",
        },
        {
            "principal": "serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:sa-ci-deployer@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "delivery_scoped",
            "recommended_roles": [
                "roles/artifactregistry.writer",
            ],
            "must_remove": [],
            "rationale": "This identity is appropriately narrow if Cloud Build or formal CI deployment becomes part of the sanctioned delivery path.",
        },
        {
            "principal": "serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com",
            "current_roles": roles_by_principal.get("serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com", []),
            "target_state": "quarantined_until_decision",
            "recommended_roles": [],
            "must_remove": [],
            "rationale": "This identity belongs to the unmanaged parallel runtime and should not gain any additional privilege until that path is formally adopted or removed.",
        },
        {
            "principal": "user:abisaabr19@gmail.com",
            "current_roles": roles_by_principal.get("user:abisaabr19@gmail.com", []),
            "target_state": "human_admin_review",
            "recommended_roles": [
                "roles/compute.osAdminLogin",
            ],
            "must_remove": [],
            "rationale": "Human admin posture should be reviewed separately from runtime identities. Project Owner on a human can remain temporarily during bootstrap, but it should still be intentionally reviewed.",
        },
    ]

    safe_cutover_order = [
        "Take and store a fresh IAM policy snapshot before any mutation.",
        "Confirm no bootstrap work is still in flight and no operator is depending on service-account Owner access.",
        "Remove roles/owner from ramzi-service-account after confirming operator access is intact through IAP, OS Login, and serviceAccountUser on sanctioned runtime identities.",
        "Remove roles/owner from sa-bootstrap-admin or convert it into an explicit break-glass identity with no standing use.",
        "Re-run the IAM hardening packet and the GCP project-state audit immediately after the role changes.",
        "Do not touch runtime-scoped service-account roles until the sanctioned execution session and orchestration plan are stable.",
    ]

    blockers = []
    if "serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com" in owners:
        blockers.append("ramzi-service-account still has project-level Owner.")
    if "serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com" in owners:
        blockers.append("sa-bootstrap-admin still has project-level Owner.")
    if "serviceAccount:multi-ticker-vm@codexalpaca.iam.gserviceaccount.com" in roles_by_principal:
        blockers.append("The quarantined multi-ticker-vm identity is still live in the project and should not be expanded before drift resolution.")

    readiness = "change_window_required" if hardening_required else "steady_state_ready"

    return {
        "generated_at": generated_at,
        "project_id": project_id,
        "phase1_readiness": readiness,
        "project_owner_principals": owners,
        "roles_by_principal": roles_by_principal,
        "recommendations": recommendations,
        "safe_cutover_order": safe_cutover_order,
        "blockers": blockers,
        "hard_rules": [
            "Do not remove Owner from service accounts during an unknown bootstrap or deployment window.",
            "Do not grant new broad roles to quarantined identities.",
            "Do not widen runtime identities to solve operator-access problems.",
            "Re-run the project-state audit after every IAM hardening step.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP IAM Hardening Status")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- Project ID: `{payload['project_id']}`")
    lines.append(f"- Phase 1 readiness: `{payload['phase1_readiness']}`")
    lines.append("")
    lines.append("## Project Owner Principals")
    lines.append("")
    for principal in payload["project_owner_principals"]:
        lines.append(f"- `{principal}`")
    lines.append("")
    lines.append("## Current Roles By Principal")
    lines.append("")
    for principal, roles in payload["roles_by_principal"].items():
        lines.append(f"- `{principal}`")
        if roles:
            for role in roles:
                lines.append(f"  - `{role}`")
        else:
            lines.append("  - `(none at project scope)`")
    lines.append("")
    lines.append("## Recommended Actions")
    lines.append("")
    for item in payload["recommendations"]:
        lines.append(f"- `{item['principal']}`")
        lines.append(f"  - target state: `{item['target_state']}`")
        if item["must_remove"]:
            lines.append(f"  - must remove: `{', '.join(item['must_remove'])}`")
        if item["recommended_roles"]:
            lines.append(f"  - recommended standing roles: `{', '.join(item['recommended_roles'])}`")
        lines.append(f"  - rationale: {item['rationale']}")
    lines.append("")
    lines.append("## Safe Cutover Order")
    lines.append("")
    for step in payload["safe_cutover_order"]:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("## Blockers")
    lines.append("")
    for blocker in payload["blockers"]:
        lines.append(f"- {blocker}")
    lines.append("")
    lines.append("## Hard Rules")
    lines.append("")
    for rule in payload["hard_rules"]:
        lines.append(f"- {rule}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# GCP IAM Hardening Handoff")
    lines.append("")
    lines.append("## Current Read")
    lines.append("")
    lines.append(f"- Phase 1 readiness: `{payload['phase1_readiness']}`")
    lines.append("- We are ready to plan IAM hardening, but actual privilege removal should happen in an explicit change window.")
    lines.append("")
    lines.append("## Immediate Goal")
    lines.append("")
    lines.append("- Remove project-level `Owner` from service accounts.")
    lines.append("- Preserve operator access through explicit minimal roles.")
    lines.append("- Keep quarantined identities frozen until drift is resolved.")
    lines.append("")
    lines.append("## First Principals To Change")
    lines.append("")
    lines.append("- `serviceAccount:ramzi-service-account@codexalpaca.iam.gserviceaccount.com`")
    lines.append("- `serviceAccount:sa-bootstrap-admin@codexalpaca.iam.gserviceaccount.com`")
    lines.append("")
    lines.append("## Do Not Change Yet")
    lines.append("")
    lines.append("- `sa-execution-runner`, `sa-research-batch`, `sa-orchestrator`, and `sa-ci-deployer` should stay narrowly scoped as they are unless a codified plane actually needs more.")
    lines.append("- `multi-ticker-vm@codexalpaca.iam.gserviceaccount.com` should not receive new privileges while the parallel runtime path is quarantined.")
    lines.append("")
    lines.append("## Rule")
    lines.append("")
    lines.append("- Do not perform the IAM cutover casually. Take a fresh policy snapshot, use a planned change window, and rerun the audit immediately after each privilege drop.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    token = mint_token(Path(args.credentials_json).resolve())
    policy = get_project_iam(args.project_id, token)
    roles = principal_roles(policy)
    payload = build_payload(args.project_id, roles)

    report_dir = Path(args.report_dir).resolve()
    write_json(report_dir / "gcp_iam_hardening_status.json", payload)
    write_markdown(report_dir / "gcp_iam_hardening_status.md", payload)
    write_handoff(report_dir / "gcp_iam_hardening_handoff.md", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
