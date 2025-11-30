"""
Daily Traffic Aggregation Batch Job
Processes historical traffic data and computes daily aggregations
"""

from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, avg, sum, count, max, min, hour, dayofweek, 
    when, lit, window, to_timestamp, expr, stddev, percentile_approx
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DoubleType, TimestampType, BooleanType, MapType
)
from datetime import datetime, timedelta
import argparse
import sys


class DailyAggregationJob:
    """Spark batch job for daily traffic aggregations"""
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self) -> SparkSession:
        """Create and configure Spark session"""
        return (SparkSession.builder
                .appName("DailyTrafficAggregation")
                .config("spark.sql.adaptive.enabled", "true")
                .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
                .config("spark.sql.parquet.compression.codec", "snappy")
                .getOrCreate())
    
    def _define_schema(self) -> StructType:
        """Define schema for traffic events"""
        return StructType([
            StructField("sensor_id", StringType(), False),
            StructField("timestamp", StringType(), False),
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
    
    def load_data(self, date: str = None):
        """Load traffic data for processing"""
        schema = self._define_schema()
        
        if date:
            input_file = f"{self.input_path}/traffic_{date}.json"
            df = self.spark.read.schema(schema).json(input_file)
        else:
            df = self.spark.read.schema(schema).json(f"{self.input_path}/*.json")
        
        # Convert timestamp to proper format
        df = df.withColumn("timestamp", to_timestamp(col("timestamp"), 
                                                     "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"))
        
        return df
    
    def compute_hourly_aggregations(self, df):
        """Compute hourly traffic statistics"""
        hourly_agg = (df
            .withColumn("hour", hour(col("timestamp")))
            .withColumn("day_of_week", dayofweek(col("timestamp")))
            .groupBy(
                "sensor_id",
                col("location.road_name").alias("road_name"),
                col("location.city_zone").alias("city_zone"),
                "hour",
                "day_of_week"
            )
            .agg(
                count("*").alias("num_readings"),
                avg("metrics.vehicle_count").alias("avg_vehicle_count"),
                sum("metrics.vehicle_count").alias("total_vehicles"),
                avg("metrics.avg_speed_mph").alias("avg_speed"),
                min("metrics.avg_speed_mph").alias("min_speed"),
                max("metrics.avg_speed_mph").alias("max_speed"),
                stddev("metrics.avg_speed_mph").alias("speed_stddev"),
                avg("metrics.lane_occupancy").alias("avg_occupancy"),
                max("metrics.lane_occupancy").alias("max_occupancy"),
                avg("metrics.flow_rate").alias("avg_flow_rate"),
                sum(when(col("anomalies.is_congested"), 1).otherwise(0)).alias("congestion_count"),
                sum(when(col("anomalies.is_accident"), 1).otherwise(0)).alias("accident_count"),
                expr("percentile_approx(metrics.avg_speed_mph, 0.5)").alias("median_speed"),
                expr("percentile_approx(metrics.vehicle_count, 0.95)").alias("p95_vehicle_count")
            )
        )
        
        # Calculate congestion percentage
        hourly_agg = hourly_agg.withColumn(
            "congestion_percentage",
            (col("congestion_count") / col("num_readings") * 100)
        )
        
        return hourly_agg
    
    def compute_road_statistics(self, df):
        """Compute road-level statistics"""
        road_stats = (df
            .groupBy(
                col("location.road_name").alias("road_name"),
                col("location.city_zone").alias("city_zone")
            )
            .agg(
                count("*").alias("total_readings"),
                count(col("sensor_id").distinct()).alias("num_sensors"),
                avg("metrics.vehicle_count").alias("avg_daily_vehicles"),
                sum("metrics.vehicle_count").alias("total_daily_vehicles"),
                avg("metrics.avg_speed_mph").alias("avg_daily_speed"),
                avg("metrics.lane_occupancy").alias("avg_daily_occupancy"),
                sum(when(col("anomalies.is_congested"), 1).otherwise(0)).alias("congestion_incidents"),
                sum(when(col("anomalies.is_accident"), 1).otherwise(0)).alias("accident_count"),
                sum(when(col("anomalies.congestion_level") == "severe", 1).otherwise(0)).alias("severe_congestion_count")
            )
        )
        
        # Calculate metrics
        road_stats = (road_stats
            .withColumn("congestion_rate", 
                       col("congestion_incidents") / col("total_readings") * 100)
            .withColumn("accident_rate",
                       col("accident_count") / col("total_readings") * 100)
        )
        
        return road_stats
    
    def identify_peak_hours(self, hourly_df):
        """Identify peak traffic hours for each road"""
        window_spec = Window.partitionBy("road_name").orderBy(col("avg_vehicle_count").desc())
        
        peak_hours = (hourly_df
            .withColumn("rank", expr("row_number() over (partition by road_name order by avg_vehicle_count desc)"))
            .filter(col("rank") <= 3)
            .select(
                "road_name",
                "city_zone",
                "hour",
                "day_of_week",
                "avg_vehicle_count",
                "avg_speed",
                "congestion_percentage",
                "rank"
            )
        )
        
        return peak_hours
    
    def compute_vehicle_type_distribution(self, df):
        """Analyze vehicle type distribution"""
        vehicle_dist = (df
            .select(
                col("location.road_name").alias("road_name"),
                col("location.city_zone").alias("city_zone"),
                col("metrics.vehicle_types.car").alias("cars"),
                col("metrics.vehicle_types.truck").alias("trucks"),
                col("metrics.vehicle_types.bus").alias("buses"),
                col("metrics.vehicle_types.motorcycle").alias("motorcycles"),
                col("metrics.vehicle_types.bicycle").alias("bicycles")
            )
            .groupBy("road_name", "city_zone")
            .agg(
                sum("cars").alias("total_cars"),
                sum("trucks").alias("total_trucks"),
                sum("buses").alias("total_buses"),
                sum("motorcycles").alias("total_motorcycles"),
                sum("bicycles").alias("total_bicycles")
            )
        )
        
        # Calculate percentages
        vehicle_dist = vehicle_dist.withColumn(
            "total_vehicles",
            col("total_cars") + col("total_trucks") + col("total_buses") + 
            col("total_motorcycles") + col("total_bicycles")
        )
        
        for vtype in ["cars", "trucks", "buses", "motorcycles", "bicycles"]:
            vehicle_dist = vehicle_dist.withColumn(
                f"{vtype}_percentage",
                (col(f"total_{vtype}") / col("total_vehicles") * 100)
            )
        
        return vehicle_dist
    
    def compute_weather_impact(self, df):
        """Analyze weather impact on traffic"""
        weather_impact = (df
            .groupBy(
                col("conditions.weather").alias("weather"),
                col("location.city_zone").alias("city_zone")
            )
            .agg(
                count("*").alias("num_readings"),
                avg("metrics.avg_speed_mph").alias("avg_speed"),
                avg("metrics.vehicle_count").alias("avg_vehicles"),
                avg("metrics.lane_occupancy").alias("avg_occupancy"),
                sum(when(col("anomalies.is_congested"), 1).otherwise(0)).alias("congestion_count"),
                sum(when(col("anomalies.is_accident"), 1).otherwise(0)).alias("accident_count")
            )
        )
        
        weather_impact = weather_impact.withColumn(
            "congestion_rate",
            (col("congestion_count") / col("num_readings") * 100)
        )
        
        return weather_impact
    
    def save_results(self, df, name: str, date: str = None):
        """Save results to parquet"""
        if date:
            output = f"{self.output_path}/{name}/date={date}"
        else:
            output = f"{self.output_path}/{name}"
        
        (df.write
         .mode("overwrite")
         .partitionBy("city_zone") if "city_zone" in df.columns else df.write
         .mode("overwrite")
         .parquet(output))
        
        print(f"✅ Saved {name} to {output}")
    
    def run(self, date: str = None):
        """Execute the complete batch job"""
        print("=" * 80)
        print("🚀 DAILY TRAFFIC AGGREGATION JOB")
        print("=" * 80)
        print(f"Input path: {self.input_path}")
        print(f"Output path: {self.output_path}")
        print(f"Processing date: {date if date else 'ALL'}")
        print("=" * 80)
        
        # Load data
        print("\n📥 Loading data...")
        df = self.load_data(date)
        total_records = df.count()
        print(f"   Loaded {total_records:,} records")
        
        # Cache for multiple operations
        df.cache()
        
        # Compute aggregations
        print("\n📊 Computing hourly aggregations...")
        hourly_agg = self.compute_hourly_aggregations(df)
        self.save_results(hourly_agg, "hourly_aggregations", date)
        
        print("\n🛣️  Computing road statistics...")
        road_stats = self.compute_road_statistics(df)
        self.save_results(road_stats, "road_statistics", date)
        
        print("\n⏰ Identifying peak hours...")
        peak_hours = self.identify_peak_hours(hourly_agg)
        self.save_results(peak_hours, "peak_hours", date)
        
        print("\n🚗 Analyzing vehicle type distribution...")
        vehicle_dist = self.compute_vehicle_type_distribution(df)
        self.save_results(vehicle_dist, "vehicle_distribution", date)
        
        print("\n🌤️  Analyzing weather impact...")
        weather_impact = self.compute_weather_impact(df)
        self.save_results(weather_impact, "weather_impact", date)
        
        # Cleanup
        df.unpersist()
        
        print("\n" + "=" * 80)
        print("✅ BATCH JOB COMPLETED SUCCESSFULLY")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Daily traffic aggregation batch job"
    )
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="Input path to raw traffic data"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        required=True,
        help="Output path for aggregated results"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Specific date to process (YYYY-MM-DD format)"
    )
    
    args = parser.parse_args()
    
    job = DailyAggregationJob(args.input_path, args.output_path)
    job.run(args.date)


if __name__ == "__main__":
    main()
