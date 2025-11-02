"""
Integrated Weather Data Pipeline
Combines PAGASA typhoon data with Open-Meteo weather forecasts
for comprehensive weather features in suspension predictions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from pagasa_checker import PAGASAChecker
from openmeteo_collector import OpenMeteoCollector


class WeatherDataPipeline:
    """
    Integrated weather data collection and feature engineering pipeline.
    Combines:
    - PAGASA typhoon/TCWS data
    - Open-Meteo historical weather
    - Open-Meteo real-time forecasts
    """
    
    def __init__(
        self,
        data_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize weather data pipeline.
        
        Args:
            data_dir: Directory to save collected data
            cache_dir: Directory for API caching
        """
        self.data_dir = Path(data_dir) if data_dir else \
            Path('weather_data')
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize collectors
        self.pagasa = PAGASAChecker()
        self.openmeteo = OpenMeteoCollector(cache_dir=cache_dir)
        
        print(f"📂 Data directory: {self.data_dir}")
    
    def collect_realtime_weather_features(self) -> Dict[str, Any]:
        """
        Collect all real-time weather features for predictions.
        
        Returns:
            Dictionary with weather features ready for ML model
        """
        print("\n🌐 Collecting real-time weather features...")
        print("=" * 70)
        
        # 1. PAGASA typhoon data
        print("\n1️⃣ Fetching PAGASA typhoon status...")
        pagasa_status = self.pagasa.check_typhoon_status()
        
        pagasa_features = {
            'tcws_level': pagasa_status.get('tcwsLevel', 0),
            'metro_manila_affected': int(pagasa_status.get(
                'metroManilaAffected', False
            )),
            'has_active_typhoon': int(pagasa_status.get(
                'hasActiveTyphoon', False
            ))
        }
        
        # Rainfall warning
        rainfall = pagasa_status.get('rainfallWarning', {})
        pagasa_features['has_rainfall_warning'] = int(
            rainfall.get('hasActiveWarning', False)
        )
        
        rainfall_levels = {'RED': 3, 'ORANGE': 2, 'YELLOW': 1}
        pagasa_features['rainfall_warning_level'] = rainfall_levels.get(
            rainfall.get('warningLevel'), 0
        )
        
        print(f"   ✅ TCWS Level: {pagasa_features['tcws_level']}")
        print(f"   ✅ Metro Manila Affected: "
              f"{bool(pagasa_features['metro_manila_affected'])}")
        print(f"   ✅ Rainfall Warning: "
              f"{rainfall.get('warningLevel', 'None')}")
        
        # 2. Open-Meteo forecast (today + tomorrow)
        print("\n2️⃣ Fetching Open-Meteo forecast (2 days)...")
        forecast_df = self.openmeteo.fetch_realtime_forecast(days_ahead=2)
        
        # Get Metro Manila average for today
        today = pd.Timestamp.now().date()
        today_forecast = forecast_df[
            forecast_df['forecast_date'].dt.date == today
        ]
        
        if len(today_forecast) > 0:
            # Average across all LGUs
            weather_features = {
                'forecast_precipitation_sum': today_forecast[
                    'precipitation_sum'
                ].mean(),
                'forecast_precipitation_probability': today_forecast[
                    'precipitation_probability_max'
                ].mean(),
                'forecast_wind_speed_max': today_forecast[
                    'wind_speed_10m_max'
                ].mean(),
                'forecast_wind_gusts_max': today_forecast[
                    'wind_gusts_10m_max'
                ].mean(),
                'forecast_temperature_max': today_forecast[
                    'temperature_2m_max'
                ].mean(),
                'forecast_humidity_mean': today_forecast[
                    'relative_humidity_2m_mean'
                ].mean(),
                'forecast_cloud_cover': today_forecast[
                    'cloud_cover_mean'
                ].mean(),
                'forecast_weather_code': int(today_forecast[
                    'weather_code'
                ].mode().iloc[0])
            }
            
            print(f"   ✅ Precipitation: "
                  f"{weather_features['forecast_precipitation_sum']:.1f}mm")
            print(f"   ✅ Wind Speed: "
                  f"{weather_features['forecast_wind_speed_max']:.1f} km/h")
            print(f"   ✅ Temperature: "
                  f"{weather_features['forecast_temperature_max']:.1f}°C")
        else:
            print("   ⚠️  No forecast data for today")
            weather_features = {
                'forecast_precipitation_sum': 0,
                'forecast_precipitation_probability': 0,
                'forecast_wind_speed_max': 0,
                'forecast_wind_gusts_max': 0,
                'forecast_temperature_max': 30,
                'forecast_humidity_mean': 70,
                'forecast_cloud_cover': 50,
                'forecast_weather_code': 0
            }
        
        # 3. Combine all features
        all_features = {
            **pagasa_features,
            **weather_features,
            'collection_timestamp': datetime.now().isoformat(),
            'date': str(today)
        }
        
        # Convert numpy types to native Python types for JSON serialization
        for key, value in all_features.items():
            if hasattr(value, 'item'):  # numpy scalar
                all_features[key] = value.item()
            elif isinstance(value, np.floating):
                all_features[key] = float(value)
            elif isinstance(value, np.integer):
                all_features[key] = int(value)
        
        # Save features
        output_file = self.data_dir / \
            f'realtime_features_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(all_features, f, indent=2)
        
        print(f"\n💾 Features saved to: {output_file}")
        print("\n✅ Real-time weather features collected!")
        
        return all_features
    
    def collect_historical_weather(
        self,
        start_date: str,
        end_date: str,
        include_forecasts: bool = True
    ) -> pd.DataFrame:
        """
        Collect historical weather data for model training.
        
        Args:
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            include_forecasts: Also fetch historical forecasts
        
        Returns:
            DataFrame with historical weather data
        """
        print(f"\n📊 Collecting historical weather: "
              f"{start_date} to {end_date}")
        print("=" * 70)
        
        # 1. Historical observations
        print("\n1️⃣ Fetching historical observations...")
        actual_file = self.data_dir / \
            f'weather_actual_{start_date}_{end_date}.csv'
        actual_df = self.openmeteo.fetch_historical_weather(
            start_date=start_date,
            end_date=end_date,
            output_file=actual_file
        )
        
        # 2. Historical forecasts (if requested)
        if include_forecasts:
            print("\n2️⃣ Fetching historical forecasts...")
            forecast_file = self.data_dir / \
                f'weather_forecast_{start_date}_{end_date}.csv'
            forecast_df = self.openmeteo.fetch_forecast_weather(
                start_date=start_date,
                end_date=end_date,
                output_file=forecast_file
            )
            
            # Merge actual and forecast
            print("\n3️⃣ Merging actual + forecast data...")
            merged_df = actual_df.merge(
                forecast_df,
                on=['date', 'lgu', 'latitude', 'longitude'],
                suffixes=('_actual', '_forecast'),
                how='left'
            )
            
            print(f"   ✅ Merged shape: {merged_df.shape}")
            
            # Save merged data
            merged_file = self.data_dir / \
                f'weather_combined_{start_date}_{end_date}.csv'
            merged_df.to_csv(merged_file, index=False)
            print(f"   💾 Saved to: {merged_file}")
            
            return merged_df
        
        return actual_df
    
    def create_weather_features_for_date(
        self,
        target_date: str,
        historical_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Create weather features for a specific date from historical data.
        
        Args:
            target_date: Date in 'YYYY-MM-DD' format
            historical_df: Historical weather DataFrame
        
        Returns:
            Dictionary of weather features
        """
        target_dt = pd.to_datetime(target_date)
        
        # Filter data for target date
        date_data = historical_df[historical_df['date'] == target_dt]
        
        if len(date_data) == 0:
            print(f"⚠️  No data found for {target_date}")
            return {}
        
        # Calculate Metro Manila averages
        features = {
            'precipitation_sum': date_data['precipitation_sum'].mean(),
            'wind_speed_10m_max': date_data['wind_speed_10m_max'].mean(),
            'wind_gusts_10m_max': date_data['wind_gusts_10m_max'].mean(),
            'temperature_2m_max': date_data['temperature_2m_max'].mean(),
            'relative_humidity_2m_mean': date_data[
                'relative_humidity_2m_mean'
            ].mean(),
            'cloud_cover_max': date_data['cloud_cover_max'].mean(),
            'pressure_msl_min': date_data['pressure_msl_min'].mean(),
            'weather_code': int(date_data['weather_code'].mode().iloc[0])
        }
        
        return features
    
    def update_master_dataset_with_weather(
        self,
        master_df: pd.DataFrame,
        weather_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add weather features to master suspension dataset.
        
        Args:
            master_df: Master dataset with suspension records
            weather_df: Weather data from Open-Meteo
        
        Returns:
            Master dataset with weather features added
        """
        print("\n🔗 Merging weather data with master dataset...")
        
        # Ensure date columns are datetime
        master_df['date'] = pd.to_datetime(master_df['date'])
        weather_df['date'] = pd.to_datetime(weather_df['date'])
        
        # Calculate Metro Manila averages
        mm_weather = self.openmeteo.get_metro_manila_average(
            weather_df,
            date_col='date'
        )
        
        # Merge on date
        merged_df = master_df.merge(
            mm_weather,
            on='date',
            how='left',
            suffixes=('', '_weather')
        )
        
        print(f"   ✅ Before merge: {master_df.shape}")
        print(f"   ✅ After merge: {merged_df.shape}")
        print(f"   ✅ Weather columns added: "
              f"{len(merged_df.columns) - len(master_df.columns)}")
        
        return merged_df
    
    def run_daily_collection(self) -> Dict[str, Any]:
        """
        Run daily automated weather collection.
        Collects both PAGASA and Open-Meteo data.
        
        Returns:
            Dictionary with collection status
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ Daily Collection Run: {timestamp}")
        print("=" * 70)
        
        results = {
            'timestamp': timestamp,
            'date': str(datetime.now().date())
        }
        
        try:
            # 1. Collect PAGASA data
            print("\n1️⃣ Collecting PAGASA data...")
            pagasa_status = self.pagasa.check_typhoon_status()
            results['pagasa'] = {
                'success': True,
                'has_typhoon': pagasa_status.get('hasActiveTyphoon'),
                'tcws_level': pagasa_status.get('tcwsLevel'),
                'metro_manila_affected': pagasa_status.get(
                    'metroManilaAffected'
                )
            }
            print("   ✅ PAGASA data collected")
            
        except Exception as e:
            results['pagasa'] = {'success': False, 'error': str(e)}
            print(f"   ❌ PAGASA collection failed: {e}")
        
        try:
            # 2. Collect Open-Meteo forecast
            print("\n2️⃣ Collecting Open-Meteo forecast...")
            forecast_file = self.data_dir / \
                f'daily_forecast_{datetime.now().strftime("%Y%m%d")}.csv'
            forecast_df = self.openmeteo.fetch_realtime_forecast(
                days_ahead=7,
                output_file=forecast_file
            )
            results['openmeteo'] = {
                'success': True,
                'records': len(forecast_df),
                'file': str(forecast_file)
            }
            print("   ✅ Open-Meteo forecast collected")
            
        except Exception as e:
            results['openmeteo'] = {'success': False, 'error': str(e)}
            print(f"   ❌ Open-Meteo collection failed: {e}")
        
        # 3. Save daily log
        log_file = self.data_dir / 'daily_collection_log.jsonl'
        with open(log_file, 'a') as f:
            f.write(json.dumps(results) + '\n')
        
        print(f"\n💾 Log saved to: {log_file}")
        print("\n✅ Daily collection complete!")
        
        return results


def main():
    """Demo of integrated weather pipeline."""
    print("=" * 70)
    print("INTEGRATED WEATHER DATA PIPELINE - DEMO")
    print("=" * 70)
    
    pipeline = WeatherDataPipeline(data_dir=Path('weather_data'))
    
    # 1. Collect real-time features
    print("\n" + "=" * 70)
    print("DEMO 1: REAL-TIME FEATURES FOR PREDICTIONS")
    print("=" * 70)
    
    features = pipeline.collect_realtime_weather_features()
    
    print("\n📊 Features collected:")
    for key, value in features.items():
        if key not in ['collection_timestamp', 'date']:
            print(f"   {key}: {value}")
    
    # 2. Historical collection (last 7 days)
    print("\n\n" + "=" * 70)
    print("DEMO 2: HISTORICAL WEATHER COLLECTION")
    print("=" * 70)
    
    today = datetime.now().date()
    start = today - timedelta(days=7)
    
    historical_df = pipeline.collect_historical_weather(
        start_date=str(start),
        end_date=str(today),
        include_forecasts=False
    )
    
    print(f"\n📊 Historical data shape: {historical_df.shape}")
    print(f"\n Sample:\n{historical_df.head(3)}")
    
    # 3. Daily collection run
    print("\n\n" + "=" * 70)
    print("DEMO 3: DAILY AUTOMATED COLLECTION")
    print("=" * 70)
    
    daily_results = pipeline.run_daily_collection()
    
    print("\n📊 Collection results:")
    print(json.dumps(daily_results, indent=2))
    
    print("\n" + "=" * 70)
    print("✅ Pipeline demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
