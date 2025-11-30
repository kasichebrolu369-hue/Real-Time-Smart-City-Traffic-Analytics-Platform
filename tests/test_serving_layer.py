"""
Unit tests for serving layer API
"""

import pytest
from fastapi.testclient import TestClient
from serving_layer.api.app import app

client = TestClient(app)


def test_health_check():
    """Test root health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_stats_summary():
    """Test statistics summary endpoint"""
    response = client.get("/api/v1/stats/summary")
    assert response.status_code in [200, 503]  # 503 if Redis not available


def test_realtime_traffic():
    """Test real-time traffic endpoint"""
    response = client.get("/api/v1/traffic/realtime")
    assert response.status_code in [200, 503]


def test_congestion_endpoint():
    """Test congestion endpoint"""
    response = client.get("/api/v1/traffic/congestion")
    assert response.status_code in [200, 503]


def test_recent_alerts():
    """Test recent alerts endpoint"""
    response = client.get("/api/v1/alerts/recent")
    assert response.status_code in [200, 503]


def test_invalid_endpoint():
    """Test invalid endpoint returns 404"""
    response = client.get("/api/v1/invalid/endpoint")
    assert response.status_code == 404


def test_api_docs():
    """Test API documentation is available"""
    response = client.get("/docs")
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
