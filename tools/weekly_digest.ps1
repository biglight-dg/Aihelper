# Weekly AI news digest. Keep this file ASCII-only for Windows PowerShell 5.1.
$ErrorActionPreference = "Stop"
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$env:PYTHONIOENCODING = "utf-8"

$proj = Split-Path $PSScriptRoot -Parent
$logDir = Join-Path $proj "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$log = Join-Path $logDir "weekly_digest.log"
$python = Join-Path $proj ".venv\Scripts\python.exe"
$codex = Get-Command codex -ErrorAction SilentlyContinue

if (-not (Test-Path $python)) { throw "Missing Python venv: $python" }
if ($null -eq $codex) { throw "codex CLI not found on PATH" }

Set-Location $proj
"`n===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') weekly digest start =====" | Out-File -FilePath $log -Append -Encoding utf8

$prompt = @'
Read AGENTS.md, then create the weekly AI news digest in Korean.
Use .venv\Scripts\python.exe for Python.
Run tools.news.collect_news(), then tools.news.build_digest_source(7).
Choose 3 key stories and enrich only those from primary/reliable sources.
For each key story, write several concise paragraphs and one reflection question.
Add about 10 short items with 1-2 sentence blurbs, plus skills and study topics.
Build the documented digest dict and call tools.news.save_digest(digest, ids).
Do not modify tracked source files. Report the 3 selected stories at the end.
'@

$previousPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$prompt | & $codex.Path --search exec -m gpt-5.4-mini -c 'model_reasoning_effort="low"' --cd $proj --dangerously-bypass-approvals-and-sandbox --ephemeral - *>> $log
$code = $LASTEXITCODE
$ErrorActionPreference = $previousPreference
"===== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') done (exit=$code) =====" | Out-File -FilePath $log -Append -Encoding utf8
exit $code
