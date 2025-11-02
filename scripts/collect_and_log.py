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
import time
import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from database.supabase_client import SupabaseLogger
from src.weather.weather_pipeline import WeatherDataPipeline


# Metro Manila LGUs
METRO_MANILA_LGUS = [
    'Manila', 'Quezon City', 'Caloocan', 'Las Piñas', 'Makati',
    'Malabon', 'Mandaluyong', 'Marikina', 'Muntinlupa', 'Navotas',
    'Parañaque', 'Pasay', 'Pasig', 'Pateros', 'San Juan',
    'Taguig', 'Valenzuela'
]


def generate_predictions(weather_features: dict, model_version: str = 'v1.0.0') -> list:
    """
    Generate suspension predictions using weather features.
    
    This is a placeholder - replace with your actual model!
    
    Args:
        weather_features: Dict with 'pagasa' and 'weather' DataFrames
        model_version: Model version identifier
    
    Returns:
        List of prediction dicts
    """
    predictions = []
    
    # Extract features
    pagasa = weather_features['pagasa']
    weather = weather_features['weather']
    
    # Simple rule-based model (REPLACE WITH YOUR ACTUAL MODEL!)
    # This is just for demonstration
    for lgu in METRO_MANILA_LGUS:
        # Get weather for this LGU
        lgu_weather = weather[weather['lgu'] == lgu]
        
        if len(lgu_weather) == 0:
            continue
        
        # Calculate risk score based on conditions
        risk_score = 0.0
        
        # PAGASA factors
        if pagasa.get('has_active_typhoon'):
            risk_score += 0.3
        if pagasa.get('tcws_level', 0) >= 2:
            risk_score += 0.2
        if pagasa.get('has_rainfall_warning'):
            risk_score += 0.15
        
        # Weather factors
        precip = lgu_weather['precipitation_sum_mm'].iloc[0]
        wind = lgu_weather['wind_speed_10m_max_kmh'].iloc[0]
        
        if precip > 50:
            risk_score += 0.2
        elif precip > 20:
            risk_score += 0.1
        
        if wind > 60:
            risk_score += 0.15
        elif wind > 40:
            risk_score += 0.05
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Create prediction
        predictions.append({
            'prediction_date': date.today(),
            'lgu': lgu,
            'suspension_probability': risk_score,
            'predicted_suspended': risk_score >= 0.5
        })
    
    return predictions


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
        features = pipeline.collect_realtime_weather_features()
        
        # Log PAGASA status
        try:
            logger.log_pagasa_status(features['pagasa'], status_date=prediction_date)
            print(f"✅ Logged PAGASA status")
            print(f"   Active typhoon: {features['pagasa'].get('has_active_typhoon')}")
            print(f"   TCWS level: {features['pagasa'].get('tcws_level', 0)}")
            print(f"   Rainfall warning: {features['pagasa'].get('has_rainfall_warning')}")
            results['pagasa_success'] = True
        except Exception as e:
            print(f"⚠️  Failed to log PAGASA status: {e}")
            results['pagasa_error'] = str(e)
        
        # Log weather data
        try:
            weather_df = features['weather']
            logger.log_weather_data(weather_df, data_type='forecast')
            results['openmeteo_records'] = len(weather_df)
            print(f"✅ Logged {len(weather_df)} weather records")
            print(f"   LGUs covered: {weather_df['lgu'].nunique()}")
            print(f"   Avg precipitation: {weather_df['precipitation_sum_mm'].mean():.1f} mm")
            print(f"   Max wind speed: {weather_df['wind_speed_10m_max_kmh'].max():.1f} km/h")
            results['openmeteo_success'] = True
        except Exception as e:
            print(f"⚠️  Failed to log weather data: {e}")
            results['openmeteo_error'] = str(e)
        
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
    
    if features:
        try:
            predictions = generate_predictions(features, model_version=args.model_version)
            
            # Log predictions
            logger.log_predictions(
                predictions,
                model_version=args.model_version,
                threshold=args.threshold
            )
            
            results['predictions_count'] = len(predictions)
            print(f"✅ Logged {len(predictions)} predictions")
            
            # Show summary
            suspended_count = sum(1 for p in predictions if p['predicted_suspended'])
            avg_prob = sum(p['suspension_probability'] for p in predictions) / len(predictions)
            
            print(f"   Predicted suspensions: {suspended_count}/{len(predictions)} LGUs")
            print(f"   Average probability: {avg_prob:.2%}")
            
            # Show top 5 at risk
            top_5 = sorted(predictions, key=lambda x: x['suspension_probability'], reverse=True)[:5]
            print(f"\n   Top 5 at risk:")
            for pred in top_5:
                status = "🔴 SUSPEND" if pred['predicted_suspended'] else "🟢 NO SUSPEND"
                print(f"      {pred['lgu']:20s} {pred['suspension_probability']:6.2%}  {status}")
            
            results['predictions_success'] = True
            print()
            
        except Exception as e:
            print(f"❌ Failed to generate/log predictions: {e}")
            results['predictions_error'] = str(e)
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
