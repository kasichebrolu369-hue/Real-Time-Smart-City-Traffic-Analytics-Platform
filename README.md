# ðŸŒ† Real-Time Smart City Traffic Analytics Platform

## Lambda Architecture Implementation for Big Data Processing

![Lambda Architecture](https://img.shields.io/badge/Architecture-Lambda-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Spark](https://img.shields.io/badge/Apache-Spark-orange)
![Kafka](https://img.shields.io/badge/Apache-Kafka-black)

## ðŸ“‹ Project Overview

A comprehensive big data platform that processes city-wide traffic sensor data using **Lambda Architecture** to provide:

- âš¡ **Real-time traffic congestion monitoring**
- ðŸš¨ **Accident detection and alerts**
- ðŸ“Š **Historical traffic pattern analytics**
- ðŸ”® **Predictive traffic modeling**
- ðŸ“ **Interactive dashboards and maps**

## ðŸ— Architecture Components

### 1ï¸âƒ£ Batch Layer (Historical Processing)
- **Storage**: HDFS (Hadoop Distributed File System)
- **Processing**: Apache Spark (PySpark)
- **Format**: Parquet/ORC
- **Frequency**: Daily batch jobs
- **Metrics**:
  - Hourly vehicle counts
  - Average speeds by time of day
  - Accident hotspot identification
  - Long-term traffic trends
  - Peak hour patterns

### 2ï¸âƒ£ Speed Layer (Real-Time Processing)
- **Message Queue**: Apache Kafka
- **Stream Processing**: Spark Streaming / Apache Flink
- **Storage**: Redis + Cassandra
- **Latency**: < 5 seconds
- **Features**:
  - Live speed monitoring
  - Congestion alerts
  - Accident detection
  - Lane occupancy tracking
  - Vehicle type classification

### 3ï¸âƒ£ Serving Layer (Query & API)
- **Database**: Cassandra + Elasticsearch
- **Cache**: Redis
- **API**: Flask/FastAPI REST endpoints
- **BI Integration**: Apache Superset / Grafana
- **Capabilities**:
  - Merged historical + real-time views
  - REST API for external systems
  - Dashboard data feeds
  - Alerting system

## ðŸ—‚ Project Structure

```
Lamda_archite/
â”œâ”€â”€ config/                      # Configuration files
â”‚   â”œâ”€â”€ kafka_config.yaml
â”‚   â”œâ”€â”€ spark_config.yaml
â”‚   â””â”€â”€ cassandra_config.yaml
â”‚
â”œâ”€â”€ data/                        # Data storage
â”‚   â”œâ”€â”€ raw/                     # Raw sensor data
â”‚   â”œâ”€â”€ processed/               # Processed data
â”‚   â”œâ”€â”€ batch/                   # Batch layer outputs
â”‚   â””â”€â”€ streaming/               # Real-time outputs
â”‚
â”œâ”€â”€ batch_layer/                 # Batch processing
â”‚   â”œâ”€â”€ spark_jobs/
â”‚   â”‚   â”œâ”€â”€ daily_aggregation.py
â”‚   â”‚   â”œâ”€â”€ traffic_patterns.py
â”‚   â”‚   â”œâ”€â”€ hotspot_detection.py
â”‚   â”‚   â””â”€â”€ trend_analysis.py
â”‚   â”œâ”€â”€ data_ingestion/
â”‚   â”‚   â””â”€â”€ hdfs_loader.py
â”‚   â””â”€â”€ utils/
â”‚       â””â”€â”€ batch_helpers.py
â”‚
â”œâ”€â”€ speed_layer/                 # Real-time processing
â”‚   â”œâ”€â”€ kafka_producers/
â”‚   â”‚   â””â”€â”€ sensor_producer.py
â”‚   â”œâ”€â”€ streaming_jobs/
â”‚   â”‚   â”œâ”€â”€ spark_streaming.py
â”‚   â”‚   â”œâ”€â”€ flink_processor.py
â”‚   â”‚   â”œâ”€â”€ congestion_detector.py
â”‚   â”‚   â””â”€â”€ accident_detector.py
â”‚   â””â”€â”€ utils/
â”‚       â””â”€â”€ streaming_helpers.py
â”‚
â”œâ”€â”€ serving_layer/               # Query & API layer
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ app.py
â”‚   â”‚   â”œâ”€â”€ routes/
â”‚   â”‚   â”‚   â”œâ”€â”€ traffic.py
â”‚   â”‚   â”‚   â”œâ”€â”€ analytics.py
â”‚   â”‚   â”‚   â””â”€â”€ alerts.py
â”‚   â”‚   â””â”€â”€ models/
â”‚   â”‚       â””â”€â”€ schemas.py
â”‚   â”œâ”€â”€ data_merger/
â”‚   â”‚   â””â”€â”€ view_builder.py
â”‚   â””â”€â”€ cache/
â”‚       â””â”€â”€ redis_manager.py
â”‚
â”œâ”€â”€ ml_models/                   # Machine Learning
â”‚   â”œâ”€â”€ training/
â”‚   â”‚   â”œâ”€â”€ traffic_predictor.py
â”‚   â”‚   â””â”€â”€ anomaly_detector.py
â”‚   â”œâ”€â”€ inference/
â”‚   â”‚   â””â”€â”€ predict_service.py
â”‚   â””â”€â”€ models/                  # Saved models
â”‚
â”œâ”€â”€ data_generator/              # Synthetic data
â”‚   â”œâ”€â”€ sensor_simulator.py
â”‚   â”œâ”€â”€ traffic_patterns.py
â”‚   â””â”€â”€ event_generator.py
â”‚
â”œâ”€â”€ dashboards/                  # Visualization
â”‚   â”œâ”€â”€ frontend/
â”‚   â”‚   â”œâ”€â”€ index.html
â”‚   â”‚   â”œâ”€â”€ css/
â”‚   â”‚   â””â”€â”€ js/
â”‚   â””â”€â”€ superset_config/
â”‚
â”œâ”€â”€ monitoring/                  # System monitoring
â”‚   â”œâ”€â”€ prometheus_config.yaml
â”‚   â””â”€â”€ grafana_dashboards/
â”‚
â”œâ”€â”€ scripts/                     # Utility scripts
â”‚   â”œâ”€â”€ setup.sh
â”‚   â”œâ”€â”€ start_services.sh
â”‚   â”œâ”€â”€ stop_services.sh
â”‚   â””â”€â”€ generate_historical_data.py
â”‚
â”œâ”€â”€ tests/                       # Testing
â”‚   â”œâ”€â”€ test_batch_layer.py
â”‚   â”œâ”€â”€ test_speed_layer.py
â”‚   â””â”€â”€ test_serving_layer.py
â”‚
â”œâ”€â”€ docker/                      # Docker configs
â”‚   â”œâ”€â”€ docker-compose.yml
â”‚   â”œâ”€â”€ Dockerfile.spark
â”‚   â”œâ”€â”€ Dockerfile.kafka
â”‚   â””â”€â”€ Dockerfile.api
â”‚
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ setup.py
â””â”€â”€ README.md
```

## ðŸš€ Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- 16GB RAM minimum
- 50GB disk space

### Installation

1. **Clone and setup environment**
```bash
cd "b:\Data Science Projects(Own)\Lamda_archite"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start infrastructure services**
```bash
docker-compose up -d
```

3. **Generate historical data**
```bash
python scripts/generate_historical_data.py --days 90
```

4. **Start batch processing**
```bash
spark-submit batch_layer/spark_jobs/daily_aggregation.py
```

5. **Start real-time streaming**
```bash
python speed_layer/kafka_producers/sensor_producer.py
python speed_layer/streaming_jobs/spark_streaming.py
```

6. **Start API server**
```bash
python serving_layer/api/app.py
```

7. **Access dashboards**
- API: http://localhost:5000
- Dashboard: http://localhost:8080
- Superset: http://localhost:8088

## ðŸ“Š Data Schema

### Traffic Sensor Event
```json
{
  "sensor_id": "SENSOR_001",
  "timestamp": "2025-11-30T10:30:45.123Z",
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "road_name": "5th Avenue",
    "intersection": "5th Ave & 42nd St"
  },
  "metrics": {
    "vehicle_count": 45,
    "avg_speed_mph": 25.5,
    "lane_occupancy": 0.75,
    "vehicle_types": {
      "car": 35,
      "truck": 5,
      "bus": 3,
      "motorcycle": 2
    }
  },
  "conditions": {
    "weather": "clear",
    "visibility": "good",
    "road_condition": "dry"
  },
  "anomalies": {
    "is_congested": false,
    "is_accident": false,
    "is_construction": false
  }
}
```

## ðŸŽ¯ Key Features

### Real-Time Features
- Live traffic speed monitoring (< 5 sec latency)
- Automatic congestion detection
- Accident alerts with location
- Lane-level occupancy tracking
- Vehicle classification

### Batch Analytics
- Daily/weekly/monthly traffic patterns
- Accident hotspot heatmaps
- Peak hour identification
- Historical trend analysis
- Road segment performance

### Predictive Analytics
- Traffic flow prediction (next 1-4 hours)
- Congestion probability modeling
- Accident risk assessment
- Optimal route suggestions
- Event impact analysis

### Dashboards
- Real-time traffic map
- Historical analytics charts
- Alert management panel
- Prediction visualizations
- System health monitoring

## ðŸ”§ Technology Stack

| Component | Technology |
|-----------|------------|
| **Batch Processing** | Apache Spark, Hadoop HDFS |
| **Stream Processing** | Apache Kafka, Spark Streaming, Flink |
| **Storage** | Cassandra, HDFS, Parquet |
| **Cache** | Redis |
| **Search** | Elasticsearch |
| **API** | FastAPI / Flask |
| **ML** | Scikit-learn, TensorFlow |
| **Visualization** | Apache Superset, Grafana |
| **Monitoring** | Prometheus, Grafana |
| **Orchestration** | Docker, Docker Compose |

## ðŸ“ˆ Performance Metrics

- **Batch Processing**: 10M+ records/hour
- **Stream Processing**: 50K+ events/second
- **API Latency**: < 100ms (p95)
- **End-to-End Latency**: < 5 seconds
- **Data Retention**: 2 years historical
- **Availability**: 99.9% uptime

## ðŸ§ª Testing

```bash
# Run all tests
pytest tests/

# Run specific layer tests
pytest tests/test_batch_layer.py
pytest tests/test_speed_layer.py
pytest tests/test_serving_layer.py

# Run with coverage
pytest --cov=. tests/
```

## ðŸ“š API Documentation

### Endpoints

#### Real-Time Traffic
```
GET  /api/v1/traffic/realtime?sensor_id={id}
GET  /api/v1/traffic/congestion
POST /api/v1/traffic/alerts
```

#### Historical Analytics
```
GET  /api/v1/analytics/patterns?road={road}&date={date}
GET  /api/v1/analytics/hotspots
GET  /api/v1/analytics/trends?start={start}&end={end}
```

#### Predictions
```
GET  /api/v1/predict/traffic?location={loc}&time={time}
GET  /api/v1/predict/congestion?road={road}
```

## ðŸ›  Configuration

Edit configuration files in `config/`:

- `kafka_config.yaml`: Kafka brokers, topics, partitions
- `spark_config.yaml`: Spark master, memory, cores
- `cassandra_config.yaml`: Keyspace, replication, tables

## ðŸ” Security

- API authentication with JWT tokens
- Rate limiting on endpoints
- Input validation and sanitization
- Encrypted data in transit (TLS)
- Role-based access control

## ðŸ“Š Monitoring

Access monitoring dashboards:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

Monitored metrics:
- Kafka lag and throughput
- Spark job performance
- API response times
- Database query performance
- System resource usage

## ðŸ¤ Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## ðŸ“ License

This project is licensed under the MIT License.

## ðŸ‘¥ Authors

- **Kasi Chebrolu** - Initial work and architecture design

## ðŸ™ Acknowledgments

- Apache Software Foundation for Spark, Kafka, Flink
- Lambda Architecture pattern by Nathan Marz
- Smart city traffic data standards

## ðŸ“§ Contact

**Kasi Chebrolu**

Project Link: https://github.com/kasichebrolu/lambda-traffic-analytics

---

**Built with â¤ï¸ for Smart Cities by Kasi Chebrolu**
#   R e a l - T i m e - S m a r t - C i t y - T r a f f i c - A n a l y t i c s - P l a t f o r m  
 