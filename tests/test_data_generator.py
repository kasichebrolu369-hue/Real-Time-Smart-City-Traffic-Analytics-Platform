"""
Unit tests for data generator
"""

import pytest
from datetime import datetime
from data_generator.sensor_simulator import (
    SensorSimulator, TrafficPatternGenerator, 
    WeatherCondition, RoadCondition
)


def test_sensor_simulator_creation():
    """Test sensor simulator initialization"""
    simulator = SensorSimulator(num_sensors=10)
    assert len(simulator.sensors) == 10
    assert simulator.accident_probability == 0.001


def test_traffic_pattern_generator():
    """Test traffic pattern generation"""
    generator = TrafficPatternGenerator()
    
    # Test rush hour (8 AM weekday)
    dt = datetime(2024, 11, 27, 8, 0)  # Wednesday
    multiplier = generator.get_base_traffic_multiplier(dt)
    assert multiplier > 0.5  # Should be high during rush hour
    
    # Test late night (2 AM)
    dt = datetime(2024, 11, 27, 2, 0)
    multiplier = generator.get_base_traffic_multiplier(dt)
    assert multiplier < 0.3  # Should be low at night


def test_generate_reading():
    """Test generating a single sensor reading"""
    simulator = SensorSimulator(num_sensors=5)
    sensor = simulator.sensors[0]
    
    event = simulator.generate_reading(sensor)
    
    assert event.sensor_id == sensor["sensor_id"]
    assert event.metrics.vehicle_count >= 0
    assert 0 <= event.metrics.avg_speed_mph <= 100
    assert 0 <= event.metrics.lane_occupancy <= 1.0
    assert event.event_id is not None


def test_generate_batch():
    """Test generating batch of readings"""
    simulator = SensorSimulator(num_sensors=20)
    batch = simulator.generate_batch(num_readings=10)
    
    assert len(batch) == 10
    assert all('sensor_id' in event for event in batch)


def test_construction_zone():
    """Test construction zone management"""
    simulator = SensorSimulator(num_sensors=5)
    sensor_id = "SENSOR_001"
    
    simulator.add_construction_zone(sensor_id)
    assert sensor_id in simulator.construction_zones
    
    simulator.remove_construction_zone(sensor_id)
    assert sensor_id not in simulator.construction_zones


def test_vehicle_type_distribution():
    """Test vehicle type distribution is reasonable"""
    simulator = SensorSimulator(num_sensors=5)
    sensor = simulator.sensors[0]
    
    event = simulator.generate_reading(sensor)
    vehicle_types = event.metrics.vehicle_types
    
    total = sum(vehicle_types.values())
    assert total == event.metrics.vehicle_count
    assert vehicle_types['car'] > 0  # Should always have cars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
