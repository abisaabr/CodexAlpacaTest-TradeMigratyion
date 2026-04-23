from __future__ import annotations

import argparse
import json
import time
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review the current headless execution VM lease dry-run validation run from GCS state."
    )
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--wait-seconds", type=int, default=900)
    parser.add_argument("--poll-seconds", type=int, default=15)
    return parser


def read_gcs_json(client: storage.Client, bucket_name: str, object_name: str) -> dict[str, Any] | None:
    blob = client.bucket(bucket_name).blob(object_name)
    if not blob.exists(client):
        return None
    return json.loads(blob.download_as_text())


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution VM Lease Dry-Run Validation Review",
        "",
        "## Snapshot",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Review state: `{payload['review_state']}`",
        f"- Result prefix: `{payload['validation_result_gcs_prefix']}`",
        "",
        "## Observed Objects",
        "",
    ]
    for object_name in list(payload.get("observed_objects") or []):
        lines.append(f"- `{object_name}`")
    lines.append("")
    if payload.get("launch_result"):
        launch_result = payload["launch_result"]
        lines.extend(
            [
                "## Launch Result",
                "",
                f"- Validation exit code: `{launch_result.get('validation_exit_code')}`",
                f"- Lease validation status present: `{launch_result.get('lease_validation_status_present')}`",
                f"- Doctor present: `{launch_result.get('doctor_present')}`",
                f"- Pytest log present: `{launch_result.get('pytest_log_present')}`",
                "",
            ]
        )
    if payload.get("lease_validation_status"):
        validation_status = payload["lease_validation_status"]
        lines.extend(
            [
                "## Lease Validation Status",
                "",
                f"- Observed external IP: `{validation_status.get('observed_external_ip')}`",
                f"- Lease backend: `{validation_status.get('lease_backend')}`",
                f"- Lease class: `{validation_status.get('ownership_lease_class')}`",
                f"- Lease dry run passed: `{validation_status.get('lease_dry_run_passed')}`",
                f"- Targeted pytest exit code: `{validation_status.get('targeted_pytest_exit_code')}`",
                f"- Final record present: `{validation_status.get('final_record_present')}`",
                "",
            ]
        )
    lines.extend(["## Next Actions", ""])
    for item in list(payload.get("next_actions") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_handoff(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# GCP Execution VM Lease Dry-Run Validation Handoff",
        "",
        f"- Review state: `{payload['review_state']}`",
        f"- VM name: `{payload['vm_name']}`",
        f"- Run ID: `{payload['run_id']}`",
        f"- Result prefix: `{payload['validation_result_gcs_prefix']}`",
        "",
    ]
    if payload.get("lease_validation_status"):
        validation_status = payload["lease_validation_status"]
        lines.extend(
            [
                "## Observed Outcome",
                "",
                f"- Lease backend: `{validation_status.get('lease_backend')}`",
                f"- Lease class: `{validation_status.get('ownership_lease_class')}`",
                f"- Acquire generation: `{(validation_status.get('acquired') or {}).get('generation')}`",
                f"- Renew generation: `{(validation_status.get('renewed') or {}).get('generation')}`",
                f"- Takeover generation: `{(validation_status.get('takeover') or {}).get('generation')}`",
                f"- Final record present: `{validation_status.get('final_record_present')}`",
                "",
            ]
        )
    lines.extend(["## Operator Rule", ""])
    if payload["review_state"] == "passed":
        lines.append("- The shared execution lease is validated on the sanctioned VM in dry-run mode, but it is still not broker-facing live.")
        lines.append("- The next step is to keep enforcement off and move toward the governed trusted validation-session gate only when the exclusive execution window is explicit.")
    elif payload["review_state"] == "failed":
        lines.append("- Do not move toward broker-facing validation. Read the result prefix and repair the dry-run failure first.")
    else:
        lines.append("- Keep polling the result prefix until the launch packet lands.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    launch_status_path = report_dir / "gcp_execution_vm_headless_lease_dry_run_validation_status.json"
    launch_status = json.loads(launch_status_path.read_text(encoding="utf-8"))

    result_prefix_uri = str(launch_status["validation_result_gcs_prefix"])
    if not result_prefix_uri.startswith("gs://"):
        raise RuntimeError(f"Unexpected result prefix URI: {result_prefix_uri}")
    bucket_and_prefix = result_prefix_uri[5:]
    bucket_name, object_prefix = bucket_and_prefix.split("/", 1)

    credentials = service_account.Credentials.from_service_account_file(
        str(Path(args.credentials_json).resolve())
    )
    client = storage.Client(project=args.project_id, credentials=credentials)

    deadline = time.time() + max(0, int(args.wait_seconds))
    launch_result = None
    lease_validation_status = None
    observed_objects: list[str] = []

    while True:
        observed_objects = sorted(blob.name for blob in client.list_blobs(bucket_name, prefix=object_prefix))
        launch_result = read_gcs_json(client, bucket_name, f"{object_prefix}/launch_result.json")
        lease_validation_status = read_gcs_json(
            client,
            bucket_name,
            f"{object_prefix}/lease_validation_status.json",
        )
        if launch_result is not None:
            break
        if time.time() >= deadline:
            break
        time.sleep(max(1, int(args.poll_seconds)))

    review_state = "pending"
    next_actions = [
        "Keep polling the headless lease dry-run result prefix until launch_result.json appears.",
    ]
    if launch_result is not None:
        exit_code = int(launch_result.get("validation_exit_code", 999))
        lease_passed = bool((lease_validation_status or {}).get("lease_dry_run_passed"))
        targeted_pytest_exit = int((lease_validation_status or {}).get("targeted_pytest_exit_code", 999))
        final_record_present = bool((lease_validation_status or {}).get("final_record_present", True))
        if exit_code == 0 and lease_validation_status is not None and lease_passed and targeted_pytest_exit == 0 and not final_record_present:
            review_state = "passed"
            next_actions = [
                "The sanctioned VM proved the shared execution lease in dry-run mode without entering the trading loop.",
                "Keep lease enforcement off by default and use this packet as the prerequisite for the next trusted validation-session discussion.",
            ]
        else:
            review_state = "failed"
            next_actions = [
                "Read launch_result.json, lease_validation_status.json, doctor.json, pytest_targeted.log, lease_validation.log, and validation-run.log from the result prefix.",
                "Do not move toward broker-facing trusted validation until the dry-run failure is understood and repaired.",
            ]

    payload = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "project_id": args.project_id,
        "vm_name": launch_status["vm_name"],
        "run_id": launch_status["run_id"],
        "validation_result_gcs_prefix": result_prefix_uri,
        "review_state": review_state,
        "observed_objects": observed_objects,
        "launch_result": launch_result,
        "lease_validation_status": lease_validation_status,
        "next_actions": next_actions,
    }

    json_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_review_status.json"
    md_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_review_status.md"
    handoff_path = report_dir / "gcp_execution_vm_lease_dry_run_validation_handoff.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    write_handoff(handoff_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
