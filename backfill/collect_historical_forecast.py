"""
Collect historical forecast data for September-October 2025.

This script uses the Open-Meteo Historical Forecast API to fetch
what weather was FORECASTED (not actual) for each day in Sept-Oct 2025.
This is crucial because ML model training used forecast data, so validation
should also use historical forecasts to match the model's input distribution.

API: https://historical-forecast-api.open-meteo.com/v1/forecast
Difference from archive API:
- Archive API: Actual weather that happened
- Historical Forecast API: What was forecasted/predicted at the time
"""

import json
import os
from datetime import datetime
from pathlib import Path
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from tqdm import tqdm
import time

# Setup Open-Meteo client with cache and retry
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Load configuration
config_path = Path(__file__).parent / "config.json"
with open(config_path, 'r') as f:
    config = json.load(f)

# Output directory
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# Metro Manila LGUs with coordinates
LGUS = config["lgu_coordinates"]

# Date range
START_DATE = config["date_range"]["start"]
END_DATE = config["date_range"]["end"]

# API endpoint (Historical Forecast, not Archive!)
API_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"

# Weather variables to collect
# These are the variables available in historical forecast API
# Match them to what the ML model expects
DAILY_VARIABLES = [
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_max",
    "precipitation_sum",
    "precipitation_hours",
    "precipitation_probability_max",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "relative_humidity_2m_mean",
    "dew_point_2m_mean",
    "cloud_cover_max",
    "pressure_msl_min",
    "cape_max",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
    "updraft_max",
    "vapour_pressure_deficit_max"
]


def fetch_lgu_forecast(lgu_name: str, lat: float, lon: float) -> dict:
    """
    Fetch historical forecast data for a single LGU.
    
    Args:
        lgu_name: Name of the LGU
        lat: Latitude
        lon: Longitude
    
    Returns:
        Dict with forecast data or None if failed
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": DAILY_VARIABLES,
        "timezone": "Asia/Singapore"
    }
    
    try:
        responses = openmeteo.weather_api(API_URL, params=params)
        response = responses[0]
        
        # Process daily data
        daily = response.Daily()
        
        # Extract all variables
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )
        }
        
        # Map variables to dataframe columns
        for i, var_name in enumerate(DAILY_VARIABLES):
            daily_data[var_name] = daily.Variables(i).ValuesAsNumpy()
        
        # Convert to DataFrame
        df = pd.DataFrame(data=daily_data)
        
        # Convert to list of records
        records = []
        for _, row in df.iterrows():
            record = {
                "lgu": lgu_name,
                "date": row["date"].strftime("%Y-%m-%d"),
                "data_type": "historical_forecast"  # Important distinction!
            }
            
            # Add all weather variables
            for var in DAILY_VARIABLES:
                value = row[var]
                # Handle NaN values
                if pd.isna(value):
                    record[var] = None
                else:
                    record[var] = float(value)
            
            records.append(record)
        
        return {
            "lgu": lgu_name,
            "success": True,
            "records": records,
            "count": len(records)
        }
        
    except Exception as e:
        return {
            "lgu": lgu_name,
            "success": False,
            "error": str(e),
            "records": [],
            "count": 0
        }


def main():
    """Main collection function."""
    print("=" * 70)
    print("📊 Historical Forecast Data Collection".center(70))
    print("=" * 70)
    print()
    print(f"📅 Date range: {START_DATE} to {END_DATE}")
    print(f"📍 LGUs: {len(LGUS)}")
    print(f"🔢 Total API calls: {len(LGUS)} (1 per LGU, covers all dates)")
    print(f"🌐 API: {API_URL}")
    print(f"📋 Variables: {len(DAILY_VARIABLES)}")
    print()
    print("🔑 KEY DIFFERENCE:")
    print("   ✅ Historical Forecast API: What was FORECASTED at the time")
    print("   ❌ Archive API: What ACTUALLY happened")
    print()
    print("This matches the ML model training data (forecasts, not actuals)!")
    print()
    
    # Calculate expected dates
    start = datetime.strptime(START_DATE, "%Y-%m-%d")
    end = datetime.strptime(END_DATE, "%Y-%m-%d")
    num_days = (end - start).days + 1
    expected_records = num_days * len(LGUS)
    
    print(f"⏱️  Estimated time: ~{len(LGUS) * 2 / 60:.1f} minutes")
    print(f"📊 Expected records: {expected_records} ({num_days} days × {len(LGUS)} LGUs)")
    print()
    
    # Collect data for all LGUs
    all_records = []
    successful = 0
    failed = 0
    api_calls = 0
    
    progress_bar = tqdm(
        LGUS.items(),
        desc="Fetching LGUs",
        unit="LGU",
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {postfix}]'
    )
    
    for lgu_name, coords in progress_bar:
        result = fetch_lgu_forecast(
            lgu_name,
            coords["lat"],
            coords["lon"]
        )
        
        api_calls += 1
        
        if result["success"]:
            all_records.extend(result["records"])
            successful += 1
            progress_bar.set_postfix({
                "Success": successful,
                "Failed": failed,
                "Records": len(all_records)
            })
        else:
            failed += 1
            progress_bar.set_postfix({
                "Success": successful,
                "Failed": failed,
                "Error": result["error"][:30]
            })
            print(f"\n⚠️  Failed to fetch {lgu_name}: {result['error']}")
        
        # Rate limiting (be nice to the API)
        time.sleep(1)
    
    print()
    print("=" * 70)
    print("📋 Collection Summary")
    print("=" * 70)
    print(f"✅ Successful: {successful}")
    print(f"⏭️  Skipped: 0")
    print(f"❌ Failed: {failed}")
    print(f"📡 API calls made: {api_calls}")
    print(f"📊 Records collected: {len(all_records)}")
    
    # Calculate date coverage
    unique_dates = set(record["date"] for record in all_records)
    print(f"📅 Unique dates: {len(unique_dates)}")
    print()
    
    if len(all_records) == 0:
        print("❌ No data collected. Exiting.")
        return
    
    # Save to JSON
    output_file = output_dir / "forecast_sept_oct.json"
    
    output_data = {
        "metadata": {
            "collection_timestamp": datetime.now().isoformat(),
            "date_range": {
                "start": START_DATE,
                "end": END_DATE
            },
            "api_endpoint": API_URL,
            "data_type": "historical_forecast",
            "lgus_count": len(LGUS),
            "dates_count": len(unique_dates),
            "records_count": len(all_records),
            "variables": DAILY_VARIABLES,
            "note": "Historical forecasts (what was predicted), not actual weather"
        },
        "records": all_records
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    file_size_kb = os.path.getsize(output_file) / 1024
    
    print(f"💾 Saved results to: {output_file.name}")
    print(f"📦 File size: {file_size_kb:.1f} KB")
    print()
    
    # Validation checks
    print("=" * 70)
    print("🔍 Data Validation")
    print("=" * 70)
    
    if len(all_records) == expected_records:
        print(f"✅ Record count matches expected: {len(all_records)}")
    else:
        print(f"⚠️  Record count mismatch:")
        print(f"   Expected: {expected_records}")
        print(f"   Actual: {len(all_records)}")
        print(f"   Missing: {expected_records - len(all_records)}")
    
    # Check for missing LGUs
    collected_lgus = set(record["lgu"] for record in all_records)
    missing_lgus = set(LGUS.keys()) - collected_lgus
    if missing_lgus:
        print(f"⚠️  Missing LGUs: {', '.join(missing_lgus)}")
    else:
        print(f"✅ All {len(LGUS)} LGUs collected")
    
    # Check date coverage
    if len(unique_dates) == num_days:
        print(f"✅ Date coverage complete: {num_days} days")
    else:
        print(f"⚠️  Date coverage incomplete:")
        print(f"   Expected: {num_days} days")
        print(f"   Actual: {len(unique_dates)} days")
    
    print()
    print("=" * 70)
    print("✨ Collection Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Review forecast_sept_oct.json")
    print("2. Run backfill/engineer_features.py to create feature vectors")
    print("3. Run backfill/generate_predictions.py to generate predictions")
    print()


if __name__ == "__main__":
    main()
