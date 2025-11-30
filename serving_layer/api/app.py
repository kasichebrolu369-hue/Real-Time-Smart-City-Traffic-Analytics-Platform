"""
FastAPI Application for Serving Layer
Provides REST APIs to query both real-time and historical traffic data
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import redis
import json
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import uvicorn


# Pydantic models for API responses
class Location(BaseModel):
    latitude: float
    longitude: float
    road_name: str
    intersection: str
    city_zone: str


class RealTimeMetrics(BaseModel):
    avg_speed: float
    avg_vehicles: float
    avg_occupancy: float
    congestion_percentage: float
    last_update: str


class HistoricalStats(BaseModel):
    road_name: str
    city_zone: str
    avg_vehicle_count: float
    avg_speed: float
    total_vehicles: int
    congestion_rate: float
    accident_count: int


class AccidentAlert(BaseModel):
    sensor_id: str
    road_name: str
    intersection: str
    latitude: float
    longitude: float
    timestamp: str
    severity: str
    alert_type: str


class CongestionHotspot(BaseModel):
    sensor_id: str
    road_name: str
    intersection: str
    severe_congestion_count: int
    avg_speed_during_congestion: float
    avg_occupancy_during_congestion: float


class PredictionResult(BaseModel):
    road_name: str
    predicted_speed: float
    predicted_vehicles: int
    confidence: float
    timestamp: str


# Initialize FastAPI app
app = FastAPI(
    title="Smart City Traffic Analytics API",
    description="Lambda Architecture API for real-time and historical traffic data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database connections
class DatabaseManager:
    """Manage connections to Redis and Cassandra"""
    
    def __init__(self):
        self.redis_client = None
        self.cassandra_session = None
        
    def connect_redis(self, host: str = "localhost", port: int = 6379):
        """Connect to Redis for real-time data"""
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                decode_responses=True,
                socket_timeout=5
            )
            self.redis_client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            
    def connect_cassandra(self, hosts: List[str] = ["localhost"]):
        """Connect to Cassandra for historical data"""
        try:
            cluster = Cluster(hosts)
            self.cassandra_session = cluster.connect()
            print("✅ Connected to Cassandra")
        except Exception as e:
            print(f"❌ Cassandra connection failed: {e}")
    
    def close(self):
        """Close all connections"""
        if self.cassandra_session:
            self.cassandra_session.shutdown()


# Global database manager
db_manager = DatabaseManager()


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    db_manager.connect_redis()
    db_manager.connect_cassandra()


@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown"""
    db_manager.close()


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Smart City Traffic Analytics API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


# Real-time traffic endpoints
@app.get("/api/v1/traffic/realtime", 
         response_model=Dict[str, RealTimeMetrics],
         tags=["Real-Time Traffic"])
async def get_realtime_traffic(
    road_name: Optional[str] = Query(None, description="Filter by road name"),
    city_zone: Optional[str] = Query(None, description="Filter by city zone")
):
    """Get real-time traffic data from Redis"""
    
    if not db_manager.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Get all real-time keys
        pattern = "traffic:realtime:*"
        keys = db_manager.redis_client.keys(pattern)
        
        results = {}
        for key in keys:
            road = key.split(":")[-1]
            
            # Apply filters
            if road_name and road_name.lower() not in road.lower():
                continue
                
            data = db_manager.redis_client.get(key)
            if data:
                metrics = json.loads(data)
                
                # Apply zone filter if specified
                if city_zone:
                    # Would need zone info in Redis key or value
                    pass
                
                results[road] = RealTimeMetrics(**metrics)
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching real-time data: {str(e)}")


@app.get("/api/v1/traffic/realtime/{road_name}",
         response_model=RealTimeMetrics,
         tags=["Real-Time Traffic"])
async def get_realtime_by_road(road_name: str):
    """Get real-time traffic for a specific road"""
    
    if not db_manager.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        key = f"traffic:realtime:{road_name}"
        data = db_manager.redis_client.get(key)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No real-time data for {road_name}")
        
        metrics = json.loads(data)
        return RealTimeMetrics(**metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/traffic/congestion",
         tags=["Real-Time Traffic"])
async def get_current_congestion():
    """Get all currently congested roads"""
    
    if not db_manager.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        pattern = "traffic:realtime:*"
        keys = db_manager.redis_client.keys(pattern)
        
        congested_roads = []
        
        for key in keys:
            data = db_manager.redis_client.get(key)
            if data:
                metrics = json.loads(data)
                if metrics.get('congestion_percentage', 0) > 50:
                    road = key.split(":")[-1]
                    congested_roads.append({
                        "road_name": road,
                        "congestion_percentage": metrics['congestion_percentage'],
                        "avg_speed": metrics['avg_speed'],
                        "avg_occupancy": metrics['avg_occupancy']
                    })
        
        # Sort by congestion level
        congested_roads.sort(key=lambda x: x['congestion_percentage'], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(congested_roads),
            "congested_roads": congested_roads
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Historical analytics endpoints
@app.get("/api/v1/analytics/road-statistics",
         tags=["Historical Analytics"])
async def get_road_statistics(
    road_name: Optional[str] = None,
    city_zone: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Get historical road statistics from batch processing"""
    
    # Simulate response (would query Cassandra or Parquet files)
    return {
        "message": "Historical analytics endpoint",
        "note": "Would query batch layer results (Parquet/Cassandra)",
        "parameters": {
            "road_name": road_name,
            "city_zone": city_zone,
            "limit": limit
        }
    }


@app.get("/api/v1/analytics/hotspots",
         tags=["Historical Analytics"])
async def get_accident_hotspots(
    top_n: int = Query(10, ge=1, le=100),
    risk_level: Optional[str] = Query(None, regex="^(Critical|High|Moderate|Low)$")
):
    """Get accident hotspot locations"""
    
    return {
        "message": "Accident hotspots endpoint",
        "note": "Would query batch layer hotspot detection results",
        "parameters": {
            "top_n": top_n,
            "risk_level": risk_level
        }
    }


@app.get("/api/v1/analytics/trends",
         tags=["Historical Analytics"])
async def get_traffic_trends(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    road_name: Optional[str] = None
):
    """Get traffic trends over time"""
    
    return {
        "message": "Traffic trends endpoint",
        "note": "Would query batch layer aggregations",
        "parameters": {
            "start_date": start_date,
            "end_date": end_date,
            "road_name": road_name
        }
    }


@app.get("/api/v1/analytics/peak-hours",
         tags=["Historical Analytics"])
async def get_peak_hours(road_name: Optional[str] = None):
    """Get peak traffic hours"""
    
    return {
        "message": "Peak hours endpoint",
        "note": "Would query batch layer peak hour analysis",
        "parameters": {
            "road_name": road_name
        }
    }


# Alert endpoints
@app.get("/api/v1/alerts/recent",
         tags=["Alerts"])
async def get_recent_alerts(
    alert_type: Optional[str] = Query(None, regex="^(ACCIDENT|SEVERE_CONGESTION|ALL)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """Get recent traffic alerts"""
    
    if not db_manager.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Get alerts from Redis
        alerts_key = "traffic:alerts:recent"
        alerts_data = db_manager.redis_client.lrange(alerts_key, 0, limit - 1)
        
        alerts = []
        for alert_json in alerts_data:
            alert = json.loads(alert_json)
            
            # Filter by type
            if alert_type and alert_type != "ALL":
                if alert.get('alert_type') != alert_type:
                    continue
            
            alerts.append(alert)
        
        return {
            "count": len(alerts),
            "alerts": alerts
        }
        
    except Exception as e:
        return {
            "count": 0,
            "alerts": [],
            "note": "Alerts would come from Kafka stream processing"
        }


# Prediction endpoints
@app.get("/api/v1/predict/traffic",
         tags=["Predictions"])
async def predict_traffic(
    road_name: str,
    hours_ahead: int = Query(1, ge=1, le=24)
):
    """Predict traffic for the next N hours"""
    
    return {
        "message": "Traffic prediction endpoint",
        "note": "Would use ML models to predict future traffic",
        "parameters": {
            "road_name": road_name,
            "hours_ahead": hours_ahead
        }
    }


@app.get("/api/v1/predict/congestion",
         tags=["Predictions"])
async def predict_congestion(
    road_name: str,
    time: str = Query(..., description="Prediction time (HH:MM)")
):
    """Predict congestion probability"""
    
    return {
        "message": "Congestion prediction endpoint",
        "note": "Would use ML models to predict congestion probability",
        "parameters": {
            "road_name": road_name,
            "time": time
        }
    }


# Statistics endpoint
@app.get("/api/v1/stats/summary",
         tags=["Statistics"])
async def get_statistics_summary():
    """Get overall traffic statistics"""
    
    if not db_manager.redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    
    try:
        # Get count of monitored roads
        pattern = "traffic:realtime:*"
        keys = db_manager.redis_client.keys(pattern)
        
        total_congested = 0
        total_roads = len(keys)
        
        speeds = []
        occupancies = []
        
        for key in keys:
            data = db_manager.redis_client.get(key)
            if data:
                metrics = json.loads(data)
                if metrics.get('congestion_percentage', 0) > 50:
                    total_congested += 1
                speeds.append(metrics.get('avg_speed', 0))
                occupancies.append(metrics.get('avg_occupancy', 0))
        
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        avg_occupancy = sum(occupancies) / len(occupancies) if occupancies else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_roads_monitored": total_roads,
            "congested_roads": total_congested,
            "congestion_percentage": (total_congested / total_roads * 100) if total_roads > 0 else 0,
            "average_speed": round(avg_speed, 2),
            "average_occupancy": round(avg_occupancy, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def main():
    """Run the API server"""
    print("=" * 80)
    print("🚀 STARTING TRAFFIC ANALYTICS API SERVER")
    print("=" * 80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
