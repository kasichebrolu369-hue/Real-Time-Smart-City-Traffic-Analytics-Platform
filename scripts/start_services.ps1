# PowerShell script to start all services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Traffic Analytics Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Check Docker services
Write-Host ""
Write-Host "Checking Docker services..." -ForegroundColor Yellow
$services = docker-compose ps --services --filter "status=running"
if ($services) {
    Write-Host "✓ Docker services running" -ForegroundColor Green
} else {
    Write-Host "Starting Docker services..." -ForegroundColor Yellow
    docker-compose up -d
    Start-Sleep -Seconds 30
}

# Start Kafka producer in background
Write-Host ""
Write-Host "Starting Kafka producer..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; python speed_layer\kafka_producers\sensor_producer.py --events-per-second 10"
Write-Host "✓ Kafka producer started" -ForegroundColor Green

# Wait a bit
Start-Sleep -Seconds 5

# Start Spark streaming in background
Write-Host ""
Write-Host "Starting Spark streaming..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; python speed_layer\streaming_jobs\spark_streaming.py --output-mode redis"
Write-Host "✓ Spark streaming started" -ForegroundColor Green

# Wait a bit
Start-Sleep -Seconds 5

# Start API server in background
Write-Host ""
Write-Host "Starting API server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& .\venv\Scripts\Activate.ps1; python serving_layer\api\app.py"
Write-Host "✓ API server started" -ForegroundColor Green

# Open dashboard
Start-Sleep -Seconds 3
Write-Host ""
Write-Host "Opening dashboard..." -ForegroundColor Yellow
Start-Process "dashboards\frontend\index.html"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All Services Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access points:" -ForegroundColor White
Write-Host "  Dashboard:  dashboards\frontend\index.html" -ForegroundColor Gray
Write-Host "  API:        http://localhost:5000" -ForegroundColor Gray
Write-Host "  API Docs:   http://localhost:5000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop services" -ForegroundColor Yellow
