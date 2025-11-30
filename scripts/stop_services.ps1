# PowerShell script to stop all services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stopping Traffic Analytics Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Stop Docker services
Write-Host ""
Write-Host "Stopping Docker services..." -ForegroundColor Yellow
docker-compose down
Write-Host "✓ Docker services stopped" -ForegroundColor Green

# Kill Python processes (if any are still running)
Write-Host ""
Write-Host "Checking for running Python processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Host "  Found $($pythonProcesses.Count) Python process(es)" -ForegroundColor Gray
    Write-Host "  Please close them manually or they will be terminated" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Uncomment to force kill
    # Stop-Process -Name python -Force
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Services Stopped" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
