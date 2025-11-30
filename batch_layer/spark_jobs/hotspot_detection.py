"""
Accident Hotspot Detection
Identifies high-risk areas for accidents using historical data
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, avg, sum, lit, round as spark_round,
    when, sqrt, pow, expr, window, to_timestamp
)
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType
import argparse


class HotspotDetectionJob:
    """Identify accident hotspots and high-risk areas"""
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.spark = self._create_spark_session()
        
    def _create_spark_session(self):
        return (SparkSession.builder
                .appName("AccidentHotspotDetection")
                .config("spark.sql.adaptive.enabled", "true")
                .getOrCreate())
    
    def load_data(self):
        """Load historical traffic data"""
        return self.spark.read.json(f"{self.input_path}/*.json")
    
    def identify_accident_hotspots(self, df):
        """Identify locations with high accident frequency"""
        
        # Extract accident data
        accidents = df.filter(col("anomalies.is_accident") == True)
        
        # Group by location
        hotspots = (accidents
            .groupBy(
                "sensor_id",
                col("location.road_name").alias("road_name"),
                col("location.intersection").alias("intersection"),
                col("location.city_zone").alias("city_zone"),
                col("location.latitude").alias("latitude"),
                col("location.longitude").alias("longitude")
            )
            .agg(
                count("*").alias("accident_count"),
                avg("metrics.avg_speed_mph").alias("avg_speed_at_accident"),
                avg("metrics.vehicle_count").alias("avg_vehicles_at_accident"),
                avg("metrics.lane_occupancy").alias("avg_occupancy_at_accident")
            )
            .orderBy(col("accident_count").desc())
        )
        
        # Calculate risk score (0-100)
        max_accidents = hotspots.agg({"accident_count": "max"}).collect()[0][0]
        
        hotspots = (hotspots
            .withColumn("risk_score", 
                       spark_round((col("accident_count") / lit(max_accidents)) * 100, 2))
            .withColumn("risk_level",
                       when(col("risk_score") >= 80, "Critical")
                       .when(col("risk_score") >= 60, "High")
                       .when(col("risk_score") >= 40, "Moderate")
                       .when(col("risk_score") >= 20, "Low")
                       .otherwise("Minimal"))
        )
        
        return hotspots
    
    def analyze_congestion_patterns(self, df):
        """Analyze severe congestion hotspots"""
        
        severe_congestion = df.filter(col("anomalies.congestion_level") == "severe")
        
        congestion_hotspots = (severe_congestion
            .groupBy(
                "sensor_id",
                col("location.road_name").alias("road_name"),
                col("location.intersection").alias("intersection"),
                col("location.city_zone").alias("city_zone")
            )
            .agg(
                count("*").alias("severe_congestion_count"),
                avg("metrics.avg_speed_mph").alias("avg_speed_during_congestion"),
                avg("metrics.lane_occupancy").alias("avg_occupancy_during_congestion"),
                avg("metrics.vehicle_count").alias("avg_vehicles_during_congestion")
            )
            .orderBy(col("severe_congestion_count").desc())
        )
        
        return congestion_hotspots
    
    def compute_temporal_patterns(self, df):
        """Analyze when accidents are most likely to occur"""
        
        accidents = df.filter(col("anomalies.is_accident") == True)
        
        # Convert timestamp
        accidents = accidents.withColumn(
            "timestamp", 
            to_timestamp(col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
        )
        
        temporal = (accidents
            .withColumn("hour", expr("hour(timestamp)"))
            .withColumn("day_of_week", expr("dayofweek(timestamp)"))
            .groupBy(
                col("location.road_name").alias("road_name"),
                "hour",
                "day_of_week"
            )
            .agg(
                count("*").alias("accident_count"),
                avg("metrics.avg_speed_mph").alias("avg_speed"),
                avg("conditions.temperature_f").alias("avg_temperature")
            )
            .orderBy("road_name", "accident_count")
        )
        
        return temporal
    
    def weather_correlation(self, df):
        """Analyze weather conditions during accidents"""
        
        accidents = df.filter(col("anomalies.is_accident") == True)
        
        weather_stats = (accidents
            .groupBy(
                col("conditions.weather").alias("weather"),
                col("conditions.road_condition").alias("road_condition"),
                col("location.city_zone").alias("city_zone")
            )
            .agg(
                count("*").alias("accident_count"),
                avg("metrics.avg_speed_mph").alias("avg_speed"),
                avg("metrics.vehicle_count").alias("avg_vehicles")
            )
            .orderBy(col("accident_count").desc())
        )
        
        return weather_stats
    
    def save_results(self, df, name: str):
        """Save analysis results"""
        output = f"{self.output_path}/{name}"
        
        (df.write
         .mode("overwrite")
         .parquet(output))
        
        print(f"✅ Saved {name} to {output}")
        
        # Also save as CSV for easy viewing
        (df.coalesce(1)
         .write
         .mode("overwrite")
         .option("header", "true")
         .csv(f"{output}_csv"))
    
    def run(self):
        """Execute hotspot detection job"""
        print("=" * 80)
        print("🚨 ACCIDENT HOTSPOT DETECTION JOB")
        print("=" * 80)
        
        print("\n📥 Loading data...")
        df = self.load_data()
        total_records = df.count()
        print(f"   Loaded {total_records:,} records")
        
        df.cache()
        
        print("\n🗺️  Identifying accident hotspots...")
        hotspots = self.identify_accident_hotspots(df)
        hotspots.show(20, truncate=False)
        self.save_results(hotspots, "accident_hotspots")
        
        print("\n🚦 Analyzing congestion hotspots...")
        congestion = self.analyze_congestion_patterns(df)
        congestion.show(20, truncate=False)
        self.save_results(congestion, "congestion_hotspots")
        
        print("\n⏰ Computing temporal patterns...")
        temporal = self.compute_temporal_patterns(df)
        self.save_results(temporal, "accident_temporal_patterns")
        
        print("\n🌤️  Analyzing weather correlation...")
        weather = self.weather_correlation(df)
        weather.show(20, truncate=False)
        self.save_results(weather, "accident_weather_correlation")
        
        df.unpersist()
        
        print("\n" + "=" * 80)
        print("✅ HOTSPOT DETECTION COMPLETED")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Accident hotspot detection job")
    parser.add_argument("--input-path", type=str, required=True, help="Input data path")
    parser.add_argument("--output-path", type=str, required=True, help="Output path")
    
    args = parser.parse_args()
    
    job = HotspotDetectionJob(args.input_path, args.output_path)
    job.run()


if __name__ == "__main__":
    main()
