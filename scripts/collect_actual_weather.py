"""
Collect Actual Weather Data (2 days ago)
==========================================

This script collects actual weather data from Open-Meteo Historical API
for 2 days ago (to account for the 2-day delay) and stores it in the database.

This runs in GitHub Actions daily to build a historical record of actual weather
that can be compared against forecasts for accuracy tracking.

Usage:
------
# Collect data for 2 days ago
python scripts/collect_actual_weather.py

# Or specify a custom date
python scripts/collect_actual_weather.py --date 2025-11-01

Output:
-------
Stores data in Supabase weather_data table with data_type='actual'
"""

import os
import sys
import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
import requests
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.supabase_client import SupabaseLogger

# Metro Manila LGU coordinates
LGU_COORDS = {
    "Manila": {"lat": 14.5995, "lon": 120.9842},
    "Quezon City": {"lat": 14.6508, "lon": 121.0487},
    "Caloocan": {"lat": 14.6538, "lon": 120.9934},
    "Makati": {"lat": 14.5547, "lon": 121.0244},
    "Pasig": {"lat": 14.5768, "lon": 121.0854},
    "Taguig": {"lat": 14.5176, "lon": 121.0509},
    "Pasay": {"lat": 14.5378, "lon": 121.0016},
    "Mandaluyong": {"lat": 14.5804, "lon": 121.0336},
    "Parañaque": {"lat": 14.4793, "lon": 121.0189},
    "Valenzuela": {"lat": 14.7040, "lon": 120.9844},
    "Las Piñas": {"lat": 14.4449, "lon": 120.9934},
    "Malabon": {"lat": 14.6565, "lon": 120.9634},
    "Marikina": {"lat": 14.6465, "lon": 121.1030},
    "Muntinlupa": {"lat": 14.4084, "lon": 121.0416},
    "Navotas": {"lat": 14.6644, "lon": 120.9392},
    "San Juan": {"lat": 14.6019, "lon": 121.0332},
    "Pateros": {"lat": 14.5422, "lon": 121.0664}
}


def fetch_actual_weather(lgu: str, lat: float, lon: float, target_date: date) -> dict:
    """
    Fetch actual weather data for a specific LGU and date.
    
    Args:
        lgu: LGU name
        lat: Latitude
        lon: Longitude
        target_date: Date to fetch data for
    
    Returns:
        Dict with weather data or None on failure
    """
    base_url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': target_date.strftime('%Y-%m-%d'),
        'end_date': target_date.strftime('%Y-%m-%d'),
        'daily': ','.join([
            'temperature_2m_max',
            'temperature_2m_min',
            'apparent_temperature_max',
            'precipitation_sum',
            'precipitation_hours',
            'wind_speed_10m_max',
            'wind_gusts_10m_max',
            'relative_humidity_2m_mean',
            'cloud_cover_max',
            'pressure_msl_min',
            'weather_code'
        ]),
        'timezone': 'Asia/Manila'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'daily' not in data:
                print(f"⚠️  Missing 'daily' key in response for {lgu}")
                return None
            
            # Extract the single day's data
            daily = data['daily']
            if not daily.get('time') or len(daily['time']) == 0:
                print(f"⚠️  No data returned for {lgu} on {target_date}")
                return None
            
            # Build weather dict (index 0 since we only requested 1 day)
            weather = {}
            for key, values in daily.items():
                if key == 'time':
                    continue
                weather[key] = values[0] if values else None
            
            return weather
        
        else:
            print(f"❌ API error for {lgu}: HTTP {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Error fetching {lgu}: {e}")
        return None


def log_actual_weather_to_db(logger: SupabaseLogger, lgu: str, 
                             weather_date: date, weather_data: dict):
    """
    Log actual weather data to Supabase.
    
    Args:
        logger: SupabaseLogger instance
        lgu: LGU name
        weather_date: Date of weather data
        weather_data: Dict with weather variables
    """
    try:
        # Prepare data for database
        db_data = {
            'weather_date': weather_date,
            'lgu': lgu,
            'data_type': 'actual',  # Important: mark as actual data
            'precipitation_sum': weather_data.get('precipitation_sum'),
            'temperature_2m_max': weather_data.get('temperature_2m_max'),
            'wind_speed_10m_max': weather_data.get('wind_speed_10m_max'),
            'wind_gusts_10m_max': weather_data.get('wind_gusts_10m_max'),
            'relative_humidity_2m_mean': weather_data.get('relative_humidity_2m_mean'),
            'cloud_cover_max': weather_data.get('cloud_cover_max'),
            'pressure_msl_min': weather_data.get('pressure_msl_min'),
            'weather_code': weather_data.get('weather_code'),
            'source': 'open-meteo-archive'
        }
        
        # Insert into weather_data table
        # Use upsert to handle duplicates (unique constraint: weather_date, lgu, data_type)
        result = logger.supabase.table('weather_data').upsert(
            db_data,
            on_conflict='weather_date,lgu,data_type'
        ).execute()
        
        return True
    
    except Exception as e:
        print(f"❌ Database error for {lgu}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect actual weather data from 2 days ago'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Date to collect data for (YYYY-MM-DD). Default: 2 days ago'
    )
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        # Default: 2 days ago (account for Open-Meteo 2-day delay)
        target_date = date.today() - timedelta(days=2)
    
    print("=" * 70)
    print("ACTUAL WEATHER DATA COLLECTION")
    print("=" * 70)
    print(f"📅 Target date: {target_date}")
    print(f"📍 LGUs: {len(LGU_COORDS)}")
    print(f"🌐 API: Open-Meteo Historical Weather (archive)")
    print(f"💾 Storage: Supabase weather_data table (data_type='actual')")
    print()
    
    # Connect to database
    try:
        logger = SupabaseLogger()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("   Make sure SUPABASE_URL and SUPABASE_KEY are set")
        return 1
    
    print()
    print("🚀 Starting data collection...")
    print()
    
    # Track results
    stats = {
        'successful': 0,
        'failed': 0
    }
    
    # Fetch and log data for each LGU
    for lgu, coords in LGU_COORDS.items():
        print(f"📡 Fetching {lgu}...", end=' ')
        
        # Fetch weather data
        weather_data = fetch_actual_weather(
            lgu=lgu,
            lat=coords['lat'],
            lon=coords['lon'],
            target_date=target_date
        )
        
        if weather_data:
            # Log to database
            success = log_actual_weather_to_db(
                logger=logger,
                lgu=lgu,
                weather_date=target_date,
                weather_data=weather_data
            )
            
            if success:
                print("✅")
                stats['successful'] += 1
            else:
                print("❌ (DB error)")
                stats['failed'] += 1
        else:
            print("❌ (API error)")
            stats['failed'] += 1
        
        # Rate limiting (1 req/sec)
        time.sleep(1)
    
    print()
    print("=" * 70)
    print("COLLECTION SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {stats['successful']}/{len(LGU_COORDS)}")
    print(f"❌ Failed: {stats['failed']}/{len(LGU_COORDS)}")
    print()
    
    if stats['successful'] == len(LGU_COORDS):
        print("✅ All LGUs collected successfully!")
        print()
        print(f"💡 Data stored in Supabase weather_data table:")
        print(f"   - weather_date: {target_date}")
        print(f"   - data_type: 'actual'")
        print(f"   - LGUs: {stats['successful']}")
        return 0
    else:
        print("⚠️  Some LGUs failed to collect")
        return 1


if __name__ == '__main__':
    sys.exit(main())
