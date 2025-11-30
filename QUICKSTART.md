# 🚀 Quick Start Guide

## Complete Setup in 5 Minutes

### Prerequisites Checklist
- ✅ Windows 10/11
- ✅ Python 3.9 or higher
- ✅ Docker Desktop installed and running
- ✅ 16GB RAM minimum
- ✅ 50GB free disk space

### Step 1: Initial Setup

```powershell
# Navigate to project directory
cd "b:\Data Science Projects(Own)\Lamda_archite"

# Run setup script
.\scripts\setup.ps1
```

This script will:
- Create Python virtual environment
- Install all dependencies
- Start Docker services (Kafka, Cassandra, Redis, Spark, etc.)
- Create necessary directories

### Step 2: Generate Sample Data

```powershell
# Generate 30 days of historical data
python scripts\generate_historical_data.py --days 30
```

This creates synthetic traffic data for testing the batch layer.

### Step 3: Test Individual Components

#### Test Data Generator
```powershell
# Test the sensor simulator
python data_generator\sensor_simulator.py
```

#### Test Kafka Producer
```powershell
# Start producing real-time events
python speed_layer\kafka_producers\sensor_producer.py --events-per-second 10 --duration 60
```

#### Test API Server
```powershell
# Start the serving layer API
python serving_layer\api\app.py
```

Then visit: http://localhost:5000/docs

### Step 4: Run Complete System

```powershell
# Start all services at once
.\scripts\start_services.ps1
```

This opens 3-4 terminal windows:
1. Kafka Producer (generating events)
2. Spark Streaming (processing events)
3. API Server (serving data)
4. Dashboard (automatically opens in browser)

### Step 5: View Results

Open the dashboard: `dashboards\frontend\index.html`

Or access API endpoints:
- Statistics: http://localhost:5000/api/v1/stats/summary
- Real-time traffic: http://localhost:5000/api/v1/traffic/realtime
- Congestion: http://localhost:5000/api/v1/traffic/congestion

### Step 6: Stop Everything

```powershell
.\scripts\stop_services.ps1
```

---

## 🎯 Component Testing

### Batch Layer Only

```powershell
# 1. Generate historical data
python scripts\generate_historical_data.py --days 7

# 2. Run daily aggregation
spark-submit batch_layer\spark_jobs\daily_aggregation.py `
  --input-path "data\raw\historical" `
  --output-path "data\batch"

# 3. Run hotspot detection
spark-submit batch_layer\spark_jobs\hotspot_detection.py `
  --input-path "data\raw\historical" `
  --output-path "data\batch"
```

### Speed Layer Only

```powershell
# Terminal 1: Start Kafka producer
python speed_layer\kafka_producers\sensor_producer.py

# Terminal 2: Start Spark streaming (console output)
python speed_layer\streaming_jobs\spark_streaming.py --output-mode console
```

### Serving Layer Only

```powershell
# Start API server
python serving_layer\api\app.py

# Test endpoints
curl http://localhost:5000/api/v1/stats/summary
```

---

## 📊 Training ML Models

```powershell
# Train prediction models
python ml_models\training\traffic_predictor.py
```

Models will be saved to: `ml_models\models/`

---

## 🐛 Troubleshooting

### Docker Services Not Starting
```powershell
# Check Docker status
docker ps

# Restart Docker Desktop
# Then run:
docker-compose up -d
```

### Port Already in Use
```powershell
# Check what's using port 9092 (Kafka)
netstat -ano | findstr :9092

# Kill the process (replace PID)
taskkill /PID <process_id> /F
```

### Python Packages Missing
```powershell
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Kafka Connection Issues
```powershell
# Verify Kafka is running
docker logs kafka

# Test Kafka connection
python -c "from kafka import KafkaProducer; print('OK')"
```

---

## 🔄 Development Workflow

### Making Changes

1. **Data Generator Changes**
   - Edit: `data_generator\sensor_simulator.py`
   - Test: `python data_generator\sensor_simulator.py`

2. **Batch Processing Changes**
   - Edit: `batch_layer\spark_jobs\*.py`
   - Test: `spark-submit batch_layer\spark_jobs\<your_job>.py`

3. **Streaming Changes**
   - Edit: `speed_layer\streaming_jobs\*.py`
   - Restart: Stop and start the streaming job

4. **API Changes**
   - Edit: `serving_layer\api\app.py`
   - Auto-reload: FastAPI has hot-reload enabled

5. **Dashboard Changes**
   - Edit: `dashboards\frontend\index.html`
   - Refresh: Just reload the browser

### Running Tests

```powershell
# Run all tests
pytest tests\

# Run specific test file
pytest tests\test_batch_layer.py

# Run with coverage
pytest --cov=. tests\
```

---

## 📈 Monitoring

### Docker Services
```powershell
# View all running containers
docker-compose ps

# View logs
docker-compose logs -f kafka
docker-compose logs -f spark-master
docker-compose logs -f cassandra
```

### Application Logs
- Check terminal windows where services are running
- Or redirect to log files:
  ```powershell
  python serving_layer\api\app.py > logs\api.log 2>&1
  ```

### Metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 💡 Usage Examples

### Example 1: Generate and Process 1 Day of Data

```powershell
# Generate
python scripts\generate_historical_data.py --days 1

# Process
spark-submit batch_layer\spark_jobs\daily_aggregation.py `
  --input-path "data\raw\historical" `
  --output-path "data\batch" `
  --date "2024-11-30"
```

### Example 2: Stream for 5 Minutes

```powershell
# Terminal 1
python speed_layer\kafka_producers\sensor_producer.py --duration 300

# Terminal 2
python speed_layer\streaming_jobs\spark_streaming.py --output-mode redis

# Terminal 3
python serving_layer\api\app.py

# Open dashboard to see real-time updates
```

### Example 3: Full Lambda Pipeline Test

```powershell
# 1. Historical data (batch layer)
python scripts\generate_historical_data.py --days 7
spark-submit batch_layer\spark_jobs\daily_aggregation.py `
  --input-path "data\raw\historical" `
  --output-path "data\batch"

# 2. Real-time data (speed layer)
# Start in separate terminals:
python speed_layer\kafka_producers\sensor_producer.py
python speed_layer\streaming_jobs\spark_streaming.py --output-mode redis

# 3. Serve merged view (serving layer)
python serving_layer\api\app.py

# 4. View in dashboard
start dashboards\frontend\index.html
```

---

## 🎓 Learning Path

### Day 1: Understand Components
- Read README.md
- Explore data_generator
- Generate sample data
- View generated JSON files

### Day 2: Batch Layer
- Run daily aggregation job
- Run hotspot detection
- View Parquet outputs
- Understand aggregations

### Day 3: Speed Layer
- Start Kafka producer
- Start Spark streaming
- Monitor console output
- Check Redis for results

### Day 4: Serving Layer
- Start API server
- Explore API documentation
- Test endpoints with curl/Postman
- Understand data merging

### Day 5: Complete Integration
- Run full pipeline
- Monitor all components
- View dashboard
- Make customizations

---

## 📚 Additional Resources

- **Spark Documentation**: https://spark.apache.org/docs/latest/
- **Kafka Documentation**: https://kafka.apache.org/documentation/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Lambda Architecture**: http://lambda-architecture.net/

---

## 🤝 Getting Help

1. Check logs in terminal windows
2. Verify all Docker containers are running: `docker ps`
3. Check if ports are available
4. Review error messages carefully
5. Ensure virtual environment is activated

---

**Ready to start? Run `.\scripts\setup.ps1` and you're good to go! 🚀**
