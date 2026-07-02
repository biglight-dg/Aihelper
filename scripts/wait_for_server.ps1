param(
    [int]$Port = 8501,
    [int]$TimeoutSeconds = 30
)

$uri = "http://127.0.0.1:$Port/_stcore/health"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200 -and $response.Content.Trim() -eq "ok") {
            exit 0
        }
    } catch {
        # The server is still starting.
    }
    Start-Sleep -Milliseconds 500
}

Write-Error "Timed out waiting for $uri"
exit 1
