"""
Traffic Prediction Model Training
Uses historical data to train ML models for traffic forecasting
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import json
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class TrafficPredictor:
    """Train models to predict traffic patterns"""
    
    def __init__(self):
        self.speed_model = None
        self.volume_model = None
        self.congestion_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_historical_data(self, data_path: str) -> pd.DataFrame:
        """Load and prepare historical traffic data"""
        
        print("📥 Loading historical data...")
        
        # In production, this would load from Parquet files or database
        # For now, create sample structure
        dates = pd.date_range(start='2024-09-01', end='2024-11-30', freq='5T')
        
        # Create sample data structure
        data = {
            'timestamp': dates,
            'sensor_id': np.random.choice(['SENSOR_001', 'SENSOR_002', 'SENSOR_003'], len(dates)),
            'road_name': np.random.choice(['Main Street', 'Broadway', '5th Avenue'], len(dates)),
            'city_zone': np.random.choice(['Downtown', 'North End', 'West Side'], len(dates)),
            'vehicle_count': np.random.randint(10, 100, len(dates)),
            'avg_speed_mph': np.random.uniform(15, 65, len(dates)),
            'lane_occupancy': np.random.uniform(0.1, 0.9, len(dates)),
            'weather': np.random.choice(['clear', 'rain', 'fog'], len(dates)),
            'temperature_f': np.random.uniform(30, 85, len(dates)),
            'is_congested': np.random.choice([0, 1], len(dates), p=[0.7, 0.3])
        }
        
        df = pd.DataFrame(data)
        print(f"✅ Loaded {len(df):,} records")
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for prediction"""
        
        print("🔧 Engineering features...")
        
        df = df.copy()
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_rush_hour'] = df['hour'].apply(
            lambda x: 1 if (7 <= x <= 9) or (17 <= x <= 19) else 0
        )
        df['month'] = df['timestamp'].dt.month
        df['day_of_month'] = df['timestamp'].dt.day
        
        # Cyclical encoding for hour and day
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Encode categorical variables
        for col in ['sensor_id', 'road_name', 'city_zone', 'weather']:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df[col])
            else:
                df[f'{col}_encoded'] = self.label_encoders[col].transform(df[col])
        
        # Lag features (previous hour's traffic)
        df = df.sort_values(['sensor_id', 'timestamp'])
        df['prev_speed'] = df.groupby('sensor_id')['avg_speed_mph'].shift(1)
        df['prev_volume'] = df.groupby('sensor_id')['vehicle_count'].shift(1)
        df['prev_occupancy'] = df.groupby('sensor_id')['lane_occupancy'].shift(1)
        
        # Rolling averages
        df['speed_rolling_3h'] = df.groupby('sensor_id')['avg_speed_mph'].transform(
            lambda x: x.rolling(window=36, min_periods=1).mean()
        )
        df['volume_rolling_3h'] = df.groupby('sensor_id')['vehicle_count'].transform(
            lambda x: x.rolling(window=36, min_periods=1).mean()
        )
        
        # Drop rows with NaN from lag features
        df = df.fillna(df.mean(numeric_only=True))
        
        print(f"✅ Created {len(df.columns)} features")
        
        return df
    
    def train_speed_model(self, X_train, X_test, y_train, y_test):
        """Train model to predict average speed"""
        
        print("\n🎯 Training speed prediction model...")
        
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        print(f"   MAE: {mae:.2f} mph")
        print(f"   RMSE: {rmse:.2f} mph")
        print(f"   R²: {r2:.3f}")
        
        self.speed_model = model
        
        return model
    
    def train_volume_model(self, X_train, X_test, y_train, y_test):
        """Train model to predict vehicle count"""
        
        print("\n🚗 Training vehicle volume prediction model...")
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        print(f"   MAE: {mae:.2f} vehicles")
        print(f"   RMSE: {rmse:.2f} vehicles")
        print(f"   R²: {r2:.3f}")
        
        self.volume_model = model
        
        return model
    
    def train_congestion_model(self, X_train, X_test, y_train, y_test):
        """Train model to predict congestion probability"""
        
        print("\n🚦 Training congestion prediction model...")
        
        from sklearn.ensemble import GradientBoostingClassifier
        
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"   Accuracy: {accuracy:.3f}")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1:.3f}")
        
        self.congestion_model = model
        
        return model
    
    def save_models(self, output_dir: str = "ml_models/models"):
        """Save trained models"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n💾 Saving models to {output_dir}...")
        
        if self.speed_model:
            joblib.dump(self.speed_model, output_path / "speed_model.pkl")
            print("   ✅ Speed model saved")
        
        if self.volume_model:
            joblib.dump(self.volume_model, output_path / "volume_model.pkl")
            print("   ✅ Volume model saved")
        
        if self.congestion_model:
            joblib.dump(self.congestion_model, output_path / "congestion_model.pkl")
            print("   ✅ Congestion model saved")
        
        joblib.dump(self.scaler, output_path / "scaler.pkl")
        joblib.dump(self.label_encoders, output_path / "label_encoders.pkl")
        
        print("   ✅ Preprocessors saved")
    
    def load_models(self, model_dir: str = "ml_models/models"):
        """Load pre-trained models"""
        
        model_path = Path(model_dir)
        
        self.speed_model = joblib.load(model_path / "speed_model.pkl")
        self.volume_model = joblib.load(model_path / "volume_model.pkl")
        self.congestion_model = joblib.load(model_path / "congestion_model.pkl")
        self.scaler = joblib.load(model_path / "scaler.pkl")
        self.label_encoders = joblib.load(model_path / "label_encoders.pkl")
        
        print("✅ Models loaded successfully")
    
    def predict(self, features: pd.DataFrame):
        """Make predictions using trained models"""
        
        speed_pred = self.speed_model.predict(features)
        volume_pred = self.volume_model.predict(features)
        congestion_prob = self.congestion_model.predict_proba(features)[:, 1]
        
        return {
            'predicted_speed': float(speed_pred[0]),
            'predicted_volume': int(volume_pred[0]),
            'congestion_probability': float(congestion_prob[0])
        }
    
    def train_all_models(self, data_path: str = None):
        """Complete training pipeline"""
        
        print("=" * 80)
        print("🤖 TRAFFIC PREDICTION MODEL TRAINING")
        print("=" * 80)
        
        # Load data
        df = self.load_historical_data(data_path)
        
        # Feature engineering
        df = self.engineer_features(df)
        
        # Prepare features
        feature_cols = [
            'hour', 'day_of_week', 'is_weekend', 'is_rush_hour',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'sensor_id_encoded', 'road_name_encoded', 'city_zone_encoded',
            'weather_encoded', 'temperature_f', 'prev_speed', 'prev_volume',
            'prev_occupancy', 'speed_rolling_3h', 'volume_rolling_3h'
        ]
        
        X = df[feature_cols]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=feature_cols)
        
        # Split data
        X_train, X_test = train_test_split(X_scaled, test_size=0.2, random_state=42)
        
        # Train models
        y_speed_train = df.loc[X_train.index, 'avg_speed_mph']
        y_speed_test = df.loc[X_test.index, 'avg_speed_mph']
        self.train_speed_model(X_train, X_test, y_speed_train, y_speed_test)
        
        y_volume_train = df.loc[X_train.index, 'vehicle_count']
        y_volume_test = df.loc[X_test.index, 'vehicle_count']
        self.train_volume_model(X_train, X_test, y_volume_train, y_volume_test)
        
        y_congestion_train = df.loc[X_train.index, 'is_congested']
        y_congestion_test = df.loc[X_test.index, 'is_congested']
        self.train_congestion_model(X_train, X_test, y_congestion_train, y_congestion_test)
        
        # Save models
        self.save_models()
        
        print("\n" + "=" * 80)
        print("✅ TRAINING COMPLETE")
        print("=" * 80)


def main():
    predictor = TrafficPredictor()
    predictor.train_all_models()


if __name__ == "__main__":
    main()
