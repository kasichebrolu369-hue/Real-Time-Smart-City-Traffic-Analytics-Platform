# PowerShell script to set up the Lambda Architecture Traffic Analytics Platform

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Smart City Traffic Analytics Platform" -ForegroundColor Cyan
Write-Host "Lambda Architecture Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check if Docker is installed
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists" -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip | Out-Null
Write-Host "✓ Pip upgraded" -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
pip install -r requirements.txt | Out-Null
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Create necessary directories
Write-Host ""
Write-Host "Creating directory structure..." -ForegroundColor Yellow
$directories = @(
    "data\raw\historical",
    "data\processed",
    "data\batch",
    "data\streaming",
    "ml_models\models",
    "logs",
    "checkpoints"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "✓ Directory structure created" -ForegroundColor Green

# Start Docker services
Write-Host ""
Write-Host "Starting Docker services..." -ForegroundColor Yellow
Write-Host "  This will start Kafka, Cassandra, Redis, Spark, etc." -ForegroundColor Gray
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host "✓ Services should be starting" -ForegroundColor Green

# Display service URLs
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Spark Master:     http://localhost:8080" -ForegroundColor White
Write-Host "  API Server:       http://localhost:5000" -ForegroundColor White
Write-Host "  Dashboard:        http://localhost:8080/index.html" -ForegroundColor White
Write-Host "  Superset:         http://localhost:8088" -ForegroundColor White
Write-Host "  Grafana:          http://localhost:3000" -ForegroundColor White
Write-Host "  Prometheus:       http://localhost:9090" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. Generate historical data:" -ForegroundColor White
Write-Host "   python scripts\generate_historical_data.py --days 90" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run batch processing:" -ForegroundColor White
Write-Host "   spark-submit batch_layer\spark_jobs\daily_aggregation.py ..." -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start Kafka producer:" -ForegroundColor White
Write-Host "   python speed_layer\kafka_producers\sensor_producer.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Start Spark streaming:" -ForegroundColor White
Write-Host "   python speed_layer\streaming_jobs\spark_streaming.py" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Start API server:" -ForegroundColor White
Write-Host "   python serving_layer\api\app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "6. Open dashboard in browser:" -ForegroundColor White
Write-Host "   dashboards\frontend\index.html" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
