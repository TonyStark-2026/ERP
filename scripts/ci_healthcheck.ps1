Param(
    [int]$wait = 0,
    [switch]$RunTests
)

$healthUrl = 'http://127.0.0.1:8000/docs'

if ($wait -gt 0) {
    Write-Host "Waiting up to $wait seconds for $healthUrl ..."
    $t = 0
    while ($t -lt $wait) {
        try {
            Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5 | Out-Null
            Write-Host "Backend is responsive."
            break
        } catch {
            Start-Sleep -Seconds 1
            $t += 1
            Write-Host "Waiting... $t`/ $wait"
        }
    }
    if ($t -ge $wait) {
        Write-Error "Timed out waiting for $healthUrl"
        exit 2
    }
}

if ($RunTests) {
    Write-Host "Running API smoke tests against $healthUrl"
    try {
        $body = '{"name":"CI-Material-PS","description":"ci test","unit_price":5.5}'
        $mat = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/materials/' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 10
        Write-Host "Created material: $($mat | ConvertTo-Json -Depth 5)"
    } catch {
        Write-Error "Create material failed: $_"
        exit 3
    }

    if (-not $mat.id) {
        Write-Error "Material response missing id"
        exit 4
    }

    try {
        $poBody = @{ material_id = $mat.id; quantity = 10 } | ConvertTo-Json
        $po = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/purchase_orders/' -Method Post -ContentType 'application/json' -Body $poBody -TimeoutSec 10
        Write-Host "Created PO: $($po | ConvertTo-Json -Depth 5)"
    } catch {
        Write-Error "Create PO failed: $_"
        exit 5
    }

    Write-Host "Smoke tests passed."
}

exit 0
