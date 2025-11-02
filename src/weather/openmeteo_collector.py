"""
Open-Meteo Weather Data Collector
Fetches historical and forecast weather data for Metro Manila LGUs
"""

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from pathlib import Path
from datetime import datetime, timedelta
from typing import Literal, Optional
import numpy as np


# Metro Manila LGU coordinates (17 cities/municipalities)
METRO_MANILA_COORDS = {
    'manila': {'lat': 14.5995, 'lon': 120.9842},
    'quezon_city': {'lat': 14.6760, 'lon': 121.0437},
    'caloocan': {'lat': 14.6584, 'lon': 120.9635},
    'las_pinas': {'lat': 14.4378, 'lon': 120.9761},
    'makati': {'lat': 14.5547, 'lon': 121.0244},
    'malabon': {'lat': 14.6649, 'lon': 120.9569},
    'mandaluyong': {'lat': 14.5794, 'lon': 121.0359},
    'marikina': {'lat': 14.6507, 'lon': 121.1029},
    'muntinlupa': {'lat': 14.3832, 'lon': 121.0409},
    'navotas': {'lat': 14.6695, 'lon': 120.9478},
    'paranaque': {'lat': 14.4793, 'lon': 121.0198},
    'pasay': {'lat': 14.5378, 'lon': 120.9896},
    'pasig': {'lat': 14.5764, 'lon': 121.0851},
    'pateros': {'lat': 14.5454, 'lon': 121.0697},
    'san_juan': {'lat': 14.6019, 'lon': 121.0355},
    'taguig': {'lat': 14.5176, 'lon': 121.0509},
    'valenzuela': {'lat': 14.7108, 'lon': 120.9830}
}


class OpenMeteoCollector:
    """
    Collects weather data from Open-Meteo API.
    Supports historical data, forecasts, and real-time weather.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize Open-Meteo collector.
        
        Args:
            cache_dir: Directory for caching API responses.
                      If None, uses .cache in current directory.
        """
        if cache_dir is None:
            cache_dir = Path('.cache')
        
        # Setup cache and retry logic
        cache_session = requests_cache.CachedSession(
            str(cache_dir),
            expire_after=3600  # 1 hour cache
        )
        retry_session = retry(
            cache_session,
            retries=5,
            backoff_factor=0.2
        )
        self.client = openmeteo_requests.Client(session=retry_session)
        
        # Extract coordinates
        self.latitudes = [coord['lat'] for coord in 
                         METRO_MANILA_COORDS.values()]
        self.longitudes = [coord['lon'] for coord in 
                          METRO_MANILA_COORDS.values()]
        self.lgu_names = list(METRO_MANILA_COORDS.keys())
    
    def fetch_historical_weather(
        self,
        start_date: str,
        end_date: str,
        output_file: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Fetch historical weather data (actual observations).
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            output_file: Optional path to save CSV
        
        Returns:
            DataFrame with historical weather data for all LGUs
        """
        print(f"🌤️  Fetching historical weather: {start_date} to {end_date}")
        
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": self.latitudes,
            "longitude": self.longitudes,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "weather_code",
                "precipitation_sum",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "et0_fao_evapotranspiration",
                "relative_humidity_2m_mean",
                "cloud_cover_max",
                "shortwave_radiation_sum",
                "temperature_2m_max",
                "apparent_temperature_max",
                "dew_point_2m_mean",
                "pressure_msl_min",
                "vapour_pressure_deficit_max"
            ],
            "timezone": "Asia/Singapore"
        }
        
        responses = self.client.weather_api(url, params=params)
        
        # Collect data from all locations
        all_data = []
        
        for lgu_name, response in zip(self.lgu_names, responses):
            daily = response.Daily()
            
            # Create date range
            dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
            
            # Extract all variables
            df = pd.DataFrame({
                'date': dates,
                'lgu': lgu_name,
                'latitude': response.Latitude(),
                'longitude': response.Longitude(),
                'weather_code': daily.Variables(0).ValuesAsNumpy(),
                'precipitation_sum': daily.Variables(1).ValuesAsNumpy(),
                'wind_speed_10m_max': daily.Variables(2).ValuesAsNumpy(),
                'wind_gusts_10m_max': daily.Variables(3).ValuesAsNumpy(),
                'et0_fao_evapotranspiration': daily.Variables(4)
                .ValuesAsNumpy(),
                'relative_humidity_2m_mean': daily.Variables(5)
                .ValuesAsNumpy(),
                'cloud_cover_max': daily.Variables(6).ValuesAsNumpy(),
                'shortwave_radiation_sum': daily.Variables(7)
                .ValuesAsNumpy(),
                'temperature_2m_max': daily.Variables(8).ValuesAsNumpy(),
                'apparent_temperature_max': daily.Variables(9)
                .ValuesAsNumpy(),
                'dew_point_2m_mean': daily.Variables(10).ValuesAsNumpy(),
                'pressure_msl_min': daily.Variables(11).ValuesAsNumpy(),
                'vapour_pressure_deficit_max': daily.Variables(12)
                .ValuesAsNumpy()
            })
            
            all_data.append(df)
        
        # Combine all LGUs
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert date to timezone-naive (remove UTC)
        combined_df['date'] = combined_df['date'].dt.tz_localize(None)
        
        print(f"✅ Fetched {len(combined_df)} records from "
              f"{len(self.lgu_names)} LGUs")
        
        # Save if requested
        if output_file:
            combined_df.to_csv(output_file, index=False)
            print(f"💾 Saved to: {output_file}")
        
        return combined_df
    
    def fetch_forecast_weather(
        self,
        start_date: str,
        end_date: str,
        output_file: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Fetch historical forecast data (what was predicted).
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            output_file: Optional path to save CSV
        
        Returns:
            DataFrame with forecast data for all LGUs
        """
        print(f"📊 Fetching historical forecasts: "
              f"{start_date} to {end_date}")
        
        url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitudes,
            "longitude": self.longitudes,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "weather_code",
                "precipitation_hours",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "dew_point_2m_mean",
                "cape_max",
                "cloud_cover_max",
                "shortwave_radiation_sum",
                "et0_fao_evapotranspiration",
                "relative_humidity_2m_mean",
                "precipitation_sum",
                "pressure_msl_min",
                "updraft_max",
                "temperature_2m_max",
                "apparent_temperature_max",
                "vapour_pressure_deficit_max"
            ],
            "timezone": "Asia/Singapore"
        }
        
        responses = self.client.weather_api(url, params=params)
        
        # Collect data from all locations
        all_data = []
        
        for lgu_name, response in zip(self.lgu_names, responses):
            daily = response.Daily()
            
            # Create date range
            dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
            
            # Extract all variables
            df = pd.DataFrame({
                'date': dates,
                'lgu': lgu_name,
                'latitude': response.Latitude(),
                'longitude': response.Longitude(),
                'weather_code': daily.Variables(0).ValuesAsNumpy(),
                'precipitation_hours': daily.Variables(1).ValuesAsNumpy(),
                'precipitation_probability_max': daily.Variables(2)
                .ValuesAsNumpy(),
                'wind_speed_10m_max': daily.Variables(3).ValuesAsNumpy(),
                'wind_gusts_10m_max': daily.Variables(4).ValuesAsNumpy(),
                'dew_point_2m_mean': daily.Variables(5).ValuesAsNumpy(),
                'cape_max': daily.Variables(6).ValuesAsNumpy(),
                'cloud_cover_max': daily.Variables(7).ValuesAsNumpy(),
                'shortwave_radiation_sum': daily.Variables(8)
                .ValuesAsNumpy(),
                'et0_fao_evapotranspiration': daily.Variables(9)
                .ValuesAsNumpy(),
                'relative_humidity_2m_mean': daily.Variables(10)
                .ValuesAsNumpy(),
                'precipitation_sum': daily.Variables(11).ValuesAsNumpy(),
                'pressure_msl_min': daily.Variables(12).ValuesAsNumpy(),
                'updraft_max': daily.Variables(13).ValuesAsNumpy(),
                'temperature_2m_max': daily.Variables(14).ValuesAsNumpy(),
                'apparent_temperature_max': daily.Variables(15)
                .ValuesAsNumpy(),
                'vapour_pressure_deficit_max': daily.Variables(16)
                .ValuesAsNumpy()
            })
            
            all_data.append(df)
        
        # Combine all LGUs
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert date to timezone-naive
        combined_df['date'] = combined_df['date'].dt.tz_localize(None)
        
        print(f"✅ Fetched {len(combined_df)} forecast records from "
              f"{len(self.lgu_names)} LGUs")
        
        # Save if requested
        if output_file:
            combined_df.to_csv(output_file, index=False)
            print(f"💾 Saved to: {output_file}")
        
        return combined_df
    
    def fetch_realtime_forecast(
        self,
        days_ahead: int = 7,
        output_file: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Fetch real-time weather forecast for the next N days.
        
        Args:
            days_ahead: Number of days to forecast (default: 7)
            output_file: Optional path to save CSV
        
        Returns:
            DataFrame with forecast data for all LGUs
        """
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        print(f"🔮 Fetching real-time forecast: "
              f"{today} to {end_date} ({days_ahead} days)")
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": self.latitudes,
            "longitude": self.longitudes,
            "daily": [
                "weather_code",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "temperature_2m_max",
                "apparent_temperature_max",
                "relative_humidity_2m_mean",
                "cloud_cover_mean",
                "pressure_msl_mean"
            ],
            "timezone": "Asia/Singapore",
            "forecast_days": days_ahead
        }
        
        responses = self.client.weather_api(url, params=params)
        
        # Collect data from all locations
        all_data = []
        
        for lgu_name, response in zip(self.lgu_names, responses):
            daily = response.Daily()
            
            # Create date range
            dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
            
            # Extract variables
            df = pd.DataFrame({
                'forecast_date': dates,
                'lgu': lgu_name,
                'latitude': response.Latitude(),
                'longitude': response.Longitude(),
                'weather_code': daily.Variables(0).ValuesAsNumpy(),
                'precipitation_sum': daily.Variables(1).ValuesAsNumpy(),
                'precipitation_probability_max': daily.Variables(2)
                .ValuesAsNumpy(),
                'wind_speed_10m_max': daily.Variables(3).ValuesAsNumpy(),
                'wind_gusts_10m_max': daily.Variables(4).ValuesAsNumpy(),
                'temperature_2m_max': daily.Variables(5).ValuesAsNumpy(),
                'apparent_temperature_max': daily.Variables(6)
                .ValuesAsNumpy(),
                'relative_humidity_2m_mean': daily.Variables(7)
                .ValuesAsNumpy(),
                'cloud_cover_mean': daily.Variables(8).ValuesAsNumpy(),
                'pressure_msl_mean': daily.Variables(9).ValuesAsNumpy(),
                'fetched_at': datetime.now()
            })
            
            all_data.append(df)
        
        # Combine all LGUs
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert date to timezone-naive
        combined_df['forecast_date'] = combined_df['forecast_date']\
            .dt.tz_localize(None)
        
        print(f"✅ Fetched {len(combined_df)} forecast records from "
              f"{len(self.lgu_names)} LGUs")
        
        # Save if requested
        if output_file:
            combined_df.to_csv(output_file, index=False)
            print(f"💾 Saved to: {output_file}")
        
        return combined_df
    
    def get_metro_manila_average(
        self,
        df: pd.DataFrame,
        date_col: str = 'date'
    ) -> pd.DataFrame:
        """
        Calculate Metro Manila average from per-LGU data.
        
        Args:
            df: DataFrame with LGU-level weather data
            date_col: Name of the date column
        
        Returns:
            DataFrame with Metro Manila averages
        """
        # Numeric columns to average
        numeric_cols = df.select_dtypes(include=[np.number])\
            .columns.tolist()
        
        # Remove coordinates
        numeric_cols = [c for c in numeric_cols 
                       if c not in ['latitude', 'longitude']]
        
        # Group by date and average
        avg_df = df.groupby(date_col)[numeric_cols].mean().reset_index()
        avg_df['lgu'] = 'metro_manila_average'
        
        return avg_df


def main():
    """Demo of weather data collection."""
    print("=" * 70)
    print("OPEN-METEO WEATHER DATA COLLECTOR - DEMO")
    print("=" * 70)
    print()
    
    collector = OpenMeteoCollector()
    
    # 1. Fetch historical weather (last 30 days)
    print("\n1️⃣ HISTORICAL WEATHER (Last 30 days)")
    print("-" * 70)
    today = datetime.now().date()
    start = today - timedelta(days=30)
    
    historical = collector.fetch_historical_weather(
        start_date=str(start),
        end_date=str(today),
        output_file=Path('weather_historical_30d.csv')
    )
    
    print(f"\nSample data:\n{historical.head()}")
    print(f"\nShape: {historical.shape}")
    
    # 2. Fetch real-time forecast (next 7 days)
    print("\n\n2️⃣ REAL-TIME FORECAST (Next 7 days)")
    print("-" * 70)
    
    forecast = collector.fetch_realtime_forecast(
        days_ahead=7,
        output_file=Path('weather_forecast_7d.csv')
    )
    
    print(f"\nSample data:\n{forecast.head()}")
    print(f"\nShape: {forecast.shape}")
    
    # 3. Calculate Metro Manila average
    print("\n\n3️⃣ METRO MANILA AVERAGE")
    print("-" * 70)
    
    mm_avg = collector.get_metro_manila_average(historical)
    print(f"\nSample data:\n{mm_avg.head()}")
    print(f"\nShape: {mm_avg.shape}")
    
    print("\n" + "=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
