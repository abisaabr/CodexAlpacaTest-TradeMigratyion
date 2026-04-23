from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "cleanroom"
    / "code"
    / "qqq_options_30d_cleanroom"
    / "build_gcp_shared_execution_lease_runtime_wiring_status.py"
)
SPEC = importlib.util.spec_from_file_location(
    "build_gcp_shared_execution_lease_runtime_wiring_status",
    MODULE_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_build_payload_reflects_current_runner_governance(tmp_path: Path) -> None:
    runner_repo_root = tmp_path / "runner"
    (runner_repo_root / "alpaca_lab" / "execution").mkdir(parents=True)
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio").mkdir(parents=True)
    (runner_repo_root / "scripts").mkdir(parents=True)

    (runner_repo_root / "alpaca_lab" / "execution" / "ownership.py").write_text(
        "class GCSGenerationMatchLeaseStore:\n    pass\n",
        encoding="utf-8",
    )
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "config.py").write_text(
        'from typing import Literal\n'
        'lease_backend: Literal["file", "gcs_generation_match"] = "file"\n'
        "gcs_lease_uri: str | None = None\n"
        "MULTI_TICKER_OWNERSHIP_LEASE_BACKEND = 'x'\n"
        "MULTI_TICKER_OWNERSHIP_GCS_LEASE_URI = 'y'\n",
        encoding="utf-8",
    )
    (runner_repo_root / "alpaca_lab" / "multi_ticker_portfolio" / "trader.py").write_text(
        "def _build_ownership_lease(self):\n"
        '    if ownership.lease_backend == "file":\n'
        "        return None\n"
        "    return GCSGenerationMatchLeaseStore.from_gcs_uri('gs://x')\n",
        encoding="utf-8",
    )
    (runner_repo_root / "scripts" / "run_multi_ticker_health_check.py").write_text(
        "def build_health_check_ownership_lease(portfolio_config):\n"
        '    if ownership.lease_backend == "gcs_generation_match":\n'
        "        return object()\n"
        "    return FileOwnershipLease(path=portfolio_config.ownership.lease_path)\n",
        encoding="utf-8",
    )
    (runner_repo_root / "scripts" / "run_multi_ticker_standby_failover_check.py").write_text(
        "def build_failover(config):\n"
        "    return evaluate_standby_failover_readiness(\n"
        "        lease_backend=config.ownership.lease_backend,\n"
        "    )\n",
        encoding="utf-8",
    )
    (runner_repo_root / "alpaca_lab" / "execution" / "failover.py").write_text(
        "ISSUE_CODE = 'non_file_ownership_backend_not_supported'\n",
        encoding="utf-8",
    )
    (runner_repo_root / "pyproject.toml").write_text(
        "[project]\n"
        "[project.optional-dependencies]\n"
        'gcp = ["google-cloud-storage>=2.18"]\n',
        encoding="utf-8",
    )

    payload = MODULE.build_payload(runner_repo_root, "81 passed")

    assert payload["wiring_findings"]["health_check_supports_gcs_backend"] is True
    assert payload["wiring_findings"]["health_check_default_path_still_file_scoped"] is True
    assert payload["wiring_findings"]["standby_check_passes_lease_backend"] is True
    assert payload["wiring_findings"]["standby_check_rejects_non_file_backend"] is True
