"""
Local Prediction Generator (No Supabase Required)
================================================

Generates predictions for tomorrow and saves to docs/predictions/latest.json
Use this for local testing without Supabase credentials.

Usage:
------
python scripts/collect_predictions_local.py
"""

import sys
import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Import from main script
from scripts.collect_and_log import (
    load_model,
    generate_predictions,
    save_predictions_to_web
)
from src.weather.weather_pipeline import WeatherDataPipeline
from src.weather.risk_tiers import get_tier_summary


def main():
    print("🚀 Generating predictions for Metro Manila")
    print(f"   Date: {date.today()}")
    print(f"   Prediction for: {date.today() + timedelta(days=1)}")
    print()
    
    # Load model
    model = load_model()
    if model is None:
        print("⚠️  No model found, will use rule-based predictions")
    
    # Initialize weather pipeline
    try:
        pipeline = WeatherDataPipeline()
        print("✅ Initialized weather pipeline")
    except Exception as e:
        print(f"❌ Failed to initialize weather pipeline: {e}")
        return 1
    
    print()
    
    # Collect weather features
    print("📡 Collecting weather features...")
    try:
        features = pipeline.collect_realtime_weather_features()
        print(f"✅ Collected weather features")
    except Exception as e:
        print(f"❌ Failed to collect weather data: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Generate predictions
    print("\n🎯 Generating predictions...")
    try:
        predictions = generate_predictions(
            weather_features=features,
            model_version='v1.0.0',
            model=model
        )
        print(f"✅ Generated {len(predictions)} predictions")
        
        # Show tier summary
        tier_summary = get_tier_summary(predictions)
        print("\n📊 Prediction Summary:")
        print(f"   🟢 NORMAL: {tier_summary.get('normal', 0)}")
        print(f"   🟠 ALERT: {tier_summary.get('alert', 0)}")
        print(f"   🔴 SUSPENSION: {tier_summary.get('suspension', 0)}")
        
        # Show top 5 at risk
        top_5 = sorted(
            predictions,
            key=lambda x: x['suspension_probability'],
            reverse=True
        )[:5]
        print(f"\n   Top 5 at risk:")
        for pred in top_5:
            prob = pred['suspension_probability']
            tier = pred['risk_tier']['tier']
            print(f"      {pred['lgu']:20s} {prob:6.2%}  {tier}")
        
    except Exception as e:
        print(f"❌ Failed to generate predictions: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Save to file
    print("\n💾 Saving predictions...")
    try:
        save_predictions_to_web(predictions, features)
        print("✅ Saved to docs/predictions/latest.json")
        print("\n🎉 Done!")
    except Exception as e:
        print(f"❌ Failed to save predictions: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
