"""
Feature Engineering Pipeline for Historical Data
=================================================

Replicates the feature engineering from scripts/collect_and_log.py
to prepare historical Sept-Oct 2025 data for model predictions.

Input:
- backfill/output/forecast_sept_oct.json (1,037 historical forecast records)
- backfill/output/pagasa_sept_oct.json (61 days of PAGASA status)

Output:
- backfill/output/features_sept_oct.json (1,037 feature vectors, 33 features each)

Features engineered (33 total):
1. Temporal (8): year, month, day, day_of_week, is_rainy_season, 
                 month_from_sy_start, is_holiday, is_school_day
2. LGU (1): lgu_id
3. Flood risk (1): mean_flood_risk_score
4. Historical t-1 (10): hist_precipitation_sum_t1, hist_wind_speed_max_t1, etc.
5. Historical aggregates (3): hist_precip_sum_7d, hist_precip_sum_3d, hist_wind_max_7d
6. Forecast (10): fcst_precipitation_sum, fcst_wind_speed_max, etc.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import numpy as np

# Load data files
OUTPUT_DIR = Path(__file__).parent / "output"
FORECAST_FILE = OUTPUT_DIR / "forecast_sept_oct.json"
PAGASA_FILE = OUTPUT_DIR / "pagasa_sept_oct.json"
FEATURES_OUTPUT = OUTPUT_DIR / "features_sept_oct.json"

# Metro Manila LGUs (alphabetical order for ID mapping)
METRO_MANILA_LGUS = sorted([
    'Manila', 'Quezon City', 'Caloocan', 'Las Piñas', 'Makati',
    'Malabon', 'Mandaluyong', 'Marikina', 'Muntinlupa', 'Navotas',
    'Parañaque', 'Pasay', 'Pasig', 'Pateros', 'San Juan',
    'Taguig', 'Valenzuela'
])

# LGU ID mapping (same as production)
LGU_ID_MAP = {lgu: idx for idx, lgu in enumerate(METRO_MANILA_LGUS)}

# Handle encoding variants (ñ vs Ã±)
LGU_ID_MAP['Las PiÃ±as'] = LGU_ID_MAP['Las Piñas']
LGU_ID_MAP['ParaÃ±aque'] = LGU_ID_MAP['Parañaque']

# School holidays in Sept-Oct 2025 (simplified)
HOLIDAYS = [
    # Add known holidays if needed
]


def load_forecast_data() -> dict:
    """Load historical forecast data."""
    print("📥 Loading forecast data...")
    with open(FORECAST_FILE, 'r') as f:
        data = json.load(f)
    
    # Organize by (lgu, date) for easy lookup
    forecast_by_lgu_date = {}
    for record in data['records']:
        key = (record['lgu'], record['date'])
        forecast_by_lgu_date[key] = record
    
    print(f"   ✅ Loaded {len(data['records'])} forecast records")
    return forecast_by_lgu_date


def load_pagasa_data() -> dict:
    """Load PAGASA status data."""
    print("📥 Loading PAGASA data...")
    with open(PAGASA_FILE, 'r') as f:
        data = json.load(f)
    
    # Organize by date
    pagasa_by_date = {}
    records = data.get('daily_status', data)  # Handle both formats
    for record in records:
        pagasa_by_date[record['date']] = record
    
    print(f"   ✅ Loaded {len(records)} PAGASA records")
    return pagasa_by_date


def calculate_temporal_features(date_str: str) -> dict:
    """Calculate temporal features from date."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    return {
        'year': dt.year,
        'month': dt.month,
        'day': dt.day,
        'day_of_week': dt.weekday(),  # Monday=0, Sunday=6
        'is_rainy_season': 1 if dt.month in [6, 7, 8, 9, 10, 11] else 0,
        'month_from_sy_start': (dt.month - 6) % 12,  # School year starts June
        'is_holiday': 1 if date_str in HOLIDAYS else 0,
        'is_school_day': 1 if dt.weekday() < 5 and date_str not in HOLIDAYS else 0
    }


def calculate_historical_features(
    lgu: str,
    date_str: str,
    forecast_by_lgu_date: dict
) -> dict:
    """
    Calculate historical features (t-1, t-7 day lookback).
    
    Args:
        lgu: LGU name
        date_str: Current date (YYYY-MM-DD)
        forecast_by_lgu_date: Forecast data lookup dict
    
    Returns:
        Dict with historical features
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    # T-1 day (yesterday)
    t1_date = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
    t1_key = (lgu, t1_date)
    t1_data = forecast_by_lgu_date.get(t1_key)
    
    if t1_data:
        hist_t1 = {
            'hist_precipitation_sum_t1': t1_data.get('precipitation_sum', 0.0),
            'hist_wind_speed_max_t1': t1_data.get('wind_speed_10m_max', 0.0),
            'hist_wind_gusts_max_t1': t1_data.get('wind_gusts_10m_max', 0.0),
            'hist_pressure_msl_min_t1': t1_data.get('pressure_msl_min', 1010.0),
            'hist_temperature_max_t1': t1_data.get('temperature_2m_max', 30.0),
            'hist_relative_humidity_mean_t1': t1_data.get('relative_humidity_2m_mean', 70.0),
            'hist_cloud_cover_max_t1': t1_data.get('cloud_cover_max', 50.0),
            'hist_dew_point_mean_t1': t1_data.get('dew_point_2m_mean', 24.0),
            'hist_apparent_temperature_max_t1': t1_data.get('apparent_temperature_max', 30.0),
            'hist_weather_code_t1': t1_data.get('weather_code', 0.0)
        }
    else:
        # Use defaults for first day (no historical data)
        hist_t1 = {
            'hist_precipitation_sum_t1': 0.0,
            'hist_wind_speed_max_t1': 0.0,
            'hist_wind_gusts_max_t1': 0.0,
            'hist_pressure_msl_min_t1': 1010.0,
            'hist_temperature_max_t1': 30.0,
            'hist_relative_humidity_mean_t1': 70.0,
            'hist_cloud_cover_max_t1': 50.0,
            'hist_dew_point_mean_t1': 24.0,
            'hist_apparent_temperature_max_t1': 30.0,
            'hist_weather_code_t1': 0.0
        }
    
    # T-3 and T-7 day aggregates (rolling windows)
    precip_3d = []
    precip_7d = []
    wind_7d = []
    
    for i in range(1, 8):  # Look back 7 days
        past_date = (dt - timedelta(days=i)).strftime("%Y-%m-%d")
        past_key = (lgu, past_date)
        past_data = forecast_by_lgu_date.get(past_key)
        
        if past_data:
            precip = past_data.get('precipitation_sum', 0.0) or 0.0
            wind = past_data.get('wind_speed_10m_max', 0.0) or 0.0
            
            if i <= 3:
                precip_3d.append(precip)
            precip_7d.append(precip)
            wind_7d.append(wind)
    
    hist_aggregates = {
        'hist_precip_sum_3d': sum(precip_3d) if precip_3d else 0.0,
        'hist_precip_sum_7d': sum(precip_7d) if precip_7d else 0.0,
        'hist_wind_max_7d': max(wind_7d) if wind_7d else 0.0
    }
    
    return {**hist_t1, **hist_aggregates}


def calculate_forecast_features(forecast_record: dict) -> dict:
    """
    Extract forecast features from forecast record.
    
    Args:
        forecast_record: Forecast data for current date
    
    Returns:
        Dict with forecast features
    """
    return {
        'fcst_precipitation_sum': forecast_record.get('precipitation_sum', 0.0) or 0.0,
        'fcst_precipitation_hours': forecast_record.get('precipitation_hours', 0.0) or 0.0,
        'fcst_wind_speed_max': forecast_record.get('wind_speed_10m_max', 0.0) or 0.0,
        'fcst_wind_gusts_max': forecast_record.get('wind_gusts_10m_max', 0.0) or 0.0,
        'fcst_pressure_msl_min': forecast_record.get('pressure_msl_min', 1010.0) or 1010.0,
        'fcst_temperature_max': forecast_record.get('temperature_2m_max', 30.0) or 30.0,
        'fcst_relative_humidity_mean': forecast_record.get('relative_humidity_2m_mean', 70.0) or 70.0,
        'fcst_cloud_cover_max': forecast_record.get('cloud_cover_max', 50.0) or 50.0,
        'fcst_dew_point_mean': forecast_record.get('dew_point_2m_mean', 24.0) or 24.0,
        'fcst_cape_max': forecast_record.get('cape_max', 0.0) or 0.0
    }


def engineer_features():
    """Main feature engineering pipeline."""
    print("=" * 70)
    print("⚙️  Feature Engineering Pipeline".center(70))
    print("=" * 70)
    print()
    
    # Load data
    forecast_by_lgu_date = load_forecast_data()
    pagasa_by_date = load_pagasa_data()
    
    print()
    print("🔧 Engineering features...")
    print()
    
    # Get all unique dates from forecast data
    all_keys = sorted(forecast_by_lgu_date.keys())
    
    feature_vectors = []
    dates_processed = set()
    
    for key in all_keys:
        lgu, date_str = key
        
        # Progress indicator
        if date_str not in dates_processed:
            print(f"   📅 Processing {date_str}...")
            dates_processed.add(date_str)
        
        forecast_record = forecast_by_lgu_date[key]
        pagasa_record = pagasa_by_date.get(date_str, {})
        
        # Build complete feature vector (33 features)
        features = {}
        
        # 1. Temporal features (8)
        features.update(calculate_temporal_features(date_str))
        
        # 2. LGU ID (1)
        features['lgu_id'] = LGU_ID_MAP[lgu]
        
        # 3. Flood risk (1) - simplified default
        features['mean_flood_risk_score'] = 0.5
        
        # 4. Historical features (10 + 3 = 13)
        features.update(calculate_historical_features(
            lgu, date_str, forecast_by_lgu_date))
        
        # 5. Forecast features (10)
        features.update(calculate_forecast_features(forecast_record))
        
        # Get PAGASA info - CRITICAL: Only use TCWS if Metro Manila is affected!
        metro_manila_affected = pagasa_record.get('metro_manila_affected', False)
        raw_tcws = pagasa_record.get('tcws_level', 0)
        
        # Zero out TCWS if Metro Manila not affected by the typhoon
        effective_tcws = raw_tcws if metro_manila_affected else 0
        
        # Add metadata
        feature_vector = {
            'date': date_str,
            'lgu': lgu,
            'features': features,
            # Also store PAGASA info for reference (not model features)
            'pagasa_context': {
                'has_active_typhoon': pagasa_record.get('has_active_typhoon', False),
                'typhoon_name': pagasa_record.get('typhoon_name', 'None'),
                'tcws_level': effective_tcws,  # Effective TCWS for Metro Manila
                'raw_tcws_level': raw_tcws,  # Original TCWS (may be for other regions)
                'rainfall_warning': pagasa_record.get('rainfall_warning', 'NONE'),
                'metro_manila_affected': metro_manila_affected
            }
        }
        
        feature_vectors.append(feature_vector)
    
    print()
    print(f"✅ Engineered {len(feature_vectors)} feature vectors")
    print()
    
    # Validate feature counts
    if feature_vectors:
        sample_features = feature_vectors[0]['features']
        feature_count = len(sample_features)
        print(f"🔍 Validation:")
        print(f"   Feature count: {feature_count} (expected: 33)")
        
        if feature_count != 33:
            print(f"   ⚠️  WARNING: Feature count mismatch!")
            print(f"   Features: {list(sample_features.keys())}")
        else:
            print(f"   ✅ Feature count correct")
    
    # Save to JSON
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "date_range": {
                "start": "2025-09-01",
                "end": "2025-10-31"
            },
            "feature_count": 33,
            "record_count": len(feature_vectors),
            "lgus": METRO_MANILA_LGUS,
            "feature_names": [
                'year', 'month', 'day', 'day_of_week', 'is_rainy_season',
                'month_from_sy_start', 'is_holiday', 'is_school_day', 'lgu_id',
                'mean_flood_risk_score', 'hist_precipitation_sum_t1',
                'hist_wind_speed_max_t1', 'hist_wind_gusts_max_t1',
                'hist_pressure_msl_min_t1', 'hist_temperature_max_t1',
                'hist_relative_humidity_mean_t1', 'hist_cloud_cover_max_t1',
                'hist_dew_point_mean_t1', 'hist_apparent_temperature_max_t1',
                'hist_weather_code_t1', 'hist_precip_sum_7d', 'hist_precip_sum_3d',
                'hist_wind_max_7d', 'fcst_precipitation_sum', 'fcst_precipitation_hours',
                'fcst_wind_speed_max', 'fcst_wind_gusts_max', 'fcst_pressure_msl_min',
                'fcst_temperature_max', 'fcst_relative_humidity_mean',
                'fcst_cloud_cover_max', 'fcst_dew_point_mean', 'fcst_cape_max'
            ],
            "note": "Features engineered from historical forecast data for model predictions"
        },
        "feature_vectors": feature_vectors
    }
    
    with open(FEATURES_OUTPUT, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    file_size_kb = FEATURES_OUTPUT.stat().st_size / 1024
    
    print()
    print("=" * 70)
    print("💾 Output")
    print("=" * 70)
    print(f"File: {FEATURES_OUTPUT.name}")
    print(f"Size: {file_size_kb:.1f} KB")
    print(f"Records: {len(feature_vectors)}")
    print()
    
    # Show sample
    if feature_vectors:
        print("=" * 70)
        print("📊 Sample Feature Vector")
        print("=" * 70)
        sample = feature_vectors[0]
        print(f"Date: {sample['date']}")
        print(f"LGU: {sample['lgu']}")
        print(f"\nTemporal Features:")
        temp_features = ['year', 'month', 'day', 'day_of_week', 'is_rainy_season']
        for feat in temp_features:
            print(f"  {feat}: {sample['features'][feat]}")
        print(f"\nForecast Features:")
        fcst_features = ['fcst_precipitation_sum', 'fcst_wind_speed_max', 'fcst_temperature_max']
        for feat in fcst_features:
            print(f"  {feat}: {sample['features'][feat]:.2f}")
        print(f"\nHistorical Features:")
        hist_features = ['hist_precipitation_sum_t1', 'hist_precip_sum_7d']
        for feat in hist_features:
            print(f"  {feat}: {sample['features'][feat]:.2f}")
        print(f"\nPAGASA Context:")
        print(f"  Typhoon: {sample['pagasa_context']['typhoon_name']}")
        print(f"  TCWS: {sample['pagasa_context']['tcws_level']}")
    
    print()
    print("=" * 70)
    print("✨ Feature Engineering Complete!")
    print("=" * 70)
    print()
    print("Next step:")
    print("  python backfill/generate_predictions.py")
    print()


if __name__ == "__main__":
    engineer_features()
