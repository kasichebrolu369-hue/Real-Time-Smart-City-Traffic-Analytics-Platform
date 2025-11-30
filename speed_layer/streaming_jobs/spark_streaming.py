"""
Spark Structured Streaming for Real-Time Traffic Analytics
Processes Kafka stream and detects congestion/accidents in real-time
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_json, struct, window, 
    avg, count, max, min, sum, when, lit, expr,
    current_timestamp, unix_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, BooleanType, MapType, TimestampType
)
import argparse


class RealTimeTrafficProcessor:
    """Process traffic events in real-time using Spark Streaming"""
    
    def __init__(self, kafka_bootstrap: str = "localhost:9092",
                 input_topic: str = "traffic-events",
                 output_topic: str = "traffic-aggregates",
                 alert_topic: str = "traffic-alerts",
                 checkpoint_dir: str = "/tmp/spark-checkpoint"):
        
        self.kafka_bootstrap = kafka_bootstrap
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.alert_topic = alert_topic
        self.checkpoint_dir = checkpoint_dir
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self):
        """Create Spark session with Kafka support"""
        return (SparkSession.builder
                .appName("RealTimeTrafficAnalytics")
                .config("spark.jars.packages", 
                       "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
                .config("spark.sql.streaming.checkpointLocation", self.checkpoint_dir)
                .config("spark.sql.shuffle.partitions", "6")
                .getOrCreate())
    
    def _define_schema(self):
        """Define schema for incoming traffic events"""
        return StructType([
            StructField("sensor_id", StringType()),
            StructField("timestamp", StringType()),
            StructField("location", StructType([
                StructField("latitude", DoubleType()),
                StructField("longitude", DoubleType()),
                StructField("road_name", StringType()),
                StructField("intersection", StringType()),
                StructField("city_zone", StringType()),
                StructField("postal_code", StringType())
            ])),
            StructField("metrics", StructType([
                StructField("vehicle_count", IntegerType()),
                StructField("avg_speed_mph", DoubleType()),
                StructField("lane_occupancy", DoubleType()),
                StructField("vehicle_types", MapType(StringType(), IntegerType())),
                StructField("queue_length", IntegerType()),
                StructField("flow_rate", DoubleType())
            ])),
            StructField("conditions", StructType([
                StructField("weather", StringType()),
                StructField("visibility", StringType()),
                StructField("road_condition", StringType()),
                StructField("temperature_f", DoubleType()),
                StructField("humidity", DoubleType())
            ])),
            StructField("anomalies", StructType([
                StructField("is_congested", BooleanType()),
                StructField("is_accident", BooleanType()),
                StructField("is_construction", BooleanType()),
                StructField("is_special_event", BooleanType()),
                StructField("congestion_level", StringType())
            ])),
            StructField("event_id", StringType())
        ])
    
    def read_kafka_stream(self):
        """Read streaming data from Kafka"""
        return (self.spark
                .readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", self.kafka_bootstrap)
                .option("subscribe", self.input_topic)
                .option("startingOffsets", "latest")
                .option("failOnDataLoss", "false")
                .load())
    
    def parse_events(self, kafka_df):
        """Parse JSON events from Kafka"""
        schema = self._define_schema()
        
        return (kafka_df
                .selectExpr("CAST(value AS STRING) as json_value")
                .select(from_json(col("json_value"), schema).alias("data"))
                .select("data.*")
                .withColumn("processing_time", current_timestamp()))
    
    def compute_realtime_aggregates(self, events_df):
        """Compute real-time aggregates with 30-second windows"""
        
        aggregates = (events_df
            .withWatermark("processing_time", "1 minute")
            .groupBy(
                window(col("processing_time"), "30 seconds"),
                col("location.road_name").alias("road_name"),
                col("location.city_zone").alias("city_zone")
            )
            .agg(
                count("*").alias("event_count"),
                avg("metrics.avg_speed_mph").alias("avg_speed"),
                avg("metrics.vehicle_count").alias("avg_vehicles"),
                avg("metrics.lane_occupancy").alias("avg_occupancy"),
                max("metrics.lane_occupancy").alias("max_occupancy"),
                sum(when(col("anomalies.is_congested"), 1).otherwise(0)).alias("congestion_count"),
                sum(when(col("anomalies.is_accident"), 1).otherwise(0)).alias("accident_count")
            )
            .withColumn("congestion_percentage", 
                       (col("congestion_count") / col("event_count") * 100))
        )
        
        return aggregates
    
    def detect_accidents(self, events_df):
        """Detect and alert on accidents"""
        
        accidents = (events_df
            .filter(col("anomalies.is_accident") == True)
            .select(
                col("sensor_id"),
                col("timestamp"),
                col("location.road_name").alias("road_name"),
                col("location.intersection").alias("intersection"),
                col("location.latitude").alias("latitude"),
                col("location.longitude").alias("longitude"),
                col("metrics.avg_speed_mph").alias("speed"),
                col("metrics.vehicle_count").alias("vehicles"),
                lit("ACCIDENT").alias("alert_type"),
                lit("CRITICAL").alias("severity"),
                current_timestamp().alias("alert_time")
            )
        )
        
        return accidents
    
    def detect_severe_congestion(self, events_df):
        """Detect severe congestion events"""
        
        congestion = (events_df
            .filter(col("anomalies.congestion_level") == "severe")
            .select(
                col("sensor_id"),
                col("timestamp"),
                col("location.road_name").alias("road_name"),
                col("location.intersection").alias("intersection"),
                col("location.latitude").alias("latitude"),
                col("location.longitude").alias("longitude"),
                col("metrics.avg_speed_mph").alias("speed"),
                col("metrics.vehicle_count").alias("vehicles"),
                col("metrics.lane_occupancy").alias("occupancy"),
                lit("SEVERE_CONGESTION").alias("alert_type"),
                lit("HIGH").alias("severity"),
                current_timestamp().alias("alert_time")
            )
        )
        
        return congestion
    
    def write_to_kafka(self, df, topic: str):
        """Write results back to Kafka"""
        
        return (df
            .select(to_json(struct("*")).alias("value"))
            .writeStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_bootstrap)
            .option("topic", topic)
            .option("checkpointLocation", f"{self.checkpoint_dir}/{topic}")
            .outputMode("append")
            .start())
    
    def write_to_console(self, df, query_name: str):
        """Write results to console for debugging"""
        
        return (df
            .writeStream
            .format("console")
            .outputMode("complete" if "window" in df.columns else "append")
            .option("truncate", False)
            .option("numRows", 20)
            .queryName(query_name)
            .start())
    
    def write_to_cassandra(self, df, keyspace: str, table: str):
        """Write results to Cassandra"""
        
        return (df
            .writeStream
            .format("org.apache.spark.sql.cassandra")
            .option("keyspace", keyspace)
            .option("table", table)
            .option("checkpointLocation", f"{self.checkpoint_dir}/cassandra_{table}")
            .outputMode("append")
            .start())
    
    def write_to_redis(self, df, redis_host: str = "localhost", redis_port: int = 6379):
        """Write real-time metrics to Redis"""
        
        def write_to_redis_batch(batch_df, batch_id):
            """Write each batch to Redis"""
            import redis
            import json
            
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            
            for row in batch_df.collect():
                key = f"traffic:realtime:{row['road_name']}"
                value = json.dumps({
                    'avg_speed': row['avg_speed'],
                    'avg_vehicles': row['avg_vehicles'],
                    'avg_occupancy': row['avg_occupancy'],
                    'congestion_percentage': row['congestion_percentage'],
                    'last_update': str(row['window']['end'])
                })
                
                # Set with expiration (5 minutes)
                r.setex(key, 300, value)
        
        return (df
            .writeStream
            .foreachBatch(write_to_redis_batch)
            .option("checkpointLocation", f"{self.checkpoint_dir}/redis")
            .start())
    
    def run(self, output_mode: str = "console"):
        """Run the streaming application"""
        
        print("=" * 80)
        print("⚡ REAL-TIME TRAFFIC ANALYTICS - SPARK STREAMING")
        print("=" * 80)
        print(f"📥 Input Topic: {self.input_topic}")
        print(f"📤 Output Topic: {self.output_topic}")
        print(f"🚨 Alert Topic: {self.alert_topic}")
        print(f"💾 Checkpoint: {self.checkpoint_dir}")
        print(f"🎯 Output Mode: {output_mode}")
        print("=" * 80)
        
        # Read from Kafka
        print("\n📡 Reading from Kafka...")
        kafka_df = self.read_kafka_stream()
        
        # Parse events
        print("🔍 Parsing events...")
        events_df = self.parse_events(kafka_df)
        
        # Compute aggregates
        print("📊 Computing real-time aggregates...")
        aggregates = self.compute_realtime_aggregates(events_df)
        
        # Detect accidents
        print("🚨 Setting up accident detection...")
        accidents = self.detect_accidents(events_df)
        
        # Detect congestion
        print("🚦 Setting up congestion detection...")
        congestion = self.detect_severe_congestion(events_df)
        
        # Start queries based on output mode
        queries = []
        
        if output_mode == "console":
            queries.append(self.write_to_console(aggregates, "aggregates"))
            queries.append(self.write_to_console(accidents, "accidents"))
            queries.append(self.write_to_console(congestion, "congestion"))
        
        elif output_mode == "kafka":
            queries.append(self.write_to_kafka(aggregates, self.output_topic))
            queries.append(self.write_to_kafka(accidents, self.alert_topic))
            queries.append(self.write_to_kafka(congestion, self.alert_topic))
        
        elif output_mode == "redis":
            queries.append(self.write_to_redis(aggregates))
            queries.append(self.write_to_console(accidents, "accidents"))
            queries.append(self.write_to_console(congestion, "congestion"))
        
        print("\n✅ Streaming queries started!")
        print("⏳ Processing events... (Press Ctrl+C to stop)\n")
        
        # Wait for termination
        try:
            for query in queries:
                query.awaitTermination()
        except KeyboardInterrupt:
            print("\n⚠️  Stopping queries...")
            for query in queries:
                query.stop()
            print("✅ All queries stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Real-time traffic analytics with Spark Streaming"
    )
    parser.add_argument(
        "--kafka-bootstrap",
        type=str,
        default="localhost:9092",
        help="Kafka bootstrap servers"
    )
    parser.add_argument(
        "--input-topic",
        type=str,
        default="traffic-events",
        help="Input Kafka topic"
    )
    parser.add_argument(
        "--output-topic",
        type=str,
        default="traffic-aggregates",
        help="Output Kafka topic"
    )
    parser.add_argument(
        "--alert-topic",
        type=str,
        default="traffic-alerts",
        help="Alert Kafka topic"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="/tmp/spark-checkpoint",
        help="Checkpoint directory"
    )
    parser.add_argument(
        "--output-mode",
        type=str,
        default="console",
        choices=["console", "kafka", "redis"],
        help="Output mode: console, kafka, or redis"
    )
    
    args = parser.parse_args()
    
    processor = RealTimeTrafficProcessor(
        kafka_bootstrap=args.kafka_bootstrap,
        input_topic=args.input_topic,
        output_topic=args.output_topic,
        alert_topic=args.alert_topic,
        checkpoint_dir=args.checkpoint_dir
    )
    
    processor.run(output_mode=args.output_mode)


if __name__ == "__main__":
    main()
