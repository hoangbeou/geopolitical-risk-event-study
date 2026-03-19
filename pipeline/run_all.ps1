$ErrorActionPreference = "Stop"

function Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Info "Repo root: $root"

# Prefer python launcher on Windows
$python = "python"

function RunStep($name, $path) {
  if (-not (Test-Path $path)) {
    Warn "Skip: $name (missing: $path)"
    return
  }
  Info "Running: $name -> $path"
  & $python $path
}

Info "00) Ingest: download + merge raw data"
RunStep "download_and_merge_data" "pipeline\00_ingest\download_and_merge_data.py"

Info "02) Detect events (GPR spikes/high-period)"
RunStep "detect_events" "pipeline\02_event_detection\detect_events.py"

Info "03) Enrich events with Wikipedia locations"
RunStep "enrich_events_with_locations" "pipeline\03_enrichment\enrich_events_with_locations.py"

Info "03) Map locations to regions"
RunStep "map_locations_to_region" "pipeline\03_enrichment\map_locations_to_region.py"

Info "03) Classify events ACT vs THREAT"
RunStep "classify_act_threat" "pipeline\03_enrichment\classify_act_threat.py"

Info "04) Run event study"
RunStep "run_event_study" "pipeline\04_event_study\run_event_study.py"

Info "05) Analysis: top events"
RunStep "show_top_events" "pipeline\05_analysis\show_top_events.py"

Info "05) Analysis: insights ACT vs THREAT"
RunStep "generate_act_threat_insights" "pipeline\05_analysis\generate_act_threat_insights.py"

Info "05) Analysis: advanced insights"
RunStep "generate_advanced_insights" "pipeline\05_analysis\generate_advanced_insights.py"

Info "06) Reporting: generate result tables"
RunStep "generate_results_tables" "pipeline\06_reporting\generate_results_tables.py"

Info "Done."

