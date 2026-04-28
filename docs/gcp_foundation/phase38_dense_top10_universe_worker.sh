set -eu

WAVE_ID="top100_liquidity_research_20260426"
PHASE_ID="phase38_dense_top10_universe_20260428203428"
SOURCE_URI="gs://codexalpaca-control-us/research_source/codexalpaca_runner_source_133a1a7f5cd1.zip"
QUEUE_URI="gs://codexalpaca-control-us/research_waves/top100_liquidity_research_20260426/top100_portfolio_bruteforce_queue.json"
VARIANTS_URI="gs://codexalpaca-control-us/research_waves/broad_150_stock_proxy_20260424/broad_150_stock_proxy_variants.jsonl"
PROJECT_ID="codexalpaca"
SYMBOLS="SPY NVDA QQQ AMZN TSLA MSFT IWM AAPL META MU"

TASK_INDEX="${BATCH_TASK_INDEX:-0}"
SYMBOL=""
i=0
for candidate_symbol in $SYMBOLS; do
  if [ "$i" = "$TASK_INDEX" ]; then
    SYMBOL="$candidate_symbol"
  fi
  i=$((i + 1))
done
if [ -z "$SYMBOL" ]; then
  echo "No symbol mapped for BATCH_TASK_INDEX=$TASK_INDEX" >&2
  exit 2
fi

BUILD_NAME="top100_phase38_${SYMBOL}_dense_atm5_options_20260302_20260423"
WORK="/tmp/${PHASE_ID}_${SYMBOL}"
COMBINED="$WORK/combined_top100_silver"
DENSE_DIR="$WORK/dense_option_universe"
SELECTED_ROOT="$DENSE_DIR/selected_option_contracts"
REPLAY_DIR="$WORK/option_aware_replay"
PORTFOLIO_DIR="$WORK/portfolio_report"
PROMOTION_DIR="$WORK/promotion_review_packet"
QUEUE_JSON="$WORK/source_queue.json"
CANDIDATE_QUEUE_JSON="$WORK/phase38_${SYMBOL}_queue.json"
VARIANTS_JSONL="$WORK/broad_150_stock_proxy_variants.jsonl"
REPORT_ROOT="gs://codexalpaca-control-us/research_results/${WAVE_ID}/portfolio_event_driven_data/${PHASE_ID}/data_shards/${SYMBOL}"
DATA_ROOT_URI="gs://codexalpaca-data-us/research_option_data/${WAVE_ID}/${BUILD_NAME}"

mkdir -p "$WORK" "$COMBINED" "$DENSE_DIR" "$REPLAY_DIR" "$PORTFOLIO_DIR" "$PROMOTION_DIR"
cd "$WORK"

python3 -m pip install --upgrade pip
python3 -m pip install google-cloud-storage google-cloud-secret-manager

cat > "$WORK/gcs_io.py" <<'PY'
from __future__ import annotations

import pathlib
import sys

from google.cloud import storage

client = storage.Client(project="codexalpaca")


def split_uri(uri: str) -> tuple[str, str]:
    rest = uri[5:]
    bucket, _, name = rest.partition("/")
    return bucket, name


def download(uri: str, dest: str) -> None:
    bucket_name, blob_name = split_uri(uri)
    pathlib.Path(dest).parent.mkdir(parents=True, exist_ok=True)
    client.bucket(bucket_name).blob(blob_name).download_to_filename(dest)


def download_prefix(uri: str, dest: str) -> None:
    bucket_name, prefix = split_uri(uri.rstrip("/") + "/")
    dest_path = pathlib.Path(dest)
    count = 0
    for blob in client.list_blobs(bucket_name, prefix=prefix):
        if blob.name.endswith("/"):
            continue
        rel = pathlib.PurePosixPath(blob.name).relative_to(pathlib.PurePosixPath(prefix))
        target = dest_path / pathlib.Path(*rel.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(target))
        count += 1
    print(f"downloaded_prefix {uri} files={count} dest={dest}")


def upload(src: str, uri: str) -> None:
    bucket_name, blob_prefix = split_uri(uri)
    bucket = client.bucket(bucket_name)
    src_path = pathlib.Path(src)
    if src_path.is_dir():
        for path in src_path.rglob("*"):
            if path.is_file():
                rel = path.relative_to(src_path).as_posix()
                bucket.blob(f"{blob_prefix.rstrip('/')}/{rel}").upload_from_filename(str(path))
    elif src_path.exists():
        bucket.blob(blob_prefix).upload_from_filename(str(src_path))


if __name__ == "__main__":
    mode, source, dest = sys.argv[1:4]
    if mode == "download":
        download(source, dest)
    elif mode == "download-prefix":
        download_prefix(source, dest)
    elif mode == "upload":
        upload(source, dest)
    else:
        raise SystemExit(f"unknown mode {mode}")
PY

cat > "$WORK/read_secret.py" <<'PY'
from __future__ import annotations

import sys

from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/codexalpaca/secrets/{sys.argv[1]}/versions/latest"
response = client.access_secret_version(request={"name": name})
print(response.payload.data.decode("utf-8").strip())
PY

BOOT_OUT="$WORK/${PHASE_ID}_${SYMBOL}.bootstrap.out.log"
BOOT_ERR="$WORK/${PHASE_ID}_${SYMBOL}.bootstrap.err.log"
RUN_OUT="$WORK/${PHASE_ID}_${SYMBOL}.out.log"
RUN_ERR="$WORK/${PHASE_ID}_${SYMBOL}.err.log"
touch "$BOOT_OUT" "$BOOT_ERR" "$RUN_OUT" "$RUN_ERR"

upload_artifacts() {
  status=$?
  python3 "$WORK/gcs_io.py" upload "$BOOT_OUT" "${REPORT_ROOT}/logs/bootstrap.out.log" || true
  python3 "$WORK/gcs_io.py" upload "$BOOT_ERR" "${REPORT_ROOT}/logs/bootstrap.err.log" || true
  python3 "$WORK/gcs_io.py" upload "$RUN_OUT" "${REPORT_ROOT}/logs/run.out.log" || true
  python3 "$WORK/gcs_io.py" upload "$RUN_ERR" "${REPORT_ROOT}/logs/run.err.log" || true
  [ -f "$CANDIDATE_QUEUE_JSON" ] && python3 "$WORK/gcs_io.py" upload "$CANDIDATE_QUEUE_JSON" "${REPORT_ROOT}/candidate_queue/phase38_${SYMBOL}_queue.json" || true
  [ -d "$DENSE_DIR" ] && python3 "$WORK/gcs_io.py" upload "$DENSE_DIR" "${REPORT_ROOT}/dense_option_universe" || true
  [ -d "$WORK/repo/reports/${BUILD_NAME}" ] && python3 "$WORK/gcs_io.py" upload "$WORK/repo/reports/${BUILD_NAME}" "${REPORT_ROOT}/download_report" || true
  [ -f "$WORK/repo/data/raw/manifests/${BUILD_NAME}.json" ] && python3 "$WORK/gcs_io.py" upload "$WORK/repo/data/raw/manifests/${BUILD_NAME}.json" "${REPORT_ROOT}/download_manifest.json" || true
  [ -d "$WORK/repo/data/silver/historical/${BUILD_NAME}" ] && python3 "$WORK/gcs_io.py" upload "$WORK/repo/data/silver/historical/${BUILD_NAME}" "${DATA_ROOT_URI}/silver" || true
  [ -d "$WORK/repo/data/raw/historical/${BUILD_NAME}" ] && python3 "$WORK/gcs_io.py" upload "$WORK/repo/data/raw/historical/${BUILD_NAME}" "${DATA_ROOT_URI}/raw" || true
  [ -d "$REPLAY_DIR" ] && python3 "$WORK/gcs_io.py" upload "$REPLAY_DIR" "${REPORT_ROOT}/replay" || true
  [ -d "$PORTFOLIO_DIR" ] && python3 "$WORK/gcs_io.py" upload "$PORTFOLIO_DIR" "${REPORT_ROOT}/portfolio_report" || true
  [ -d "$PROMOTION_DIR" ] && python3 "$WORK/gcs_io.py" upload "$PROMOTION_DIR" "${REPORT_ROOT}/promotion_review_packet" || true
  exit $status
}
trap upload_artifacts EXIT

exec > "$BOOT_OUT" 2> "$BOOT_ERR"
echo "phase38_worker_start $(date -Iseconds) symbol=${SYMBOL} task_index=${TASK_INDEX}"
python3 --version

python3 "$WORK/gcs_io.py" download "$SOURCE_URI" "$WORK/source.zip"
python3 - <<'PY'
import zipfile
from pathlib import Path

work = Path.cwd()
with zipfile.ZipFile(work / "source.zip") as zf:
    zf.extractall(work / "repo")
PY

python3 "$WORK/gcs_io.py" download "$QUEUE_URI" "$QUEUE_JSON"
python3 "$WORK/gcs_io.py" download "$VARIANTS_URI" "$VARIANTS_JSONL"
export SYMBOL

python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

symbol = os.environ["SYMBOL"]
source_queue = json.loads(Path("source_queue.json").read_text(encoding="utf-8"))
queue_items = [
    item
    for item in source_queue.get("queue_items", [])
    if str(item.get("symbol") or "").upper() == symbol and not item.get("blockers")
]
queue_items.sort(
    key=lambda item: (
        int(item.get("liquidity_rank") or 9999),
        int(item.get("rank") or 999999),
    )
)
candidate_queue = {
    **source_queue,
    "status": "phase38_dense_top10_universe_symbol_queue",
    "objective": "research_only_dense_top10_liquid_underlying_fill_diagnosis_and_candidate_discovery",
    "candidate_count": len(queue_items),
    "symbol_count": 1,
    "symbol_filter": [symbol],
    "dense_option_universe": {
        "start_date": "2026-03-02",
        "end_date": "2026-04-23",
        "min_dte": 0,
        "max_dte": 7,
        "strike_steps": 5,
        "reference_bar": "first",
    },
    "broker_facing": False,
    "live_manifest_effect": "none",
    "risk_policy_effect": "none",
    "promotion_allowed": False,
    "queue_items": queue_items,
}
Path(f"phase38_{symbol}_queue.json").write_text(
    json.dumps(candidate_queue, indent=2), encoding="utf-8"
)
print(f"phase38_symbol_queue symbol={symbol} candidate_count={len(queue_items)}")
if not queue_items:
    raise SystemExit(f"no queue items for {symbol}")
PY

for shard in 01 02 03 04 05 06 07 08 09 10; do
  base="gs://codexalpaca-data-us/research_option_data/${WAVE_ID}/top100_contract_inventory_20260302_20260423_shard_${shard}/silver"
  python3 "$WORK/gcs_io.py" download-prefix "$base/stock_bars" "$COMBINED/stock_bars"
  python3 "$WORK/gcs_io.py" download-prefix "$base/option_contract_inventory" "$COMBINED/option_contract_inventory"
done

cd "$WORK/repo"
python3 -m pip install -e '.[gcp]' google-cloud-secret-manager
export ALPACA_API_KEY="$(python3 "$WORK/read_secret.py" execution-alpaca-paper-api-key)"
export ALPACA_SECRET_KEY="$(python3 "$WORK/read_secret.py" execution-alpaca-paper-secret-key)"
export APCA_API_KEY_ID="$ALPACA_API_KEY"
export APCA_API_SECRET_KEY="$ALPACA_SECRET_KEY"
export ALPACA_PAPER_TRADE=true
export LIVE_TRADING=false
export DRY_RUN=true
export SYMBOL="$SYMBOL"

python3 scripts/build_dense_option_universe.py \
  --stock-bars-path "$COMBINED/stock_bars" \
  --option-contracts-root "$COMBINED/option_contract_inventory" \
  --output-dir "$DENSE_DIR" \
  --symbol-filter "$SYMBOL" \
  --start-date 2026-03-02 \
  --end-date 2026-04-23 \
  --min-dte 0 \
  --max-dte 7 \
  --strike-steps 5 \
  --reference-bar first >> "$RUN_OUT" 2>> "$RUN_ERR"

python3 scripts/download_option_market_data_for_selected_contracts.py \
  --selected-contracts-root "$SELECTED_ROOT" \
  --build-name "$BUILD_NAME" \
  --data-root "$WORK/repo/data" \
  --reports-root "$WORK/repo/reports" \
  --option-batch-size 30 \
  --start-date 2026-03-02 \
  --end-date 2026-04-23 \
  --overwrite >> "$RUN_OUT" 2>> "$RUN_ERR"

for spec in \
  "phase38_lag5_exit10_slip10_fee065 5 10 10 0.65" \
  "phase38_lag10_exit30_slip25_fee100 10 30 25 1.00" \
  "phase38_lag30_exit60_slip50_fee150 30 60 50 1.50"; do
  set -- $spec
  name="$1"; entry_lag="$2"; exit_lag="$3"; slip="$4"; fee="$5"
  python3 scripts/run_option_aware_research_backtest.py \
    --queue-json "$CANDIDATE_QUEUE_JSON" \
    --variants-jsonl "$VARIANTS_JSONL" \
    --stock-bars-path "$COMBINED/stock_bars" \
    --selected-contracts-root "$SELECTED_ROOT" \
    --option-bars-root "$WORK/repo/data/silver/historical/${BUILD_NAME}/option_bars" \
    --option-trades-root "$WORK/repo/data/silver/historical/${BUILD_NAME}/option_trades" \
    --output-dir "$REPLAY_DIR" \
    --run-id "${PHASE_ID}_${SYMBOL}_${name}" \
    --top-n 999 \
    --symbol-filter "$SYMBOL" \
    --skip-blocked-queue-items \
    --contract-selection-method entry_liquidity_first_research_only \
    --test-date-count 5 \
    --initial-cash 25000 \
    --allocation-fraction 0.10 \
    --max-entry-lag-minutes "$entry_lag" \
    --max-exit-lag-minutes "$exit_lag" \
    --slippage-bps "$slip" \
    --fee-per-contract "$fee" >> "$RUN_OUT" 2>> "$RUN_ERR"
done

python3 scripts/build_research_portfolio_report.py \
  --replay-root "$REPLAY_DIR" \
  --output-dir "$PORTFOLIO_DIR" \
  --fill-coverage-gate 0.90 \
  --min-option-trades 20 \
  --min-test-net-pnl 0 \
  --max-positions 4 \
  --max-strategies-per-symbol 2 \
  --max-symbol-weight 0.25 \
  --initial-cash 25000 >> "$RUN_OUT" 2>> "$RUN_ERR"

python3 scripts/build_research_promotion_review_packet.py \
  --portfolio-report-json "$PORTFOLIO_DIR/research_portfolio_report.json" \
  --output-dir "$PROMOTION_DIR" \
  --max-review-candidates 10 >> "$RUN_OUT" 2>> "$RUN_ERR"

echo "phase38_worker_done $(date -Iseconds) symbol=${SYMBOL}"
