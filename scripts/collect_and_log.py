"""
Complete Data Collection and Logging Script
============================================

Integrates:
1. PAGASA typhoon/rainfall checker
2. Open-Meteo weather collector
3. Suspension prediction model
4. Supabase database logging

Run this script from GitHub Actions hourly to:
- Collect real-time weather data
- Generate suspension predictions
- Log everything to database

Usage:
------
# Set environment variables first:
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_KEY="eyJhbG..."

# Run script:
python scripts/collect_and_log.py

# Or with custom date:
python scripts/collect_and_log.py --date 2025-11-02
"""

import os
import sys
import json
import time
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import pickle
import joblib  # For loading scikit-learn models

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from database.supabase_client import SupabaseLogger
from src.weather.weather_pipeline import WeatherDataPipeline
from src.weather.risk_tiers import interpret_prediction, get_tier_summary


# Metro Manila LGUs
METRO_MANILA_LGUS = [
    'Manila', 'Quezon City', 'Caloocan', 'Las Piñas', 'Makati',
    'Malabon', 'Mandaluyong', 'Marikina', 'Muntinlupa', 'Navotas',
    'Parañaque', 'Pasay', 'Pasig', 'Pateros', 'San Juan',
    'Taguig', 'Valenzuela'
]


def load_model(model_path: Path = None):
    """Load the trained ML model."""
    if model_path is None:
        # Look in data/processed directory where models are saved
        model_path = PROJECT_ROOT / 'model-training' / 'data' / 'processed'
    
    # Try specific known model files first
    known_models = ['best_core_model.pkl', 'core_model.pkl', 'final_model.pkl']
    for model_name in known_models:
        model_file = model_path / model_name
        if model_file.exists():
            print(f"📦 Loading model: {model_name}")
            try:
                # Use joblib for scikit-learn models
                model = joblib.load(model_file)
                return model
            except Exception as e:
                print(f"⚠️  Failed to load {model_name}: {e}")
                continue
    
    # Fallback: try any pkl/joblib files
    model_files = list(model_path.glob('*.pkl')) + \
                  list(model_path.glob('*.joblib'))
    
    if not model_files:
        print("⚠️  No trained model found, using rule-based fallback")
        return None
    
    # Use most recent model
    latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
    print(f"📦 Loading model: {latest_model.name}")
    
    try:
        # Use joblib for scikit-learn models
        model = joblib.load(latest_model)
        return model
    except Exception as e:
        print(f"⚠️  Failed to load model: {e}, using rule-based fallback")
        return None


def generate_predictions(
    weather_features: dict,
    model_version: str = 'v1.0.0',
    model=None
) -> list:
    """
    Generate suspension predictions using weather features.
    
    Args:
        weather_features: Flat dict with all weather/PAGASA features
        model_version: Model version identifier
        model: Trained ML model (if None, uses rule-based)
    
    Returns:
        List of prediction dicts with risk tier interpretation
    """
    predictions = []
    
    # LGU ID mapping (alphabetical order)
    lgu_id_map = {lgu: idx for idx, lgu in
                  enumerate(sorted(METRO_MANILA_LGUS))}
    
    for lgu in METRO_MANILA_LGUS:
        if model is not None:
            # Use ML model with feature engineering
            try:
                risk_score = predict_with_model(
                    model, weather_features, lgu, lgu_id_map[lgu])
            except Exception as e:
                print(f"⚠️  Model prediction failed for {lgu}: {e}")
                risk_score = calculate_rule_based_score_from_features(
                    weather_features)
        else:
            # Rule-based model
            risk_score = calculate_rule_based_score_from_features(
                weather_features)
        
        # Get risk tier interpretation
        interpretation = interpret_prediction(
            probability=float(risk_score),
            lgu_name=lgu,
            date=str(date.today()),
            precipitation_mm=weather_features.get(
                'forecast_precipitation_sum'),
            weather_code=weather_features.get('forecast_weather_code'),
            pagasa_warning=weather_features.get('rainfall_warning_level'),
            tcws_level=weather_features.get('tcws_level', 0),
            typhoon_name=weather_features.get('typhoon_name')
        )
        
        # Create prediction with risk tier
        predictions.append({
            'prediction_date': str(date.today()),  # Convert to string
            'lgu': lgu,
            'suspension_probability': float(risk_score),
            'predicted_suspended': bool(risk_score >= 0.5),
            'risk_tier': interpretation['risk_tier'],
            'weather_context': interpretation['weather_context']
        })
    
    return predictions


def predict_with_model(model, weather_features: dict, lgu: str, lgu_id: int) -> float:
    """
    Generate prediction using the trained ML model.
    
    Args:
        model: Trained scikit-learn model
        weather_features: Dict with current weather/PAGASA data
        lgu: LGU name
        lgu_id: Numeric LGU identifier (0-16)
    
    Returns:
        Suspension probability (0.0-1.0)
    """
    today = date.today()
    
    # Build feature vector matching training data format
    # Model expects 33 features in specific order (see core_model_metadata.json)
    features = {
        # Temporal features
        'year': today.year,
        'month': today.month,
        'day': today.day,
        'day_of_week': today.weekday(),
        'is_rainy_season': 1 if today.month in [6, 7, 8, 9, 10, 11] else 0,
        'month_from_sy_start': ((today.month - 6) % 12),  # School year starts June
        'is_holiday': 0,  # Simplified: assume not holiday
        'is_school_day': 1 if today.weekday() < 5 else 0,
        
        # LGU identifier
        'lgu_id': lgu_id,
        
        # Flood risk (simplified)
        'mean_flood_risk_score': 0.5,  # Neutral default
        
        # Historical weather (t-1 day) - use forecast as proxy since we don't have historical
        'hist_precipitation_sum_t1': weather_features.get('forecast_precipitation_sum', 0),
        'hist_wind_speed_max_t1': weather_features.get('forecast_wind_speed_max', 0),
        'hist_wind_gusts_max_t1': weather_features.get('forecast_wind_gusts_max', 0),
        'hist_pressure_msl_min_t1': 1010.0,  # Default atmospheric pressure
        'hist_temperature_max_t1': weather_features.get('forecast_temperature_max', 30),
        'hist_relative_humidity_mean_t1': weather_features.get('forecast_humidity_mean', 70),
        'hist_cloud_cover_max_t1': weather_features.get('forecast_cloud_cover', 50),
        'hist_dew_point_mean_t1': 24.0,  # Typical for Manila
        'hist_apparent_temperature_max_t1': weather_features.get('forecast_temperature_max', 30),
        'hist_weather_code_t1': weather_features.get('forecast_weather_code', 0),
        
        # Historical aggregates (3d, 7d) - use current as proxy
        'hist_precip_sum_7d': weather_features.get('forecast_precipitation_sum', 0) * 3,
        'hist_precip_sum_3d': weather_features.get('forecast_precipitation_sum', 0) * 2,
        'hist_wind_max_7d': weather_features.get('forecast_wind_speed_max', 0) * 1.2,
        
        # Forecast features (these we have!)
        'fcst_precipitation_sum': weather_features.get('forecast_precipitation_sum', 0),
        'fcst_precipitation_hours': weather_features.get('forecast_precipitation_probability', 0) / 10,
        'fcst_wind_speed_max': weather_features.get('forecast_wind_speed_max', 0),
        'fcst_wind_gusts_max': weather_features.get('forecast_wind_gusts_max', 0),
        'fcst_pressure_msl_min': 1010.0,  # Default
        'fcst_temperature_max': weather_features.get('forecast_temperature_max', 30),
        'fcst_relative_humidity_mean': weather_features.get('forecast_humidity_mean', 70),
        'fcst_cloud_cover_max': weather_features.get('forecast_cloud_cover', 50),
        'fcst_dew_point_mean': 24.0,  # Typical
        'fcst_cape_max': 0.0,  # CAPE not available from Open-Meteo free tier
    }
    
    # Convert to DataFrame with correct feature order
    feature_order = [
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
    ]
    
    X = pd.DataFrame([features])[feature_order]
    
    # Get prediction probability
    # model.predict_proba returns [[prob_class_0, prob_class_1]]
    proba = model.predict_proba(X)[0, 1]  # Probability of class 1 (suspension)
    
    return float(proba)


def calculate_rule_based_score_from_features(features: dict) -> float:
    """Calculate suspension risk score from flat features dict."""
    risk_score = 0.0
    
    # PAGASA factors
    if features.get('has_active_typhoon'):
        risk_score += 0.3
    if features.get('tcws_level', 0) >= 2:
        risk_score += 0.2
    if features.get('has_rainfall_warning'):
        risk_score += 0.15
    
    # Weather factors
    precip = features.get('forecast_precipitation_sum', 0)
    wind = features.get('forecast_wind_speed_max', 0)
    
    if precip > 50:
        risk_score += 0.2
    elif precip > 20:
        risk_score += 0.1
    
    if wind > 60:
        risk_score += 0.15
    elif wind > 40:
        risk_score += 0.05
    
    # Cap at 1.0
    return min(risk_score, 1.0)


def save_predictions_to_web(predictions: list, weather_features: dict):
    """Save predictions to JSON file for GitHub Pages."""
    web_dir = PROJECT_ROOT / 'web' / 'predictions'
    web_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare output data
    output = {
        'generated_at': datetime.now().isoformat(),
        'prediction_date': str(predictions[0]['prediction_date']),
        'model_version': 'v1.0.0',
        'pagasa_status': {
            'has_active_typhoon': weather_features.get(
                'has_active_typhoon', False),
            'typhoon_name': weather_features.get('typhoon_name'),
            'tcws_level': weather_features.get('tcws_level', 0),
            'has_rainfall_warning': weather_features.get(
                'has_rainfall_warning', False),
            'rainfall_warning_level': weather_features.get(
                'rainfall_warning_level')
        },
        'weather': {
            'precipitation_sum_mm': weather_features.get(
                'forecast_precipitation_sum', 0),
            'wind_speed_max_kmh': weather_features.get(
                'forecast_wind_speed_max', 0),
            'temperature_max_c': weather_features.get(
                'forecast_temperature_max', 0),
            'humidity_mean_pct': weather_features.get(
                'forecast_humidity_mean', 0)
        },
        'predictions': predictions,
        'summary': {
            'total_lgus': len(predictions),
            'predicted_suspensions': sum(
                1 for p in predictions if p['predicted_suspended']),
            'avg_probability': sum(
                p['suspension_probability'] for p in predictions
            ) / len(predictions) if predictions else 0
        }
    }
    
    # Save to latest.json
    latest_file = web_dir / 'latest.json'
    with open(latest_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved predictions to {latest_file}")
    
    # Also save timestamped version
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_file = web_dir / f'predictions_{timestamp}.json'
    with open(timestamped_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Saved timestamped version to {timestamped_file}")
    
    return output


def main():
    """Main data collection and logging pipeline."""
    parser = argparse.ArgumentParser(description='Collect weather data and generate predictions')
    parser.add_argument('--date', type=str, help='Prediction date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--model-version', type=str, default='v1.0.0', help='Model version identifier')
    parser.add_argument('--threshold', type=float, default=0.5, help='Classification threshold')
    args = parser.parse_args()
    
    # Parse date
    if args.date:
        prediction_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        prediction_date = date.today()
    
    print(f"🚀 Starting data collection for {prediction_date}")
    print(f"   Model: {args.model_version}, Threshold: {args.threshold}")
    print(f"   GitHub Run ID: {os.getenv('GITHUB_RUN_ID', 'local')}")
    print()
    
    start_time = time.time()
    
    # Initialize clients
    try:
        logger = SupabaseLogger()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("   Make sure SUPABASE_URL and SUPABASE_KEY are set")
        return 1
    
    try:
        pipeline = WeatherDataPipeline()
        print("✅ Initialized weather pipeline")
    except Exception as e:
        print(f"❌ Failed to initialize weather pipeline: {e}")
        return 1
    
    print()
    
    # Track results
    results = {
        'pagasa_success': False,
        'pagasa_error': None,
        'openmeteo_success': False,
        'openmeteo_records': 0,
        'openmeteo_error': None,
        'predictions_success': False,
        'predictions_count': 0,
        'predictions_error': None
    }
    
    # Step 1: Collect weather data
    print("=" * 60)
    print("STEP 1: Collecting Real-Time Weather Data")
    print("=" * 60)
    
    try:
        # Collect features (returns flat dict with all features)
        features = pipeline.collect_realtime_weather_features()
        
        # Extract PAGASA status from flat features dict
        pagasa_status = {
            'has_active_typhoon': features.get('has_active_typhoon', False),
            'typhoon_name': features.get('typhoon_name'),
            'typhoon_status': features.get('typhoon_status'),
            'metro_manila_affected': features.get(
                'metro_manila_affected', False),
            'tcws_level': features.get('tcws_level', 0),
            'has_rainfall_warning': features.get(
                'has_rainfall_warning', False),
            'rainfall_warning_level': features.get('rainfall_warning_level')
            if features.get('has_rainfall_warning') else None
        }
        
        # Log PAGASA status
        try:
            logger.log_pagasa_status(pagasa_status,
                                     status_date=prediction_date)
            print(f"✅ Logged PAGASA status to database")
            print(f"   Active typhoon: "
                  f"{pagasa_status.get('has_active_typhoon')}")
            print(f"   TCWS level: {pagasa_status.get('tcws_level', 0)}")
            print(f"   Rainfall warning: "
                  f"{pagasa_status.get('has_rainfall_warning')}")
            results['pagasa_success'] = True
        except Exception as e:
            print(f"⚠️  Failed to log PAGASA status: {e}")
            results['pagasa_error'] = str(e)
        
        # Note: We don't log individual LGU weather to database here
        # (that's for historical collection). Just mark as success.
        results['openmeteo_success'] = True
        results['openmeteo_records'] = 17  # Metro Manila LGUs
        print(f"✅ Weather data collected successfully")
        
        print()
        
    except Exception as e:
        print(f"❌ Failed to collect weather data: {e}")
        results['pagasa_error'] = str(e)
        results['openmeteo_error'] = str(e)
        features = None
    
    # Step 2: Generate predictions
    print("=" * 60)
    print("STEP 2: Generating Suspension Predictions")
    print("=" * 60)
    
    predictions = None
    if features:
        try:
            # Load model
            model = load_model()
            
            # Generate predictions
            predictions = generate_predictions(
                features,
                model_version=args.model_version,
                model=model
            )
            
            # Log to database
            logger.log_predictions(
                predictions,
                model_version=args.model_version,
                threshold=args.threshold
            )
            
            # Save to web/predictions/latest.json
            save_predictions_to_web(predictions, features)
            
            results['predictions_count'] = len(predictions)
            print(f"✅ Logged {len(predictions)} predictions to database")
            
            # Show summary
            suspended_count = sum(
                1 for p in predictions if p['predicted_suspended'])
            avg_prob = sum(
                p['suspension_probability'] for p in predictions
            ) / len(predictions)
            
            print(f"   Predicted suspensions: "
                  f"{suspended_count}/{len(predictions)} LGUs")
            print(f"   Average probability: {avg_prob:.2%}")
            
            # Show top 5 at risk
            top_5 = sorted(
                predictions,
                key=lambda x: x['suspension_probability'],
                reverse=True
            )[:5]
            print(f"\n   Top 5 at risk:")
            for pred in top_5:
                status = ("🔴 SUSPEND" if pred['predicted_suspended']
                          else "🟢 NO SUSPEND")
                prob = pred['suspension_probability']
                print(f"      {pred['lgu']:20s} {prob:6.2%}  {status}")
            
            results['predictions_success'] = True
            print()
            
        except Exception as e:
            print(f"❌ Failed to generate/log predictions: {e}")
            results['predictions_error'] = str(e)
            import traceback
            traceback.print_exc()
    else:
        print("⚠️  Skipping predictions (no weather data)")
    
    # Step 3: Log collection run
    print("=" * 60)
    print("STEP 3: Logging Collection Run")
    print("=" * 60)
    
    duration = int(time.time() - start_time)
    
    try:
        logger.log_collection_run(
            run_date=prediction_date,
            pagasa_success=results['pagasa_success'],
            pagasa_error=results['pagasa_error'],
            openmeteo_success=results['openmeteo_success'],
            openmeteo_records=results['openmeteo_records'],
            openmeteo_error=results['openmeteo_error'],
            predictions_success=results['predictions_success'],
            predictions_count=results['predictions_count'],
            predictions_error=results['predictions_error'],
            duration_seconds=duration
        )
        print(f"✅ Logged collection run (duration: {duration}s)")
    except Exception as e:
        print(f"⚠️  Failed to log collection run: {e}")
    
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total duration: {duration} seconds")
    print(f"📊 PAGASA collection: {'✅ SUCCESS' if results['pagasa_success'] else '❌ FAILED'}")
    print(f"🌤️  Weather collection: {'✅ SUCCESS' if results['openmeteo_success'] else '❌ FAILED'}")
    print(f"🎯 Predictions: {'✅ SUCCESS' if results['predictions_success'] else '❌ FAILED'}")
    print()
    
    if all([results['pagasa_success'], results['openmeteo_success'], results['predictions_success']]):
        print("✅ All operations completed successfully!")
        return 0
    else:
        print("⚠️  Some operations failed - check logs above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
