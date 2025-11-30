"""
Real-time Traffic Sensor Data Generator
Generates synthetic traffic sensor data with realistic patterns, anomalies, and events
"""

import random
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
import math


class VehicleType(Enum):
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"


class WeatherCondition(Enum):
    CLEAR = "clear"
    RAIN = "rain"
    SNOW = "snow"
    FOG = "fog"
    STORM = "storm"


class RoadCondition(Enum):
    DRY = "dry"
    WET = "wet"
    ICY = "icy"
    CONSTRUCTION = "construction"


@dataclass
class Location:
    latitude: float
    longitude: float
    road_name: str
    intersection: str
    city_zone: str
    postal_code: str


@dataclass
class TrafficMetrics:
    vehicle_count: int
    avg_speed_mph: float
    lane_occupancy: float
    vehicle_types: Dict[str, int]
    queue_length: int
    flow_rate: float  # vehicles per minute


@dataclass
class Conditions:
    weather: str
    visibility: str  # good, moderate, poor
    road_condition: str
    temperature_f: float
    humidity: float


@dataclass
class Anomalies:
    is_congested: bool
    is_accident: bool
    is_construction: bool
    is_special_event: bool
    congestion_level: str  # none, light, moderate, heavy, severe


@dataclass
class TrafficSensorEvent:
    sensor_id: str
    timestamp: str
    location: Location
    metrics: TrafficMetrics
    conditions: Conditions
    anomalies: Anomalies
    event_id: str


class TrafficPatternGenerator:
    """Generate realistic traffic patterns based on time of day and day of week"""
    
    def __init__(self):
        # Base traffic multipliers by hour of day
        self.hourly_patterns = {
            0: 0.15, 1: 0.10, 2: 0.08, 3: 0.07, 4: 0.10,  # Late night/early morning
            5: 0.25, 6: 0.50, 7: 0.85, 8: 1.00, 9: 0.80,  # Morning rush
            10: 0.65, 11: 0.70, 12: 0.75, 13: 0.72,       # Mid-day
            14: 0.68, 15: 0.75, 16: 0.85, 17: 0.95,       # Afternoon
            18: 1.00, 19: 0.85, 20: 0.65, 21: 0.50,       # Evening rush & wind down
            22: 0.35, 23: 0.22                             # Night
        }
        
        # Day of week multipliers (Mon=0, Sun=6)
        self.daily_patterns = {
            0: 1.00, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.05,  # Weekdays
            5: 0.85, 6: 0.70                               # Weekend
        }
        
    def get_base_traffic_multiplier(self, dt: datetime) -> float:
        """Get traffic multiplier based on time and day"""
        hour_mult = self.hourly_patterns[dt.hour]
        day_mult = self.daily_patterns[dt.weekday()]
        
        # Add some randomness
        random_factor = random.uniform(0.85, 1.15)
        
        return hour_mult * day_mult * random_factor


class SensorSimulator:
    """Simulate traffic sensors across a city"""
    
    def __init__(self, num_sensors: int = 50):
        self.num_sensors = num_sensors
        self.sensors = self._create_sensors()
        self.pattern_generator = TrafficPatternGenerator()
        self.accident_probability = 0.001  # 0.1% chance per reading
        self.construction_zones = set()
        
    def _create_sensors(self) -> List[Dict]:
        """Create virtual sensors at different locations"""
        sensors = []
        
        # City center (high traffic)
        city_center_roads = [
            ("Main Street", "Downtown"),
            ("Broadway", "Downtown"),
            ("5th Avenue", "Downtown"),
            ("Market Street", "Downtown"),
            ("Park Avenue", "Downtown"),
        ]
        
        # Suburban areas (medium traffic)
        suburban_roads = [
            ("Oak Street", "North End"),
            ("Maple Drive", "West Side"),
            ("Elm Avenue", "East Side"),
            ("Cedar Lane", "South Side"),
            ("Pine Road", "Suburbs"),
        ]
        
        # Highway sections (high speed)
        highway_sections = [
            ("I-95 North", "Highway"),
            ("I-95 South", "Highway"),
            ("Route 1 North", "Highway"),
            ("Route 1 South", "Highway"),
        ]
        
        # Distribute sensors
        all_roads = (city_center_roads * 6 + suburban_roads * 4 + 
                    highway_sections * 3)
        
        for i in range(self.num_sensors):
            road_name, zone = random.choice(all_roads)
            
            # Generate coordinates (roughly around NYC area)
            base_lat = 40.7128
            base_lon = -74.0060
            lat = base_lat + random.uniform(-0.1, 0.1)
            lon = base_lon + random.uniform(-0.1, 0.1)
            
            sensor = {
                "sensor_id": f"SENSOR_{i+1:03d}",
                "location": Location(
                    latitude=round(lat, 6),
                    longitude=round(lon, 6),
                    road_name=road_name,
                    intersection=f"{road_name} & {random.choice(['1st', '2nd', '3rd', '4th', '5th'])} St",
                    city_zone=zone,
                    postal_code=f"{10000 + random.randint(1, 999)}"
                ),
                "road_type": "highway" if "Highway" in zone else "city",
                "num_lanes": 4 if "Highway" in zone else random.choice([2, 3, 4]),
                "speed_limit": 65 if "Highway" in zone else random.choice([25, 30, 35, 40])
            }
            sensors.append(sensor)
        
        return sensors
    
    def _calculate_speed(self, base_speed: int, congestion_level: float, 
                        weather: WeatherCondition) -> float:
        """Calculate average speed based on conditions"""
        speed = base_speed
        
        # Reduce speed for congestion
        speed *= (1 - congestion_level * 0.7)
        
        # Weather impact
        weather_impact = {
            WeatherCondition.CLEAR: 1.0,
            WeatherCondition.RAIN: 0.85,
            WeatherCondition.SNOW: 0.60,
            WeatherCondition.FOG: 0.75,
            WeatherCondition.STORM: 0.50
        }
        speed *= weather_impact.get(weather, 1.0)
        
        # Add some variance
        speed *= random.uniform(0.9, 1.1)
        
        return max(5, round(speed, 1))
    
    def _generate_vehicle_mix(self, zone: str, total_vehicles: int) -> Dict[str, int]:
        """Generate realistic vehicle type distribution"""
        if "Highway" in zone:
            # More trucks on highways
            distribution = {
                VehicleType.CAR.value: 0.70,
                VehicleType.TRUCK.value: 0.20,
                VehicleType.BUS.value: 0.05,
                VehicleType.MOTORCYCLE.value: 0.04,
                VehicleType.BICYCLE.value: 0.01
            }
        else:
            # More diverse in city
            distribution = {
                VehicleType.CAR.value: 0.65,
                VehicleType.TRUCK.value: 0.10,
                VehicleType.BUS.value: 0.10,
                VehicleType.MOTORCYCLE.value: 0.08,
                VehicleType.BICYCLE.value: 0.07
            }
        
        vehicle_mix = {}
        remaining = total_vehicles
        
        for vehicle_type, proportion in distribution.items():
            count = int(total_vehicles * proportion)
            vehicle_mix[vehicle_type] = count
            remaining -= count
        
        # Distribute remaining vehicles
        vehicle_mix[VehicleType.CAR.value] += remaining
        
        return vehicle_mix
    
    def _detect_anomalies(self, speed: float, occupancy: float, 
                         sensor: Dict) -> Tuple[bool, bool, str]:
        """Detect traffic anomalies"""
        is_accident = random.random() < self.accident_probability
        is_construction = sensor["sensor_id"] in self.construction_zones
        
        # Congestion detection
        congestion_level = "none"
        is_congested = False
        
        if occupancy > 0.85 or speed < sensor["speed_limit"] * 0.3:
            congestion_level = "severe"
            is_congested = True
        elif occupancy > 0.70 or speed < sensor["speed_limit"] * 0.4:
            congestion_level = "heavy"
            is_congested = True
        elif occupancy > 0.55 or speed < sensor["speed_limit"] * 0.5:
            congestion_level = "moderate"
            is_congested = True
        elif occupancy > 0.40 or speed < sensor["speed_limit"] * 0.65:
            congestion_level = "light"
        
        # Accidents cause severe congestion
        if is_accident:
            is_congested = True
            congestion_level = "severe"
        
        return is_congested, is_accident, congestion_level
    
    def generate_reading(self, sensor: Dict, dt: datetime = None) -> TrafficSensorEvent:
        """Generate a single sensor reading"""
        if dt is None:
            dt = datetime.now()
        
        # Get base traffic level
        traffic_multiplier = self.pattern_generator.get_base_traffic_multiplier(dt)
        
        # Calculate vehicles based on road capacity
        max_vehicles_per_minute = sensor["num_lanes"] * 30
        base_vehicles = int(max_vehicles_per_minute * traffic_multiplier)
        vehicle_count = max(0, base_vehicles + random.randint(-10, 10))
        
        # Weather conditions
        weather_weights = [0.70, 0.15, 0.05, 0.05, 0.05]
        weather = random.choices(list(WeatherCondition), weights=weather_weights)[0]
        
        # Road conditions
        if weather == WeatherCondition.SNOW:
            road_condition = random.choice([RoadCondition.WET, RoadCondition.ICY])
        elif weather == WeatherCondition.RAIN:
            road_condition = RoadCondition.WET
        else:
            road_condition = RoadCondition.DRY
        
        # Check for construction
        if sensor["sensor_id"] in self.construction_zones:
            road_condition = RoadCondition.CONSTRUCTION
        
        # Lane occupancy (0-1)
        lane_occupancy = min(1.0, vehicle_count / (sensor["num_lanes"] * 40))
        lane_occupancy = round(lane_occupancy, 2)
        
        # Calculate speed
        congestion_factor = min(lane_occupancy * 1.2, 1.0)
        avg_speed = self._calculate_speed(
            sensor["speed_limit"], 
            congestion_factor, 
            weather
        )
        
        # Detect anomalies
        is_congested, is_accident, congestion_level = self._detect_anomalies(
            avg_speed, lane_occupancy, sensor
        )
        
        # Generate vehicle mix
        vehicle_types = self._generate_vehicle_mix(
            sensor["location"].city_zone, 
            vehicle_count
        )
        
        # Create event
        event = TrafficSensorEvent(
            sensor_id=sensor["sensor_id"],
            timestamp=dt.isoformat() + "Z",
            location=sensor["location"],
            metrics=TrafficMetrics(
                vehicle_count=vehicle_count,
                avg_speed_mph=avg_speed,
                lane_occupancy=lane_occupancy,
                vehicle_types=vehicle_types,
                queue_length=int(lane_occupancy * sensor["num_lanes"] * 10),
                flow_rate=round(vehicle_count / 1.0, 2)
            ),
            conditions=Conditions(
                weather=weather.value,
                visibility="poor" if weather in [WeatherCondition.FOG, WeatherCondition.STORM] 
                          else "moderate" if weather == WeatherCondition.RAIN 
                          else "good",
                road_condition=road_condition.value,
                temperature_f=round(random.uniform(20, 85), 1),
                humidity=round(random.uniform(30, 90), 1)
            ),
            anomalies=Anomalies(
                is_congested=is_congested,
                is_accident=is_accident,
                is_construction=sensor["sensor_id"] in self.construction_zones,
                is_special_event=False,  # Can be enhanced
                congestion_level=congestion_level
            ),
            event_id=str(uuid.uuid4())
        )
        
        return event
    
    def add_construction_zone(self, sensor_id: str):
        """Mark a sensor location as having construction"""
        self.construction_zones.add(sensor_id)
    
    def remove_construction_zone(self, sensor_id: str):
        """Remove construction from a sensor location"""
        self.construction_zones.discard(sensor_id)
    
    def generate_batch(self, num_readings: int = 100, 
                      dt: datetime = None) -> List[Dict]:
        """Generate multiple readings (one per sensor)"""
        if dt is None:
            dt = datetime.now()
        
        readings = []
        for sensor in random.sample(self.sensors, min(num_readings, len(self.sensors))):
            event = self.generate_reading(sensor, dt)
            readings.append(asdict(event))
        
        return readings
    
    def generate_stream(self, duration_seconds: int = 60, 
                       readings_per_second: int = 10):
        """Generate continuous stream of readings"""
        print(f"🚦 Starting traffic sensor stream for {duration_seconds} seconds...")
        print(f"📊 Generating {readings_per_second} readings per second")
        
        start_time = time.time()
        total_readings = 0
        
        while time.time() - start_time < duration_seconds:
            cycle_start = time.time()
            
            # Generate readings for this cycle
            sensors_to_read = random.sample(
                self.sensors, 
                min(readings_per_second, len(self.sensors))
            )
            
            for sensor in sensors_to_read:
                event = self.generate_reading(sensor)
                event_dict = asdict(event)
                
                # Print or yield the event
                print(json.dumps(event_dict, indent=2))
                total_readings += 1
                
                # In production, this would publish to Kafka
                # producer.send('traffic-events', event_dict)
            
            # Sleep to maintain rate
            cycle_time = time.time() - cycle_start
            sleep_time = max(0, 1.0 - cycle_time)
            time.sleep(sleep_time)
        
        print(f"\n✅ Generated {total_readings} total readings")


def main():
    """Main execution"""
    simulator = SensorSimulator(num_sensors=50)
    
    # Add some construction zones
    simulator.add_construction_zone("SENSOR_005")
    simulator.add_construction_zone("SENSOR_023")
    
    print("=" * 80)
    print("🌆 SMART CITY TRAFFIC SENSOR SIMULATOR")
    print("=" * 80)
    print(f"📍 Total Sensors: {len(simulator.sensors)}")
    print(f"🚧 Construction Zones: {len(simulator.construction_zones)}")
    print("=" * 80)
    
    # Generate sample batch
    print("\n📦 SAMPLE BATCH READING:")
    print("-" * 80)
    sample_event = simulator.generate_reading(simulator.sensors[0])
    print(json.dumps(asdict(sample_event), indent=2))
    
    print("\n" + "=" * 80)
    print("🔄 STARTING CONTINUOUS STREAM")
    print("=" * 80)
    
    # Generate stream (run for 60 seconds)
    # simulator.generate_stream(duration_seconds=60, readings_per_second=10)


if __name__ == "__main__":
    main()
