# GCP Execution VM Validation Status

## Snapshot

- Generated at: `2026-04-23T14:31:32.040343-04:00`
- Project ID: `codexalpaca`
- VM name: `vm-execution-paper-01`
- Zone: `us-east1-b`
- Expected static IP: `34.139.193.220`

## Validation Script

- Local path: `C:\Users\rabisaab\Downloads\CodexAlpacaTest-TradeMigratyion\output\gcp_execution_vm_validation\execution_vm_validation_vm-execution-paper-01_20260423.sh`
- Control bucket URI: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase3-validation/execution_vm_validation_vm-execution-paper-01_20260423.sh`
- Runtime bootstrap script URI: `gs://codexalpaca-control-us/bootstrap/2026-04-23/foundation-phase2-runtime/execution_vm_runtime_bootstrap_vm-execution-paper-01_20260423.sh`

## Operator Commands

- IAP SSH: `gcloud compute ssh vm-execution-paper-01 --project codexalpaca --zone us-east1-b --tunnel-through-iap`
- On-VM validation fetch/run:
```bash
TOKEN=$(curl -fsS -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
OBJECT='bootstrap/2026-04-23/foundation-phase3-validation/execution_vm_validation_vm-execution-paper-01_20260423.sh'
ENCODED_OBJECT=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$OBJECT")
curl -fsS -H "Authorization: Bearer $TOKEN" "https://storage.googleapis.com/storage/v1/b/codexalpaca-control-us/o/$ENCODED_OBJECT?alt=media" -o /tmp/execution_vm_validation.sh
bash /tmp/execution_vm_validation.sh
```

## Validation Gate

- `Observed VM external IP matches the reserved execution static IP.`
- `Runtime bootstrap script completes successfully.`
- `scripts/doctor.py --skip-connectivity --json completes and reports paper-only lock compatibility.`
- `python -m pytest -q exits 0.`
- `/var/lib/codexalpaca/validation/validation_status.json exists on the VM.`

## Next Actions

- Connect to the VM through OS Login and IAP.
- Run the published validation script on the VM.
- Inspect /var/lib/codexalpaca/validation/validation_status.json and pytest.log on the VM.
- Only after this gate is clean should the next step move toward a trusted validation session.
