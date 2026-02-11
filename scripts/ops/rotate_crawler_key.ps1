param(
  [string]$CloudApiUrl = "https://ai-job-hunter-production-2730.up.railway.app",
  [string]$CrawlerEnvPath = "crawler.env"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[1/4] Generate new CRAWLER_API_KEY..."
$newKey = python -c "import secrets; print(secrets.token_urlsafe(32))"

Write-Host "[2/4] Update Railway variable (linked project/service)..."
railway variable set ("CRAWLER_API_KEY=" + $newKey) | Out-Null

Write-Host "[3/4] Rebuild latest deployment..."
railway redeploy -y | Out-Null

Write-Host "[4/4] Write local crawler.env..."
$content = @"
# Local crawler config (not committed)
CLOUD_API_URL=$CloudApiUrl
CRAWLER_API_KEY=$newKey
CRAWL_INTERVAL_HOURS=6
OPENCLAW_JOB_SITES=boss
"@
[System.IO.File]::WriteAllText((Resolve-Path .).Path + "\" + $CrawlerEnvPath, $content, (New-Object System.Text.UTF8Encoding($false)))

Write-Host "Done."
Write-Host "New key prefix: $($newKey.Substring(0,8))..."
Write-Host "crawler env: $CrawlerEnvPath"

