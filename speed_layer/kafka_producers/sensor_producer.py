"""
Kafka Producer for Real-Time Traffic Sensor Data
Publishes sensor readings to Kafka topics
"""

import json
import time
import sys
from pathlib import Path
from kafka import KafkaProducer
from kafka.errors import KafkaError
import argparse
from dataclasses import asdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from data_generator.sensor_simulator import SensorSimulator


class TrafficSensorProducer:
    """Produces real-time traffic sensor data to Kafka"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092", 
                 topic: str = "traffic-events"):
        self.topic = topic
        self.producer = self._create_producer(bootstrap_servers)
        self.simulator = SensorSimulator(num_sensors=50)
        
        # Add construction zones
        self.simulator.add_construction_zone("SENSOR_005")
        self.simulator.add_construction_zone("SENSOR_023")
        
    def _create_producer(self, bootstrap_servers: str) -> KafkaProducer:
        """Create Kafka producer with JSON serialization"""
        return KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            compression_type='gzip',
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=5,
            batch_size=16384,
            linger_ms=10,
            buffer_memory=33554432
        )
    
    def send_event(self, event: dict):
        """Send a single event to Kafka"""
        try:
            # Use sensor_id as key for partitioning
            future = self.producer.send(
                self.topic,
                key=event['sensor_id'],
                value=event
            )
            
            # Get metadata (optional, for debugging)
            # record_metadata = future.get(timeout=10)
            # print(f"Sent to {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
            
            return True
        except KafkaError as e:
            print(f"❌ Error sending event: {e}")
            return False
    
    def start_stream(self, duration_seconds: int = None, 
                    events_per_second: int = 10):
        """Start streaming sensor data"""
        print("=" * 80)
        print("🚀 TRAFFIC SENSOR KAFKA PRODUCER")
        print("=" * 80)
        print(f"📡 Kafka Topic: {self.topic}")
        print(f"📍 Total Sensors: {len(self.simulator.sensors)}")
        print(f"📊 Events/Second: {events_per_second}")
        print(f"⏱️  Duration: {'Continuous' if duration_seconds is None else f'{duration_seconds}s'}")
        print("=" * 80)
        
        start_time = time.time()
        total_events = 0
        total_success = 0
        
        try:
            while True:
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break
                
                cycle_start = time.time()
                
                # Generate readings for random sensors
                batch = self.simulator.generate_batch(num_readings=events_per_second)
                
                # Send to Kafka
                for event in batch:
                    if self.send_event(event):
                        total_success += 1
                    total_events += 1
                
                # Flush to ensure delivery
                self.producer.flush()
                
                # Status update every 10 seconds
                if total_events % (events_per_second * 10) == 0:
                    elapsed = time.time() - start_time
                    rate = total_events / elapsed if elapsed > 0 else 0
                    print(f"📊 Sent: {total_events:,} events | "
                          f"Rate: {rate:.1f} events/sec | "
                          f"Success: {total_success}/{total_events}")
                
                # Maintain rate
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, 1.0 - cycle_time)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n⚠️  Interrupted by user")
        finally:
            self.producer.close()
            
            elapsed = time.time() - start_time
            print("\n" + "=" * 80)
            print("✅ PRODUCER STOPPED")
            print(f"📊 Total Events: {total_events:,}")
            print(f"✔️  Successful: {total_success:,}")
            print(f"❌ Failed: {total_events - total_success:,}")
            print(f"⏱️  Duration: {elapsed:.1f}s")
            print(f"📈 Average Rate: {total_events/elapsed:.1f} events/sec")
            print("=" * 80)
    
    def create_topics(self):
        """Create required Kafka topics"""
        from kafka.admin import KafkaAdminClient, NewTopic
        
        admin_client = KafkaAdminClient(
            bootstrap_servers="localhost:9092",
            client_id='traffic-admin'
        )
        
        topics = [
            NewTopic(name="traffic-events", num_partitions=6, replication_factor=1),
            NewTopic(name="traffic-alerts", num_partitions=3, replication_factor=1),
            NewTopic(name="traffic-aggregates", num_partitions=3, replication_factor=1)
        ]
        
        try:
            admin_client.create_topics(new_topics=topics, validate_only=False)
            print("✅ Topics created successfully")
        except Exception as e:
            print(f"⚠️  Topics might already exist: {e}")
        finally:
            admin_client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Real-time traffic sensor data producer for Kafka"
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="traffic-events",
        help="Kafka topic name (default: traffic-events)"
    )
    parser.add_argument(
        "--events-per-second",
        type=int,
        default=10,
        help="Number of events to generate per second (default: 10)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Duration in seconds (default: continuous)"
    )
    parser.add_argument(
        "--create-topics",
        action="store_true",
        help="Create Kafka topics before starting"
    )
    
    args = parser.parse_args()
    
    producer = TrafficSensorProducer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic
    )
    
    if args.create_topics:
        producer.create_topics()
    
    producer.start_stream(
        duration_seconds=args.duration,
        events_per_second=args.events_per_second
    )


if __name__ == "__main__":
    main()
