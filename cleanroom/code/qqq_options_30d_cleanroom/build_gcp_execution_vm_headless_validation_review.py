from __future__ import annotations

import argparse
import json
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
    parser = argparse.ArgumentParser(description="Review the current headless execution VM validation run from GCS state.")
    parser.add_argument("--credentials-json", default=str(DEFAULT_CREDENTIALS_JSON))
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
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
    lines: list[str] = []
    lines.append("# GCP Execution VM Headless Validation Review")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Generated at: `{payload['generated_at']}`")
    lines.append(f"- VM name: `{payload['vm_name']}`")
    lines.append(f"- Run ID: `{payload['run_id']}`")
    lines.append(f"- Review state: `{payload['review_state']}`")
    lines.append(f"- Result prefix: `{payload['validation_result_gcs_prefix']}`")
    lines.append("")
    lines.append("## Observed Objects")
    lines.append("")
    for object_name in list(payload.get("observed_objects") or []):
        lines.append(f"- `{object_name}`")
    lines.append("")
    if payload.get("launch_result"):
        lines.append("## Launch Result")
        lines.append("")
        lines.append(f"- Validation exit code: `{payload['launch_result'].get('validation_exit_code')}`")
        lines.append(f"- Validation status present: `{payload['launch_result'].get('validation_status_present')}`")
        lines.append(f"- Doctor present: `{payload['launch_result'].get('doctor_present')}`")
        lines.append(f"- Pytest log present: `{payload['launch_result'].get('pytest_log_present')}`")
        lines.append("")
    if payload.get("validation_status"):
        validation_status = payload["validation_status"]
        lines.append("## Validation Status")
        lines.append("")
        lines.append(f"- Observed external IP: `{validation_status.get('observed_external_ip')}`")
        lines.append(f"- Runtime bootstrap complete: `{validation_status.get('runtime_bootstrap_complete')}`")
        lines.append(f"- Doctor python ok: `{validation_status.get('doctor_python_ok')}`")
        lines.append(f"- Pytest exit code: `{validation_status.get('pytest_exit_code')}`")
        lines.append("")
    lines.append("## Next Actions")
    lines.append("")
    for item in list(payload.get("next_actions") or []):
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    report_dir = Path(args.report_dir).resolve()
    launch_status_path = report_dir / "gcp_execution_vm_headless_validation_status.json"
    launch_status = json.loads(launch_status_path.read_text(encoding="utf-8"))

    result_prefix_uri = str(launch_status["validation_result_gcs_prefix"])
    if not result_prefix_uri.startswith("gs://"):
        raise RuntimeError(f"Unexpected result prefix URI: {result_prefix_uri}")
    bucket_and_prefix = result_prefix_uri[5:]
    bucket_name, object_prefix = bucket_and_prefix.split("/", 1)

    credentials = service_account.Credentials.from_service_account_file(str(Path(args.credentials_json).resolve()))
    client = storage.Client(project=args.project_id, credentials=credentials)
    observed_objects = sorted(blob.name for blob in client.list_blobs(bucket_name, prefix=object_prefix))

    launch_result = read_gcs_json(client, bucket_name, f"{object_prefix}/launch_result.json")
    validation_status = read_gcs_json(client, bucket_name, f"{object_prefix}/validation_status.json")

    review_state = "pending"
    next_actions = [
        "Keep polling the headless validation result prefix until launch_result.json appears.",
    ]
    if launch_result is not None:
        exit_code = int(launch_result.get("validation_exit_code", 999))
        if exit_code == 0 and validation_status is not None:
            review_state = "passed"
            next_actions = [
                "The headless validation gate is clean enough to review for trusted validation-session readiness.",
                "Read doctor.json and pytest.log before promoting the VM beyond validation-only posture.",
            ]
        else:
            review_state = "failed"
            next_actions = [
                "Read launch_result.json, validation_status.json, doctor.json, pytest.log, and validation-run.log from the result prefix.",
                "Do not move toward a trusted validation session until the failure is understood and repaired.",
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
        "validation_status": validation_status,
        "next_actions": next_actions,
    }

    json_path = report_dir / "gcp_execution_vm_headless_validation_review_status.json"
    md_path = report_dir / "gcp_execution_vm_headless_validation_review_status.md"
    write_json(json_path, payload)
    write_markdown(md_path, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
