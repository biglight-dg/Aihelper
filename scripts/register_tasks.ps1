# Register Aihelper scheduled tasks on ONE automation-owner PC only.
# Keep this file ASCII-only for Windows PowerShell 5.1.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
  -ExecutionTimeLimit (New-TimeSpan -Minutes 45) `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -WakeToRun -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew

function Register-AihelperTask($name, $scriptPath, $time, $description) {
  if (-not (Test-Path $scriptPath)) { throw "Missing script: $scriptPath" }
  $arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
  $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At $time
  Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger `
    -Settings $settings -Description $description -Force | Out-Null
  Write-Host "Registered: $name"
}

Register-AihelperTask "Aihelper-ExpertFeed" `
  (Join-Path $root "tools\expert_feed_sync.ps1") "09:15" `
  "Aihelper YouTube expert RSS sync"
Register-AihelperTask "Aihelper-WeeklyDigest" `
  (Join-Path $root "tools\weekly_digest.ps1") "09:23" `
  "Aihelper weekly AI news digest via Codex"
Register-AihelperTask "Aihelper-SheetsSync" `
  (Join-Path $root "tools\sheets_sync.ps1") "09:40" `
  "Aihelper Google Sheets sync"

Get-ScheduledTask -TaskName "Aihelper-*" |
  Select-Object TaskName,State |
  Format-Table -AutoSize
