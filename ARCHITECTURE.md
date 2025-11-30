# 🏗️ Architecture Documentation

## System Overview

The Smart City Traffic Analytics Platform implements the **Lambda Architecture** pattern to process both real-time and historical traffic data, providing a unified view through the serving layer.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                 │
│                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│  │   Sensor    │  │   Sensor    │  │   Sensor    │                │
│  │  Device 1   │  │  Device 2   │  │  Device N   │                │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│         │                 │                 │                        │
│         └─────────────────┴─────────────────┘                        │
│                           │                                          │
└───────────────────────────┼──────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BATCH LAYER (Master Data)                         │
│                                                                       │
│  ┌──────────────┐         ┌───────────────┐      ┌──────────────┐ │
│  │   Raw Data   │ ──────► │ Spark Batch   │ ───► │ Batch Views  │ │
│  │  (HDFS/S3)   │         │   Processing  │      │  (Parquet)   │ │
│  └──────────────┘         └───────────────┘      └──────────────┘ │
│                                                                       │
│  Jobs:                                                               │
│  • Daily Aggregation        • Traffic Patterns                      │
│  • Hotspot Detection        • Trend Analysis                        │
│  • Vehicle Distribution     • Weather Impact                        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   SPEED LAYER (Real-Time)                            │
│                                                                       │
│  ┌──────────────┐    ┌────────────────┐    ┌──────────────────┐   │
│  │    Kafka     │───►│ Spark Streaming │───►│  Real-Time Views │   │
│  │  (Events)    │    │   / Flink       │    │  (Redis/Cass.)   │   │
│  └──────────────┘    └────────────────┘    └──────────────────┘   │
│                                                                       │
│  Processing:                                                         │
│  • Live Traffic Speed       • Congestion Detection                  │
│  • Accident Alerts          • Anomaly Detection                     │
│  • Lane Occupancy           • Flow Rate Analysis                    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SERVING LAYER                                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Query Processor & Data Merger                    │  │
│  │                                                                │  │
│  │  ┌──────────────┐  +  ┌──────────────┐  =  ┌─────────────┐ │  │
│  │  │ Batch Views  │     │ Speed Views  │     │   Merged    │ │  │
│  │  │ (Historical) │     │ (Real-Time)  │     │    View     │ │  │
│  │  └──────────────┘     └──────────────┘     └─────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────┐         ┌───────────────┐                        │
│  │  REST API    │         │   GraphQL     │                        │
│  │  (FastAPI)   │         │   (Optional)  │                        │
│  └──────┬───────┘         └───────┬───────┘                        │
└─────────┼───────────────────────────┼──────────────────────────────┘
          │                           │
          ▼                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                               │
│                                                                       │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐          │
│  │   Dashboard   │  │   Superset    │  │   Grafana     │          │
│  │   (HTML/JS)   │  │      BI       │  │  Monitoring   │          │
│  └───────────────┘  └───────────────┘  └───────────────┘          │
│                                                                       │
│  ┌───────────────┐  ┌───────────────┐                              │
│  │ Mobile App    │  │ External APIs │                              │
│  │  (Future)     │  │  (Public)     │                              │
│  └───────────────┘  └───────────────┘                              │
└───────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. Batch Layer (λ)

**Purpose**: Process complete historical dataset to generate accurate views

**Components**:
- **Storage**: HDFS / Local File System / S3
- **Processing**: Apache Spark (PySpark)
- **Output**: Parquet files with aggregated results

**Jobs**:

1. **Daily Aggregation** (`daily_aggregation.py`)
   - Hourly vehicle counts by road
   - Average speeds and occupancy
   - Congestion statistics
   - Peak hour identification

2. **Hotspot Detection** (`hotspot_detection.py`)
   - Accident frequency analysis
   - Risk score calculation
   - Temporal pattern analysis
   - Weather correlation

3. **Traffic Patterns** (Future)
   - Weekly/monthly trends
   - Seasonal variations
   - Event impact analysis

**Schedule**: Daily batch jobs (typically overnight)

**Latency**: Hours (acceptable for historical analysis)

---

### 2. Speed Layer (κ)

**Purpose**: Process recent data in real-time for low-latency views

**Components**:
- **Message Queue**: Apache Kafka
- **Stream Processing**: Spark Structured Streaming / Apache Flink
- **Storage**: Redis (cache) + Cassandra (persistent)

**Processing**:

1. **Kafka Producer** (`sensor_producer.py`)
   - Ingest sensor readings
   - Publish to Kafka topics
   - Handle batching and compression

2. **Spark Streaming** (`spark_streaming.py`)
   - 30-second micro-batches
   - Real-time aggregations
   - Anomaly detection
   - Alert generation

**Features**:
- Congestion detection (< 5s latency)
- Accident alerts
- Live speed monitoring
- Lane occupancy tracking

**Latency**: < 5 seconds end-to-end

---

### 3. Serving Layer (σ)

**Purpose**: Merge batch and speed layers to serve unified queries

**Components**:
- **API Framework**: FastAPI
- **Cache**: Redis
- **Database**: Cassandra / PostgreSQL
- **Search**: Elasticsearch (optional)

**API Endpoints**:

```
Real-Time:
  GET  /api/v1/traffic/realtime
  GET  /api/v1/traffic/congestion
  POST /api/v1/traffic/alerts

Historical:
  GET  /api/v1/analytics/road-statistics
  GET  /api/v1/analytics/hotspots
  GET  /api/v1/analytics/trends
  GET  /api/v1/analytics/peak-hours

Predictions:
  GET  /api/v1/predict/traffic
  GET  /api/v1/predict/congestion
```

**Query Resolution**:
1. Check Redis for recent data (< 5 minutes old)
2. Query Cassandra for recent history (< 7 days)
3. Query Parquet files for historical data (> 7 days)
4. Merge results and return

---

## Data Flow

### Batch Path

```
Sensors → JSON Files → HDFS/Storage
                         ↓
                    Spark Batch Jobs
                         ↓
                    Parquet Files
                         ↓
                    Serving Layer
```

**Characteristics**:
- High throughput
- Complete accuracy
- Immutable data
- Recomputable views

### Speed Path

```
Sensors → Kafka Topics → Spark Streaming
                              ↓
                         Redis/Cassandra
                              ↓
                         Serving Layer
```

**Characteristics**:
- Low latency
- Approximate results
- Incremental updates
- Compensates for batch delay

### Merged View

```
Query → Serving Layer
            ↓
    ┌───────┴────────┐
    ↓                ↓
Batch View      Speed View
    ↓                ↓
    └───────┬────────┘
            ↓
      Merged Result
```

---

## Technology Stack Details

### Data Storage

| Component | Technology | Purpose | TTL |
|-----------|-----------|---------|-----|
| Raw Data | JSON/Parquet | Source of truth | Permanent |
| Batch Views | Parquet | Historical aggregates | Permanent |
| Speed Views | Redis | Real-time cache | 5 minutes |
| Speed Persistent | Cassandra | Recent history | 7 days |
| Metadata | PostgreSQL | System metadata | Permanent |

### Processing

| Layer | Technology | Use Case |
|-------|-----------|----------|
| Batch | Apache Spark | Large-scale batch processing |
| Stream | Spark Streaming | Real-time micro-batching |
| Stream Alt | Apache Flink | Alternative stream processor |
| Orchestration | Airflow (Future) | Job scheduling |

### Serving

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API | FastAPI | REST endpoints |
| Cache | Redis | Fast lookups |
| Database | Cassandra | Distributed storage |
| Search | Elasticsearch | Full-text search |

---

## Scalability Considerations

### Horizontal Scaling

**Batch Layer**:
- Add more Spark executors
- Increase HDFS data nodes
- Partition data by date/sensor

**Speed Layer**:
- Increase Kafka partitions
- Add Spark streaming executors
- Scale Redis cluster

**Serving Layer**:
- Deploy multiple API instances
- Use load balancer (nginx/HAProxy)
- Scale Cassandra ring

### Vertical Scaling

- Increase executor memory (Spark)
- Increase broker memory (Kafka)
- Increase cache size (Redis)

---

## Fault Tolerance

### Batch Layer
- HDFS replication (3x default)
- Spark task retry
- Checkpointing for long jobs

### Speed Layer
- Kafka replication
- Spark Structured Streaming checkpoints
- Redis persistence (AOF/RDB)

### Serving Layer
- Cassandra replication
- API instance redundancy
- Graceful degradation (serve batch view if speed fails)

---

## Monitoring & Observability

### Metrics Collection
- Prometheus for metrics
- Grafana for visualization
- ELK stack for logs (optional)

### Key Metrics

**Batch Layer**:
- Job execution time
- Records processed
- Error rate

**Speed Layer**:
- Processing latency (p50, p95, p99)
- Kafka lag
- Event throughput

**Serving Layer**:
- API response time
- Request rate
- Error rate
- Cache hit ratio

---

## Security

### Authentication
- API key authentication
- JWT tokens
- OAuth2 (future)

### Authorization
- Role-based access control (RBAC)
- Service-to-service auth

### Data Protection
- TLS/SSL in transit
- Encryption at rest (optional)
- PII anonymization

---

## Future Enhancements

1. **ML Integration**
   - Traffic prediction models
   - Anomaly detection with ML
   - Route optimization

2. **Advanced Analytics**
   - Graph analytics (Neo4j)
   - Time-series forecasting
   - What-if simulations

3. **Real-Time Optimization**
   - Apache Flink for sub-second latency
   - Event sourcing with Kafka Streams
   - CQRS pattern

4. **Extended Coverage**
   - Weather integration
   - Public transit data
   - Parking availability
   - Air quality sensors

---

## References

- [Lambda Architecture](http://lambda-architecture.net/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Kafka Streams](https://kafka.apache.org/documentation/streams/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
