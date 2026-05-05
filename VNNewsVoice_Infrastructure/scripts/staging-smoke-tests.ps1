param(
    [string]$GatewayBaseUrl = $env:GATEWAY_BASE_URL,
    [string]$RagHealthUrl = $env:RAG_HEALTH_URL,
    [string]$RabbitMqApiUrl = $env:RABBITMQ_API_URL,
    [string]$RabbitMqUser = $env:RABBITMQ_USER,
    [string]$RabbitMqPassword = $env:RABBITMQ_PASSWORD,
    [int]$TimeoutSec = 15
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($GatewayBaseUrl)) {
    Write-Error "GATEWAY_BASE_URL is required."
    exit 2
}

if ([string]::IsNullOrWhiteSpace($RagHealthUrl)) {
    $RagHealthUrl = "$GatewayBaseUrl/api/v1/health"
}

$results = @()

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Detail
    )

    $script:results += [pscustomobject]@{
        Check  = $Name
        Result = if ($Passed) { "PASS" } else { "FAIL" }
        Detail = $Detail
    }
}

function Invoke-Check {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    try {
        & $Action
    }
    catch {
        Add-Result -Name $Name -Passed $false -Detail $_.Exception.Message
    }
}

Invoke-Check -Name "Gateway health" -Action {
    $resp = Invoke-WebRequest -Uri "$GatewayBaseUrl/health" -Method GET -TimeoutSec $TimeoutSec
    if ($resp.StatusCode -eq 200 -and $resp.Content -match "ok") {
        Add-Result -Name "Gateway health" -Passed $true -Detail "HTTP 200"
    }
    else {
        Add-Result -Name "Gateway health" -Passed $false -Detail "Unexpected response"
    }
}

Invoke-Check -Name "Auth JWKS" -Action {
    $jwks = Invoke-RestMethod -Uri "$GatewayBaseUrl/api/.well-known/jwks.json" -Method GET -TimeoutSec $TimeoutSec
    if ($null -ne $jwks.keys -and $jwks.keys.Count -ge 1) {
        Add-Result -Name "Auth JWKS" -Passed $true -Detail "keys=$($jwks.keys.Count)"
    }
    else {
        Add-Result -Name "Auth JWKS" -Passed $false -Detail "Missing JWKS keys"
    }
}

Invoke-Check -Name "RAG health" -Action {
    $rag = Invoke-RestMethod -Uri $RagHealthUrl -Method GET -TimeoutSec $TimeoutSec
    if ($null -ne $rag.status) {
        Add-Result -Name "RAG health" -Passed $true -Detail "status=$($rag.status)"
    }
    else {
        Add-Result -Name "RAG health" -Passed $true -Detail "HTTP OK"
    }
}

if (-not [string]::IsNullOrWhiteSpace($RabbitMqApiUrl)) {
    if ([string]::IsNullOrWhiteSpace($RabbitMqUser) -or [string]::IsNullOrWhiteSpace($RabbitMqPassword)) {
        Add-Result -Name "RabbitMQ API" -Passed $false -Detail "RABBITMQ_USER/RABBITMQ_PASSWORD required when RABBITMQ_API_URL is set"
    }
    else {
        Invoke-Check -Name "RabbitMQ API" -Action {
            $raw = [Text.Encoding]::ASCII.GetBytes("$RabbitMqUser`:$RabbitMqPassword")
            $b64 = [Convert]::ToBase64String($raw)
            $headers = @{ Authorization = "Basic $b64" }
            $overview = Invoke-RestMethod -Uri "$RabbitMqApiUrl/api/overview" -Headers $headers -Method GET -TimeoutSec $TimeoutSec
            if ($null -ne $overview.rabbitmq_version) {
                Add-Result -Name "RabbitMQ API" -Passed $true -Detail "version=$($overview.rabbitmq_version)"
            }
            else {
                Add-Result -Name "RabbitMQ API" -Passed $false -Detail "No rabbitmq_version field"
            }
        }
    }
}
else {
    Add-Result -Name "RabbitMQ API" -Passed $true -Detail "Skipped (RABBITMQ_API_URL not set)"
}

$results | Format-Table -AutoSize

$failed = ($results | Where-Object { $_.Result -eq "FAIL" }).Count
if ($failed -gt 0) {
    Write-Error "Smoke tests failed: $failed check(s)."
    exit 1
}

Write-Host "All smoke tests passed."
exit 0
