$python = 'C:\Users\rabisaab\AppData\Local\Programs\Python\Python312\python.exe'
$root = 'C:\Users\rabisaab\Downloads\qqq_options_30d_cleanroom'
$script = Join-Path $root 'queue_bundle_candidate_batch.py'
$bundleDir = 'C:\Users\rabisaab\OneDrive - First American Corporation\qqq_options_30d_cleanroom\output'
$researchDir = Join-Path $root 'output\candidate_batch_research_20260419_quality6_followon'
$successFile = Join-Path $root 'output\candidate_batch_research_20260418_fresh6_followon\master_summary.json'

Set-Location $root

& $python $script `
  --tickers 'gme,upro,ura,nugt,uco,yinn' `
  --bundle-output-dir $bundleDir `
  --research-dir $researchDir `
  --wait-for-pid 44156 `
  --poll-seconds 60 `
  --wait-for-success-file $successFile
