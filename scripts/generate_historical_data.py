"""
Historical Data Generator for Batch Layer
Generates months/years of historical traffic data for batch processing
"""

import os
import json
import sys
from datetime import datetime, timedelta
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data_generator.sensor_simulator import SensorSimulator
from dataclasses import asdict


def generate_historical_data(num_days: int = 90, output_dir: str = None):
    """
    Generate historical traffic data for specified number of days
    
    Args:
        num_days: Number of days of historical data to generate
        output_dir: Directory to save the data
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "raw" / "historical"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    simulator = SensorSimulator(num_sensors=50)
    
    # Add some construction zones
    simulator.add_construction_zone("SENSOR_005")
    simulator.add_construction_zone("SENSOR_023")
    
    print("=" * 80)
    print("📅 HISTORICAL DATA GENERATION")
    print("=" * 80)
    print(f"Days to generate: {num_days}")
    print(f"Sensors: {len(simulator.sensors)}")
    print(f"Output directory: {output_dir}")
    print(f"Estimated records: ~{num_days * 24 * 60 * len(simulator.sensors):,}")
    print("=" * 80)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=num_days)
    
    current_date = start_date
    total_records = 0
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\n📆 Processing {date_str}...")
        
        # Create daily file
        daily_file = output_dir / f"traffic_{date_str}.json"
        daily_records = []
        
        # Generate readings every minute for all sensors
        for hour in range(24):
            for minute in range(0, 60, 5):  # Every 5 minutes to reduce volume
                timestamp = current_date.replace(hour=hour, minute=minute, second=0)
                
                # Generate reading for each sensor
                for sensor in simulator.sensors:
                    event = simulator.generate_reading(sensor, timestamp)
                    daily_records.append(asdict(event))
                    total_records += 1
        
        # Write daily file
        with open(daily_file, 'w') as f:
            for record in daily_records:
                f.write(json.dumps(record) + '\n')
        
        print(f"   ✅ Generated {len(daily_records):,} records -> {daily_file.name}")
        
        current_date += timedelta(days=1)
    
    print("\n" + "=" * 80)
    print(f"✅ GENERATION COMPLETE!")
    print(f"📊 Total records: {total_records:,}")
    print(f"💾 Total files: {num_days}")
    print(f"📁 Location: {output_dir}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Generate historical traffic data for batch processing"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Number of days of historical data to generate (default: 90)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for generated data"
    )
    
    args = parser.parse_args()
    
    generate_historical_data(num_days=args.days, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
